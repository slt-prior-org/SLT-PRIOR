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
# Hätätilanneilmaisujen painotukset –> vaikuttavat lopulliseen riskiluokitukseen
# ---------------------------------------------------------------------------
EMERGENCY_SCORE_THRESHOLD = 12

EXERTIONAL_DYSPNEA = re.compile(
    r"\b(rasituksessa|rasituksesta|rasituksen\s+aikana|after\s+exercise|on\s+exertion|during\s+exercise)\b",
    re.IGNORECASE,
)

EMERGENCY_SIGNAL_PATTERNS_FI = [
    (re.compile(r"\b(eloton|paineluelvy\w*|elvyt\w*)\b", re.IGNORECASE), "resuscitation", 25),
    (re.compile(r"\b(soita\s*112|ambulanssi\w*)\b", re.IGNORECASE), "call_ambulance", 25),
    (re.compile(r"\b(en\s+saa\s+henk[eä]\w*|ei\s+saa\s+henk[eä]\w*|en\s+pysty\s+hengittämään|ei\s+pysty\s+hengittämään|henki ei kulje)\b", re.IGNORECASE), "respiratory_failure", 25),
    (re.compile(r"\b(tukehtu\w*|tukehtuu|tukehtumassa|tukehtui)\b", re.IGNORECASE), "asphyxia", 22),
    (re.compile(r"\b(sydänkohtau\w*|sydänpysähdy\w*|aivohalvau\w*|aivoverenvuod\w*)\b", re.IGNORECASE), "acute_event", 22),
    (re.compile(r"\b(tajut\w*|menettänyt tajunnan|menetti tajuntansa|taju lähtee|meinaa taju lähteä|pyörty\w*)\b", re.IGNORECASE), "loss_of_consciousness", 20),
    (re.compile(r"\b(kourist\w*)\b", re.IGNORECASE), "seizure", 20),
    (re.compile(r"\b(kuole\w*|kuollut)\b", re.IGNORECASE), "death_statement", 20),
    (re.compile(r"\b(hengenahdist\w*|hengitysvaikeu\w*)\b", re.IGNORECASE), "respiratory_distress", 16),
    (re.compile(r"\b(verenvuod\w*|vuotaa verta|paljon verta|verta tulee|runsaa?sti verta)\b", re.IGNORECASE), "severe_bleeding", 20),
    (re.compile(r"\b(en\s+saa\s+tyrehtymään|ei\s+saa\s+tyrehtymään)\b", re.IGNORECASE), "bleeding_uncontrolled", 22),
    (re.compile(r"\b(rintakipu|rintaa\s+puristaa|rinnan\s+puristaa|rintaa\s+painaa|rinnan\s+painaa)\b", re.IGNORECASE), "chest_pain", 6),
    (re.compile(r"\bnitro\w*\b", re.IGNORECASE), "nitro", 8),
    (re.compile(
        r"\b(ei\s+helpotu|ei\s+ohitu|ei\s+ole\s+helpottanut|puristaa\s+edelleen|puristaa\s+vielä|jatkuu\w*|jatkunut|jatkuva|ei\s+mene\s+ohi|ei\s+ota\s+hellittää)\b",
        re.IGNORECASE,
    ), "not_relieved", 6),
    (re.compile(r"\b(levossa|levollakaan|edes\s+levossa|ei\s+helpotu\s+levossa|ei\s+ohitu\s+levossa)\b", re.IGNORECASE), "at_rest", 6),
    (re.compile(r"\b(pistos|pistopaik\w*)\b", re.IGNORECASE), "injection_site", 8),
    (re.compile(r"\b(turpoaa\w*|turvot\w*)\b", re.IGNORECASE), "swelling", 8),
    (re.compile(r"\b(rytmi(häiriö|häiriöt|häiriötuntemus)|rytmihäiriö)\b", re.IGNORECASE), "arrhythmia", 8),
    (re.compile(r"\b(pahen\w*|suurenee|koko\s*ajan|kokoajan|jatkuvasti|olo pahenee|olo huononee)\b", re.IGNORECASE), "worsening", 5),
    (re.compile(r"\b(kova|todella kova|todella paljon|paljon|hallitsematon)\b", re.IGNORECASE), "severity", 4),
]

