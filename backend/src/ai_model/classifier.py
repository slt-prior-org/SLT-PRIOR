"""
classifier.py

Luokittelee käyttäjän kysymykset kahteen kategoriaan:
- SAFE: yleinen terveystieto, johon AI voi vastata suoraan (ml. epämääräiset oiremaininnat)
- NEEDS_REVIEW: henkilökohtainen terveysarvio, joka vaatii ammattilaisen tarkistuksen

EU AI Act -yhteensopivuus: epäselvissä tapauksissa aina NEEDS_REVIEW (fail-safe).
"""

import json
import logging
from enum import Enum
from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

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
    model='gemini-2.5-flash-lite',
    temperature=0.0,
    max_tokens=300,
    google_api_key=settings.GOOGLE_API_KEY
)

def get_classifier_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0.0,
        max_tokens=300,
        google_api_key=settings.GOOGLE_API_KEY,
    )

CLASSIFICATION_PROMPT = """You are a safety classifier for a heart health chatbot focused on coronary artery disease.

CORE DECISION RULE:
Could a knowledgeable health educator answer this from public health guidelines \
(Käypä hoito, ESC) WITHOUT needing to know anything specific about this particular person?
- YES → SAFE (general health education, AI can respond directly)
- NO, the answer would require acting as this person's doctor → NEEDS_REVIEW

────────────────────────────────────────
CRITICAL PRIORITY OVERRIDE:
────────────────────────────────────────
ONLY classify as NEEDS_REVIEW if the user explicitly asks for:
- Request for personal diagnosis (e.g. "Do I have heart disease?", "Onko minulla sydänsairaus?")
- Request for personal risk assessment (e.g. "Am I at risk?", "Olenko riskissä sairastua?")
- Request for personal treatment or medication decision (e.g. "Should I take aspirin?", "Pitäisikö minun ottaa statiineja?")
- Sharing personal health measurements or lab results (e.g. "My blood pressure is 180/100", "Verenpaineeni on 160/95", "Sykeeni on levossa 110", "LDL-kolesterolini on 4.8")
- Asking whether their own symptom or situation is dangerous (e.g. "Is this dangerous?", "Onko se vaarallista?", "Should I be worried?", "Pitäisikö minun olla huolissaan?")
- Asking for interpretation of their own symptoms or test results (e.g. "What does this mean?", "Mitä tämä tarkoittaa?", "Is it too high?", "Onko se liikaa?", "Onko se huono?")

────────────────────────────────────────
NEEDS_REVIEW ONLY IF EXPLICIT:
────────────────────────────────────────
- "Is this dangerous?"
- "Do I have X?"
- "Should I take/change medication?"
- "What does MY result mean?"

────────────────────────────────────────
SYMPTOM DURATION / ABNORMAL CONTEXT RULE:
────────────────────────────────────────
A symptom-only statement is SAFE ONLY IF it is neutral and not medically concerning in context.

If the user mentions symptoms AND includes any of the following, classify as NEEDS_REVIEW:
- prolonged duration (e.g. "for days", "for weeks", "pitkään", "useita päiviä", "jatkunut")
- worsening or persistent pattern (e.g. "keeps getting worse", "jatkuu", "ei mene ohi")
- repeated or recurring episodes (e.g. "comes back", "toistuu")
- severity escalation (e.g. "severe", "worse than before", "pahempi kuin aiemmin")

Examples:
- "I have chest pain" → SAFE
- "Minulla on rintakipua" → SAFE
- "I have had chest pain for 3 days" → NEEDS_REVIEW
- "Rintakipu jatkunut useita päiviä" → NEEDS_REVIEW
- "Chest pain keeps coming back" → NEEDS_REVIEW

────────────────────────────────────────
SAFE ALWAYS INCLUDES:
────────────────────────────────────────
- General explanations of diseases, treatments, diagnostics, or medical concepts
  (e.g. "What is coronary artery disease?", "How do statins work?")
- Educational curiosity and learning questions
  (e.g. "What are risk factors?", "How does ECG work?")
- Conversational continuation requests
  (e.g. "Tell me more", "Explain again", "Go on", "Kerro lisää")
- Asking for general meaning of medical terms
  (e.g. "What does diagnosis mean in general?")
- Simply mentioning a symptom without asking for interpretation or danger assessment 
  (e.g. "I have chest pain", "Minulla on rintakipua") → SAFE

────────────────────────────────────────
SYMPTOM + EMOTIONAL CONTEXT RULE:
────────────────────────────────────────
Presence of emotional language such as "I am worried", "olen huolissani", 
or mild situational context does NOT trigger NEEDS_REVIEW.

Symptom descriptions remain SAFE unless the user explicitly asks:
- if it is dangerous
- what it means medically
- whether they should seek care
  
────────────────────────────────────────
USER DATA RULE:
────────────────────────────────────────
Logged-in status and personal data MUST NOT change classification
unless the user explicitly refers to:

- their lab results
- their medications
- their diagnosed conditions

Otherwise treat as general question → SAFE
  
EU AI Act compliance: When genuinely uncertain → NEEDS_REVIEW (fail-safe default).

USER CONTEXT: {user_context}
{conversation_history_section}USER QUESTION: {question}

Respond in this exact JSON format and nothing else:
{{"classification": "SAFE" or "NEEDS_REVIEW", "reasoning": "brief explanation", "confidence": "HIGH" or "MEDIUM" or "LOW"}}"""


async def classify_question(
    question: str,
    user_data: dict | None = None,
    is_logged_in: bool = False,
    conversation_history: list[dict] | None = None,
) -> ClassificationResult:
    """
    Luokittelee käyttäjän kysymyksen SAFE tai NEEDS_REVIEW -kategoriaan.

    Virhetilanteissa palauttaa aina NEEDS_REVIEW (fail-safe).
    """
    try:
        if is_logged_in and user_data:
            user_context = (
                "User is logged in and has personal health data available. "
                "This does NOT affect classification of general symptoms. "
                "Only explicit references to personal data (labs, medications, diagnoses) matter."
            )
        else:
            user_context = "User is not logged in. No personal health data available."

        if conversation_history:
            lines = []
            for msg in conversation_history[-10:]:
                role = "User" if msg["sender"] == "user" else "Assistant"
                lines.append(f"{role}: {msg['content']}")
            history_text = "\n".join(lines)
            conversation_history_section = (
                f"CONVERSATION HISTORY (oldest first):\n{history_text}\n"
                f"If the history reveals an accumulating pattern of cardiac symptoms, "
                f"classify as NEEDS_REVIEW even if the current message alone would be SAFE.\n"
                f"If the current message appears to be answering a follow-up question from the assistant "
                f"(e.g. a duration, severity, or yes/no reply), use the full conversation context "
                f"to determine the classification — do not evaluate the reply in isolation.\n\n"
            )
        else:
            conversation_history_section = ""

        prompt = CLASSIFICATION_PROMPT.format(
            question=question,
            user_context=user_context,
            conversation_history_section=conversation_history_section
        )

        llm = get_classifier_llm()
        response = await llm.ainvoke(prompt)
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
