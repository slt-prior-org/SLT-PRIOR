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
    re.compile(r"\bsydänkohtau\w*\b", re.IGNORECASE),        # sydänkohtauksen, sydänkohtausta
    re.compile(r"\bsydänpysähdy\w*\b", re.IGNORECASE),       # sydänpysähdyksen
    re.compile(r"\baivohalvau\w*\b", re.IGNORECASE),         # aivohalvauksen, aivohalvausta
    re.compile(r"\bhengitysvaikeu\w*\b", re.IGNORECASE),     # hengitysvaikeuksia
    re.compile(r"\btajutto\w*\b", re.IGNORECASE),            # tajuttomana, tajuttomuuden
    re.compile(r"\belvyt\w*\b", re.IGNORECASE),              # elvytys, elvyttää, elvyttäkää, elvytykseen, elvytän
    re.compile(r"\bhengenahdist\w*\b", re.IGNORECASE),       # hengenahdistusta
    re.compile(r"\btukehtu\w*\b", re.IGNORECASE),            # tukehtuu, tukehtuminen, tukehtumassa, tukehtui
    re.compile(r"\bkourist\w*\b", re.IGNORECASE),            # kouristus, kouristelee, kouristaa, kouristuksia
    re.compile(                                                # vain verbimuodot, ei kuolematon/kuolevainen
        r"\bkuole(n|e|mme|tte|vat|taan|maisillaan|eko|si)\b"
        r"|\bkuolemassa\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bpyörty\w*\b", re.IGNORECASE),             # pyörtyi, pyörtynyt, pyörtyminen
    re.compile(r"\baivoverenvuod\w*\b", re.IGNORECASE),      # aivoverenvuodon, aivoverenvuotoa
    re.compile(r"\bambulanssi\w*\b", re.IGNORECASE),         # ambulanssin, ambulanssiin
]

EMERGENCY_PATTERNS_EN = [
    re.compile(r"\bheart\s+attack\w*\b", re.IGNORECASE),
    re.compile(r"\bstroke\b", re.IGNORECASE),
    re.compile(r"\bcan'?t\s+breathe\b", re.IGNORECASE),
    re.compile(r"\bunconscious\w*\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Kiireellisyyssignaalit — estävät poisjätön aina
# ---------------------------------------------------------------------------
URGENCY_SIGNALS = re.compile(
    r"\b(right now|right away|immediately|help me|need help|i need|call now|"
    r"nyt|heti|apua|auta|välittömästi|nopeasti|kiireesti)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Poisjättöpatternit — vähentävät vääriä hälytyksiä
# ---------------------------------------------------------------------------

# A) Kasvatukselliset kysymykset (FI)
_EXCL_EDU_FI = [
    re.compile(
        r"\b(mitä on|mikä on|miten|kuinka|kerro|selitä)\b"
        r".{0,80}\b(sydänkohtau|aivohalvau|elvyt|ambulanssi)\w*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(sydänkohtau|aivohalvau|elvyt|ambulanssi)\w*\b"
        r".{0,60}\b(tunnistaminen|yleisesti|tietoa|selitä|opas)\b",
        re.IGNORECASE,
    ),
]

# B) Kielikuvat (FI): "Kuolen nälkään"
_EXCL_FIG_FI = [
    re.compile(
        r"\bkuolen\b.{0,30}"
        r"\b(nälkään|janoon|nauruun|tylsyyteen|häpeään|innosta|väsymykseen|ikävästä)\b",
        re.IGNORECASE,
    ),
]

# C) Menneisyys/historia (FI)
_EXCL_PAST_FI = [
    re.compile(
        r"\b(sai|koki|tapahtui|kuoli|menehtyi)\b.{0,80}"
        r"\b(sydänkohtau|aivohalvau)\w*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(viime vuonna|kauan sitten|\d+ vuotta sitten|aikoinaan)\b",
        re.IGNORECASE,
    ),
]

# D) Kasvatukselliset kysymykset (EN)
_EXCL_EDU_EN = [
    re.compile(
        r"\b(what is|what are|how to|how do|tell me about|explain|describe)\b"
        r".{0,60}\b(heart attack|stroke|cardiac arrest|cpr|ambulance)\w*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(heart attack|stroke|cardiac arrest)\w*\b"
        r".{0,50}\b(symptoms?|signs?|in general|generally|information)\b",
        re.IGNORECASE,
    ),
]

# E) Kielikuvat (EN): "I'm dying of laughter"
_EXCL_FIG_EN = [
    re.compile(
        r"\b(im dying|i am dying|i'm dying)\b.{0,30}"
        r"\bof\s+(laughter|boredom|embarrassment|hunger|thirst|excitement|joy)\b",
        re.IGNORECASE,
    ),
]

# F) Menneisyys/historia (EN)
_EXCL_PAST_EN = [
    re.compile(
        r"\b(grandfather|grandmother|father|mother|dad|mom|parent|relative)\b"
        r".{0,40}\b(had|suffered|experienced)\b.{0,40}"
        r"\b(heart attack|stroke|cardiac arrest)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(heart attack|stroke)\b.{0,50}"
        r"\b(in\s+\d{4}|last year|years ago|in the past)\b",
        re.IGNORECASE,
    ),
]

NON_EMERGENCY_EXCLUSIONS: list[re.Pattern] = (
    _EXCL_EDU_FI + _EXCL_FIG_FI + _EXCL_PAST_FI
    + _EXCL_EDU_EN + _EXCL_FIG_EN + _EXCL_PAST_EN
)

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


def is_non_emergency_context(message_lower: str) -> bool:
    """Palauttaa True jos viesti on todennäköisesti väärä positiivi."""
    if URGENCY_SIGNALS.search(message_lower):
        return False   # kiireellisyyssignaali → älä koskaan jätä pois
    for pattern in NON_EMERGENCY_EXCLUSIONS:
        if pattern.search(message_lower):
            return True
    return False


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

    # Poisjätön tarkistus
    if is_non_emergency_context(message_lower):
        logger.debug(
            f"Emergency match suppressed (non-emergency context). "
            f"Keywords: {matched}, Message: {message[:100]}"
        )
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
