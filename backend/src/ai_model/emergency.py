"""
emergency.py

Hätätilanteen tunnistus käyttäjän viestistä avainsana- ja regex-pohjaisesti.
Ei käytä LLM:ää – puhdas Python-toteutus, synkroninen ja nopea (<1 ms).

Tunnistaa sekä suomen- että englanninkieliset hätätilanneilmaisut
ja palauttaa kaksikielisen hätäviestin numerolla 112.
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmergencyResult:
    matched_keywords: list[str]
    emergency_message_fi: str
    emergency_message_en: str


# ---------------------------------------------------------------------------
# Avainsanat – täsmäsanat (case-insensitive substring match)
# ---------------------------------------------------------------------------

EMERGENCY_KEYWORDS_EN = [
    "heart attack",
    "cardiac arrest",
    "chest pain",
    "stroke",
    "can't breathe",
    "cannot breathe",
    "cant breathe",
    "unable to breathe",
    "difficulty breathing",
    "having a seizure",
    "seizure",
    "unconscious",
    "not breathing",
    "stopped breathing",
    "choking",
    "severe bleeding",
    "heavy bleeding",
    "anaphylaxis",
    "anaphylactic shock",
    "collapsed",
    "unresponsive",
    "sudden numbness",
    "sudden weakness",
    "sudden confusion",
    "slurred speech",
    "loss of consciousness",
    "cpr",
    "call 911",
    "call 112",
    "call an ambulance",
    "i'm dying",
    "im dying",
    "i am dying",
]

EMERGENCY_KEYWORDS_FI = [
    "sydänkohtaus",
    "sydänpysähdys",
    "rintakipu",
    "aivohalvaus",
    "aivoverenvuoto",
    "aivoverenkiertohäiriö",
    "aivotapahtuma",
    "hengitysvaikeu",      # osuu: hengitysvaikeus, hengitysvaikeuksia
    "en pysty hengittämään",
    "en saa henkeä",
    "ei saa henkeä",
    "ei pysty hengittämään",
    "hengenahdistus",
    "tajuton",
    "tajuttomuus",
    "menettänyt tajunnan",
    "menetti tajuntansa",
    "tukehtu",             # osuu: tukehtuu, tukehtuminen, tukehtumassa
    "kouristus",
    "kouristelee",
    "kouristelu",
    "kouristaa",
    "elvytys",
    "elvyttä",             # osuu: elvyttää, elvyttäkää, elvättämään
    "elvytän",
    "elvytetään",
    "soita 112",
    "ambulanssi",
    "kuolen",
    "kuolemassa",
    "kuolee",
    "kuollut",
    "vakava verenvuoto",
    "vuotaa verta",
    "anafylaksia",
    "anafylaktinen",
    "sydän pysähty",       # osuu: sydän pysähtyi, sydän pysähtyy
    "menetän tajun",       # osuu: menetän tajuntani
    "pyörryn",
    "pyörtyi",
    "pyörtynyt",
]

# ---------------------------------------------------------------------------
# Regex-patternit suomen taivutusmuodoille
# ---------------------------------------------------------------------------

EMERGENCY_PATTERNS_FI = [
    re.compile(r"\brintakipu\w*\b", re.IGNORECASE),          # rintakipua, rintakipuja
    re.compile(r"\bsydänkohtau\w*\b", re.IGNORECASE),        # sydänkohtauksen, sydänkohtausta
    re.compile(r"\bsydänpysähdy\w*\b", re.IGNORECASE),       # sydänpysähdyksen
    re.compile(r"\baivohalvau\w*\b", re.IGNORECASE),         # aivohalvauksen, aivohalvausta
    re.compile(r"\bhengitysvaikeu\w*\b", re.IGNORECASE),     # hengitysvaikeuksia
    re.compile(r"\btajutto\w*\b", re.IGNORECASE),            # tajuttomana, tajuttomuuden
    re.compile(r"\belvyt\w*\b", re.IGNORECASE),              # elvytys, elvyttää, elvyttäkää, elvytykseen, elvytän
    re.compile(r"\bhengenahdist\w*\b", re.IGNORECASE),       # hengenahdistusta
    re.compile(r"\btukehtu\w*\b", re.IGNORECASE),            # tukehtuu, tukehtuminen, tukehtumassa, tukehtui
    re.compile(r"\bkourist\w*\b", re.IGNORECASE),            # kouristus, kouristelee, kouristaa, kouristuksia
    re.compile(r"\bkuole\w*\b", re.IGNORECASE),              # kuolen, kuolee, kuolemassa, kuolemaisillaan
    re.compile(r"\bpyörty\w*\b", re.IGNORECASE),             # pyörtyi, pyörtynyt, pyörtyminen
    re.compile(r"\baivoverenvuod\w*\b", re.IGNORECASE),      # aivoverenvuodon, aivoverenvuotoa
    re.compile(r"\bambulanssi\w*\b", re.IGNORECASE),         # ambulanssin, ambulanssiin
]

EMERGENCY_PATTERNS_EN = [
    re.compile(r"\bheart\s+attack\w*\b", re.IGNORECASE),
    re.compile(r"\bchest\s+pain\w*\b", re.IGNORECASE),
    re.compile(r"\bstroke\b", re.IGNORECASE),
    re.compile(r"\bcan'?t\s+breathe\b", re.IGNORECASE),
    re.compile(r"\bunconscious\w*\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Hätäviesti
# ---------------------------------------------------------------------------

EMERGENCY_MESSAGE_FI = (
    "<strong>⚠️ Tämä vaikuttaa hätätilanteelta.</strong><br><br>"
    "Jos sinulla tai jollakin lähelläsi on henkeä uhkaava tilanne, "
    "<strong>soita hätänumeroon 112 välittömästi.</strong><br><br>"
    "Tämä chatbot ei voi antaa ensiapua eikä korvata hätäpalvelua."
)

EMERGENCY_MESSAGE_EN = (
    "<strong>⚠️ This appears to be an emergency situation.</strong><br><br>"
    "If you or someone near you is in a life-threatening situation, "
    "<strong>call the emergency number 112 immediately.</strong><br><br>"
    "This chatbot cannot provide first aid or replace emergency services."
)


def detect_emergency(message: str) -> EmergencyResult | None:
    """
    Tarkistaa sisältääkö viesti hätätilannetta viittaavia avainsanoja.

    Palauttaa EmergencyResult-olion jos osuma löytyy, muuten None.
    Synkroninen funktio – ei async, ei LLM-kutsua.
    """
    if not message or not message.strip():
        return None

    message_lower = message.lower()
    matched: list[str] = []

    # 1) Tarkista avainsanat (substring match)
    for keyword in EMERGENCY_KEYWORDS_EN:
        if keyword in message_lower:
            matched.append(keyword)

    for keyword in EMERGENCY_KEYWORDS_FI:
        if keyword in message_lower:
            matched.append(keyword)

    # 2) Tarkista regex-patternit
    for pattern in EMERGENCY_PATTERNS_FI:
        if pattern.search(message_lower):
            match_text = pattern.search(message_lower).group()
            if match_text not in matched:
                matched.append(match_text)

    for pattern in EMERGENCY_PATTERNS_EN:
        if pattern.search(message_lower):
            match_text = pattern.search(message_lower).group()
            if match_text not in matched:
                matched.append(match_text)

    if not matched:
        return None

    logger.warning(
        f"EMERGENCY detected! Keywords: {matched}, "
        f"Message: {message[:100]}"
    )

    combined_message = (
        f"{EMERGENCY_MESSAGE_FI}<br><br>---<br><br>{EMERGENCY_MESSAGE_EN}"
    )

    return EmergencyResult(
        matched_keywords=matched,
        emergency_message_fi=EMERGENCY_MESSAGE_FI,
        emergency_message_en=combined_message,
    )