EMERGENCY_SIGNAL_PATTERNS_EN = [
    (re.compile(r"\b(heart\s+attack|cardiac\s+arrest|stroke)\b", re.IGNORECASE), "acute_event", 22),
    (re.compile(r"\b(can'?t|cannot|unable)\s+(to\s+)?breathe\b", re.IGNORECASE), "respiratory_failure", 25),
    (re.compile(r"\b(difficulty\s+breathing|hard\s+to\s+breathe|really\s+hard\s+to\s+breathe|breathing\s+problems?)\b", re.IGNORECASE), "respiratory_distress", 16),
    (re.compile(r"\b(choking|choke|unable\s+to\s+breathe|airway\s+blocked)\b", re.IGNORECASE), "asphyxia", 20),
    (re.compile(r"\b(unconscious|passed\s+out|faint(ed|ing)?|loss\s+of\s+consciousness|black(ed)?\s*out)\b", re.IGNORECASE), "loss_of_consciousness", 20),
    (re.compile(r"\b(i\s*('?m|am)\s+dying|im\s+dying)\b", re.IGNORECASE), "dying_statement", 20),
    (re.compile(r"\b(cpr|perform\s+cpr|start\s+cpr|resuscitation)\b", re.IGNORECASE), "resuscitation", 18),
    (re.compile(r"\b(call(\s+an)?\s+ambulance|call\s+(911|112))\b", re.IGNORECASE), "call_ambulance", 25),
    (re.compile(r"\b(severe|heavy|lots\s+of)\s+bleeding\b|\bbleeding\s+(heavily|a lot)\b", re.IGNORECASE), "severe_bleeding", 18),
    (re.compile(r"\b(chest\s+pain|chest\s+pressure|pain\s+in\s+the\s+chest|chest\s+hurts|chest\s+discomfort)\b", re.IGNORECASE), "chest_pain", 6),
    (re.compile(r"\bnitro\b", re.IGNORECASE), "nitro", 8),
    (re.compile(r"\b(not\s+relieved|won' ?t\s+go\s+away|will\s+not\s+go\s+away|doesn'?t\s+go\s+away|does\s+not\s+go\s+away|doesn'?t\s+get\s+better|does\s+not\s+get\s+better|persists|persistent|still\s+(there|here|pain|hurts)|keeps\s+hurting)\b", re.IGNORECASE), "not_relieved", 6),
    (re.compile(r"\b(at\s+rest|while\s+resting|while\s+rest|even\s+at\s+rest|not\s+relieved\s+at\s+rest|doesn'?t\s+go\s+away\s+at\s+rest|does\s+not\s+go\s+away\s+at\s+rest|still\s+there\s+at\s+rest)\b", re.IGNORECASE), "at_rest", 6),
    (re.compile(r"\b(injection\s+site|needle\s+site|site\s+is\s+bleeding)\b", re.IGNORECASE), "injection_site", 8),
    (re.compile(r"\b(swelling|growing\s+swelling|increasing\s+swelling)\b", re.IGNORECASE), "swelling", 8),
    (re.compile(r"\b(arrhythmia|irregular\s+heartbeat|palpitations|racing\s+heart)\b", re.IGNORECASE), "arrhythmia", 8),
    (re.compile(r"\b(worsen|worsening|getting\s+worse|increasing\s+pain|growing\s+swelling|feeling\s+worse)\b", re.IGNORECASE), "worsening", 5),
    (re.compile(r"\b(severe|very\s+severe|really\s+bad|uncontrolled|a lot|heavy)\b", re.IGNORECASE), "severity", 4),
]


