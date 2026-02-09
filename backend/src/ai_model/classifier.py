"""
classifier.py

Luokittelee käyttäjän kysymykset kahteen kategoriaan:
- SAFE: yleinen terveystieto, johon AI voi vastata suoraan (ml. epämääräiset oiremaininnat)
- NEEDS_REVIEW: henkilökohtainen terveysarvio, joka vaatii ammattilaisen tarkistuksen

EU AI Act -yhteensopivuus: epäselvissä tapauksissa aina NEEDS_REVIEW (fail-safe).
"""

import os
import json
import logging
from enum import Enum
from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
google_api_key = os.getenv('GEMINI_API')

logger = logging.getLogger(__name__)


class Classification(str, Enum):
    SAFE = "SAFE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    EMERGENCY = "EMERGENCY"


@dataclass
class ClassificationResult:
    classification: Classification
    reasoning: str
    confidence: str  # "HIGH", "MEDIUM", "LOW"


# Deterministic LLM for classification (temperature=0)
classifier_llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-001',
    temperature=0.0,
    max_tokens=300,
    google_api_key=google_api_key
)

CLASSIFICATION_PROMPT = """You are a medical question safety classifier for a healthcare chatbot focused on heart health and coronary artery disease. Your job is to determine whether a user's question can be safely answered with general health information, or whether it requires professional medical review.

CLASSIFICATION RULES:

SAFE - The question asks for general, educational health information that can be answered from approved medical guidelines (Käypä hoito, ESC guidelines). Examples:
- Factual questions about what a condition is ("What is coronary artery disease?", "Mikä on sepelvaltimotauti?")
- General risk factors for heart disease ("Mitkä ovat sydänsairauksien riskitekijät?")
- General lifestyle advice (diet, exercise) ("Millainen ruokavalio on hyväksi sydämelle?")
- Explaining medical terms or concepts
- How diagnostic procedures work in general
- General information about how medications work (NOT whether someone should take them)
- Understanding their own condition in general terms ("Help me understand my illness", "Voitko auttaa minua ymmärtämään sairauttani?", "What does my diagnosis mean in general?")
- General questions about living with a condition ("How do people manage coronary artery disease?", "Miten sepelvaltimotaudin kanssa eletään?")
- Asking what a diagnosis or condition generally involves
- Vague, non-urgent symptom mentions that can be addressed with general health information and follow-up questions ("My legs swell in the evenings", "Jalkojani turvottaa iltaisin", "I've been tired lately", "Olen ollut väsynyt", "I sometimes feel dizzy", "Välillä huimaa")

NEEDS_REVIEW - The question involves ANY of the following:
- Personal symptoms or complaints ("I have chest pain", "Minulla on rintakipua")
- Specific health values or measurements ("My blood pressure is 180/100", "Verenpaineeni on 180/100")
- Medication decisions ("Should I stop/start/change my medication?", "Pitäisikö lopettaa lääkitykseni?")
- Personal risk assessment ("Am I at risk?", "Olenko riskissä?")
- Treatment recommendations ("What treatment should I get?", "Mitä hoitoa tarvitsen?")
- Diagnosis requests ("Do I have heart disease?", "Onko minulla sydänsairaus?")
- Emergency or urgent situations ("I'm having a heart attack", "Saan sydänkohtauksen")
- Questions requesting interpretation or assessment of the user's own specific health data, test results, or symptoms
- Any request for personalized medical advice
- Questions about specific medication dosing or schedules
- Interpreting personal test results or measurements
- Questions asking whether something is dangerous or harmful ("Is this dangerous?", "Onko tämä vaarallista?", "Should I be worried?", "Pitäisikö minun olla huolissaan?")

IMPORTANT DISTINCTION: A question is SAFE if the user is seeking general understanding or education about a condition, even if they refer to "my illness" or "my condition". It becomes NEEDS_REVIEW only when they ask for personalized assessment, interpretation of specific values, or treatment decisions.

IMPORTANT: Vague, non-urgent symptom mentions WITHOUT specific values, emergency indicators, or requests for personal diagnosis are SAFE. The chatbot will provide general information and ask clarifying follow-up questions naturally. Only classify as NEEDS_REVIEW when there are specific values, urgency, or explicit requests for personal medical assessment.

CRITICAL: When genuinely uncertain whether a question seeks personal medical advice or general education, classify as NEEDS_REVIEW. However, do not classify educational questions as NEEDS_REVIEW simply because the user mentions their own condition.

USER CONTEXT: {user_context}

USER QUESTION: {question}

Respond in this exact JSON format and nothing else:
{{"classification": "SAFE" or "NEEDS_REVIEW", "reasoning": "brief explanation", "confidence": "HIGH" or "MEDIUM" or "LOW"}}"""


async def classify_question(
    question: str,
    user_data: dict | None = None,
    is_logged_in: bool = False
) -> ClassificationResult:
    """
    Luokittelee käyttäjän kysymyksen SAFE tai NEEDS_REVIEW -kategoriaan.

    Virhetilanteissa palauttaa aina NEEDS_REVIEW (fail-safe).
    """
    try:
        if is_logged_in and user_data:
            user_context = (
                "User is logged in and has personal health data on file "
                "(conditions, medications, blood pressure, etc.). "
                "Questions that could relate to their personal data should be "
                "classified as NEEDS_REVIEW."
            )
        else:
            user_context = "User is not logged in. No personal health data available."

        prompt = CLASSIFICATION_PROMPT.format(
            question=question,
            user_context=user_context
        )

        response = await classifier_llm.ainvoke(prompt)
        response_text = response.content.strip()

        # Poistetaan mahdolliset markdown-koodilohkot
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()

        result = json.loads(response_text)

        classification = Classification(result.get("classification", "NEEDS_REVIEW"))
        reasoning = result.get("reasoning", "No reasoning provided")
        confidence = result.get("confidence", "LOW")

        # Matala luottamus + SAFE -> ylennetään NEEDS_REVIEW:ksi
        if confidence == "LOW" and classification == Classification.SAFE:
            logger.info(
                f"Low confidence SAFE overridden to NEEDS_REVIEW. "
                f"Question: {question[:100]}"
            )
            classification = Classification.NEEDS_REVIEW
            reasoning += " [Overridden: low confidence SAFE -> NEEDS_REVIEW]"

        logger.info(
            f"Classification: {classification.value}, "
            f"Confidence: {confidence}, "
            f"Question: {question[:100]}"
        )

        return ClassificationResult(
            classification=classification,
            reasoning=reasoning,
            confidence=confidence
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse classifier response: {e}")
        return ClassificationResult(
            classification=Classification.NEEDS_REVIEW,
            reasoning="Classification failed (JSON parse error) - defaulting to NEEDS_REVIEW",
            confidence="LOW"
        )
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return ClassificationResult(
            classification=Classification.NEEDS_REVIEW,
            reasoning=f"Classification failed ({type(e).__name__}) - defaulting to NEEDS_REVIEW",
            confidence="LOW"
        )