def extract_signal_matches(
    patterns: list[tuple[re.Pattern, str, int]],
    message_lower: str,
    matched: list[str],
) -> tuple[int, set[str]]:
    score = 0
    categories: set[str] = set()
    for pattern, category, weight in patterns:
        match = pattern.search(message_lower)
        if not match:
            continue
        if category not in categories:
            categories.add(category)
            score += weight
        match_text = match.group().strip()
        if match_text and match_text not in matched:
            matched.append(match_text)
    return score, categories

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
    Tarkistaa sisältääkö viesti hätätilannetta viittaavia signaaleja.

    Palauttaa EmergencyResult-olion vain, jos viesti on riittävän korkean
    riskiluokituksen mukainen hätätilanne. Tämä estää esimerkiksi pelkän
    rasituksessa tapahtuvan hengitysvaikeuden automaattisen emergency-luokituksen.
    """
    if not message or not message.strip():
        return None

    message_lower = message.lower()
    matched: list[str] = []

    score_fi, signal_categories_fi = extract_signal_matches(
        EMERGENCY_SIGNAL_PATTERNS_FI,
        message_lower,
        matched,
    )
    score_en, signal_categories_en = extract_signal_matches(
        EMERGENCY_SIGNAL_PATTERNS_EN,
        message_lower,
        matched,
    )

    total_score = score_fi + score_en
    signal_categories = signal_categories_fi | signal_categories_en

    if not matched:
        return None

    if (
        signal_categories == {"respiratory_distress"}
        and EXERTIONAL_DYSPNEA.search(message_lower)
    ):
        logger.debug(
            "Emergency suppressed: exertional dyspnea without other acute signals. "
            f"Score {total_score}, Message: {message[:100]}"
        )
        return None

    if is_non_emergency_context(message_lower):
        logger.debug(
            f"Emergency match suppressed (non-emergency context). "
            f"Keywords: {matched}, Message: {message[:100]}"
        )
        return None

    # Chest pain combinations that should trigger emergency even when
    # the single symptom score would otherwise be marginal.
    if "chest_pain" in signal_categories:
        if "not_relieved" in signal_categories:
            if (
                "at_rest" in signal_categories
                or "worsening" in signal_categories
                or "loss_of_consciousness" in signal_categories
                or "respiratory_distress" in signal_categories
                or "respiratory_failure" in signal_categories
                or "nitro" in signal_categories
            ):
                logger.debug(
                    "Emergency override: chest pain with not_relieved combination. "
                    f"Signals: {signal_categories}, Message: {message[:100]}"
                )
                total_score = max(total_score, EMERGENCY_SCORE_THRESHOLD)
        if "loss_of_consciousness" in signal_categories:
            logger.debug(
                "Emergency override: chest pain with loss of consciousness. "
                f"Signals: {signal_categories}, Message: {message[:100]}"
            )
            total_score = max(total_score, EMERGENCY_SCORE_THRESHOLD)
        if "respiratory_distress" in signal_categories or "respiratory_failure" in signal_categories:
            logger.debug(
                "Emergency override: chest pain with respiratory distress/failure. "
                f"Signals: {signal_categories}, Message: {message[:100]}"
            )
            total_score = max(total_score, EMERGENCY_SCORE_THRESHOLD)

    if total_score < EMERGENCY_SCORE_THRESHOLD:
        logger.debug(
            f"Emergency not triggered (urgent review only). "
            f"Score: {total_score}, Signals: {signal_categories}, Message: {message[:100]}"
        )
        return None

    logger.warning(
        f"EMERGENCY detected! Score: {total_score}, Signals: {signal_categories}, "
        f"Keywords: {matched}, Message: {message[:100]}"
    )

    combined_message = (
        f"{EMERGENCY_MESSAGE_FI}<br><br>---<br><br>{EMERGENCY_MESSAGE_EN}"
    )

    return EmergencyResult(
        matched_keywords=matched,
        emergency_message_fi=EMERGENCY_MESSAGE_FI,
        emergency_message_en=combined_message,
    )
