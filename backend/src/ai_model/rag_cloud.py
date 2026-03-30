import re
from config import settings
from .vectorstore import initialize_vectorstore

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

# -----------------------------
# 1) Upotukset ja vektorivarasto
# -----------------------------
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
)

vectorstore = initialize_vectorstore(
    embeddings, settings.PERSIST_DIRECTORY, settings.BUCKET_NAME
)

# -----------------------------
# 2) Luodaan RAG-ketju (retriever + LLM + prompt)
# -----------------------------

llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash-lite',  # Gemini 2.0 Flash
    temperature=0.3,  # Alustava lämpötila
    max_tokens=1000,  # nostettu 500 -> 1000
    top_p=0.9,
    google_api_key=settings.GOOGLE_API_KEY
)

selector_llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash-lite',
    temperature=0.0,
    max_tokens=5,           # Vain numero vastauksessa
    google_api_key=settings.GOOGLE_API_KEY
)

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context and chat history to answer the question. "
    "Do not use any outside knowledge or make assumptions. "
    "Determine first whether the question is in Finnish or English, and respond in the same language. "

    "If the question is in English and the information is found in the context, first provide a concise answer. "
    "Then, naturally continue the conversation by asking a relevant follow-up question based on the user's query and chat history. "

    "If the question is in Finnish and the information is found in the context, first provide a concise answer. "
    "Sen jälkeen jatka keskustelua luontevasti kysymällä aiheeseen liittyvän jatkokysymyksen, joka auttaa käyttäjää syventämään ymmärrystään ottaen huomioon aikaisemman keskustelun. "

    "If the question is in English and the information is not found in the context, say: "
    "'Unfortunately, I do not have enough information on the topic you asked about. I recommend reaching out to a specialist or your healthcare provider if needed.' "
    "Then, naturally ask a relevant follow-up question based on the chat history to better understand the user's concern. "

    "If the question is in Finnish and the information is not found in the context, say: "
    "'Valitettavasti minulla ei ole riittävästi tietoa esittämääsi aiheeseen. Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon tarvittaessa.' "
    "Tämän jälkeen kysy luontevasti jatkokysymys, joka auttaa käyttäjää tarkentamaan tilannettaan ottaen huomioon aikaisemman keskustelun. "

    "\n\n"
    "Context: {context}\n\n"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)

rag_chain = prompt | llm


ALLOWED_HISTORY_CLASSIFICATIONS = {"safe", "needs_review", "emergency"}


def _filter_chat_history(chat_history: list[dict] | None):
    """
    Suodattaa mallille välitettävän historian vain tunnetusti luokiteltuihin
    viesteihin. Tämä vähentää testailun tai muun epäolennaisen historian
    vaikutusta RAG-vastaukseen.
    """
    filtered_history = []

    for message in chat_history or []:
        classification = message.get("classification")
        if classification is None:
            continue

        classification_value = str(classification).lower()
        if classification_value not in ALLOWED_HISTORY_CLASSIFICATIONS:
            continue

        filtered_history.append(message)

    return filtered_history


def _normalize_chat_history(chat_history: list[dict] | None):
    """
    Muuntaa tallennetun keskusteluhistorian LangChainin viestiolioiksi.
    Tukee sekä Mongo-tyyppistä sender-kenttää että LangChainin type-kenttää.
    """
    normalized_history = []
    for message in chat_history or []:
        sender = message.get("sender") or message.get("type")
        content = message.get("content", "")

        if sender in ("user", "human"):
            normalized_history.append(HumanMessage(content=content))
        elif sender in ("bot", "ai", "assistant"):
            normalized_history.append(AIMessage(content=content))

    return normalized_history


# -----------------------------
# 3) Dokumenttien haku: ensin threshold, tarvittaessa MMR-fallback
# -----------------------------
async def retrieve_with_fallback(
    user_input: str,
    vectorstore,
    top_k: int = 6,
    score_threshold: float = 0.6,
    fallback_k: int = 5
):
    """
    Hakee ensin dokumentit similarity_thresholdilla.
    Jos ei löydy tarpeeksi osumia, käyttää MMR-fallbackia.
    Palauttaa listan relevantteja dokumentteja.
    """

    # Threshold-haku
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": top_k, "score_threshold": score_threshold}
    )

    relevant_docs = await retriever.ainvoke(user_input)

    # Fallback tarvittaessa
    if not relevant_docs:
        print("⚠️ Ei tarpeeksi relevantteja osumia threshold-hausta – otetaan käyttöön fallback MMR...")
        fallback_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": fallback_k}
        )
        relevant_docs = await fallback_retriever.ainvoke(user_input)

    return relevant_docs

def _build_context_and_sources(relevant_docs):
    context_parts = []
    grouped_sources = {}

    for index, doc in enumerate(relevant_docs, start=1):
        metadata = doc.metadata or {}
        source_name = metadata.get("source", "unknown")
        page = metadata.get("page")

        label = f"[{index}] Source: {source_name}"
        if page is not None:
            label += f", page {page}"

        context_parts.append(f"{label}\n{doc.page_content}")

        if source_name not in grouped_sources:
            grouped_sources[source_name] = {
                "source": source_name,
                "pages": [],
                "preview": doc.page_content[:220].strip(),
            }

        if page is not None and page not in grouped_sources[source_name]["pages"]:
            grouped_sources[source_name]["pages"].append(page)

    deduped_sources = []
    for new_index, item in enumerate(grouped_sources.values(), start=1):
        item["pages"] = sorted(item["pages"])
        item["index"] = new_index
        deduped_sources.append(item)

    return "\n\n".join(context_parts), deduped_sources

# -----------------------------
# 4) Hoitosuositusotteiden haku ilman LLM-kutsua
# -----------------------------
def _trim_to_sentence(text: str, max_chars: int = 500) -> str:
    """Katkaisee tekstin max_chars merkin kohdalla lauserajaan."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    for punct in (". ", "! ", "? "):
        idx = window.rfind(punct)
        if idx != -1:
            return window[:idx + 1]
    idx = window.rfind(" ")
    return (window[:idx] + "...") if idx != -1 else (window + "...")

def _clean_chunk_text(text: str, min_broken_run: int = 4) -> str:
    """
    Puhdistaa PDF-chunkin tekstin ennen laaduntarkistusta:
    1. PyPDF2:n rikkinäinen välistys ('Ko hon neen ve ren') — poistetaan lyhyiden
       sanojen juoksu alussa (≥4 peräkkäistä ≤4-merkkistä alpha-sanaa).
    2. Kuva/Figure-kuvatekstilohkot alussa ('Kuva 6. ... Kuva 7. ...') — poistetaan.
    3. Päivämäärät (esim. '4.3.2025 at 17.13') — poistetaan.
    4. Sivunumerot (esim. '15/29') — poistetaan.
    5. URL-osoitteet — poistetaan.
    6. Kuva/Figure-viittaukset kesken tekstin — poistetaan.
    7. Ylimääräiset välilyönnit normalisoidaan.
    Palauttaa tyhjän merkkijonon jos puhdistuksen jälkeen alle 100 merkkiä jäljellä.
    """
    t = text.strip()

    # 1) Rikkinäinen PyPDF2-prefix
    words = t.split()
    i = 0
    while i < len(words) and words[i].isalpha() and len(words[i]) <= 4:
        i += 1
    if i >= min_broken_run:
        t = " ".join(words[i:])

    # 2) Kuva/Figure-kuvatekstit alussa
    t = re.sub(r'^(?:(?:Kuva|Figure)\s+\d+\.[^\n]*\n?)+', '', t).strip()

    # 3) Päivämäärät (esim. "4.3.2025 at 17.13", "12.11.2024") — ilman \b koska pisteet aiheuttavat ongelmia
    t = re.sub(r'\d{1,2}\.\d{1,2}\.\d{4}(?:\s+(?:at\s+)?\d{1,2}[.:]\d{2})?', '', t)

    # 4) Sivunumerot (esim. "15/29") — ei poisteta verenpainelukemia kuten "140/90 mmHg"
    t = re.sub(r'\b\d+\s*/\s*\d+\b(?!\s*mmHg)', '', t)

    # 5) URL-osoitteet
    t = re.sub(r'https?://\S*', '', t)

    # 6) Kuva/Figure-viittaukset kesken tekstin (esim. "Figure 7.", "Kuva 3.")
    t = re.sub(r'(?:Kuva|Figure)\s+\d+\.', '', t)

    # 7) Ylimääräiset välilyönnit
    t = re.sub(r'[ \t]{2,}', ' ', t).strip()

    return t if len(t) >= 100 else ""


def _is_quality_excerpt(text: str, min_chars: int = 150) -> bool:
    """
    Palauttaa True jos teksti vaikuttaa oikealta hoitosuositustekstiltä.
    Hylkää navigaatio-, mainos- ja roskatekstit.
    """
    t = text.strip()
    if len(t) < min_chars:
        return False
    # Hylkää rikkinäinen PyPDF2-teksti joka on hajallaan koko chunkissa
    # (yksittäisiä kirjaimia kuten "e v o v i t" on yli 15% alpha-sanoista)
    alpha_tokens = [w for w in t.split() if w.isalpha()]
    if alpha_tokens:
        single_char_ratio = sum(1 for w in alpha_tokens if len(w) == 1) / len(alpha_tokens)
        if single_char_ratio > 0.15:
            return False
    if "utm_source" in t or "utm_medium" in t:
        return False
    if ">>" in t:
        return False
    if t.count("http") > 3:
        return False
    special = sum(1 for c in t if not c.isalnum() and not c.isspace() and c not in ".,;:!?-()\"'/")
    if special / max(len(t), 1) > 0.30:
        return False
    return True

# EI KÄYTÖSSÄ, vaan valitaan LLM:llä. Jätetty varmuuden vuoksi talteen.
_RECOMMENDATION_KEYWORDS = [
    # Yleiset suositussanat
    "suositell", "tulisi", "on tärkeää", "hoitosuositus",
    "hoidossa käytetään", "ensisijaisesti", "elintapa", "ohje",
    "voidaan hoitaa", "on suositeltavaa",
    # Hoitosuositusspesifiset termit
    "käypä hoito", "hoitosuosituksen", "näytönaste",
    "suositusluokka", "duodecim", "lääkäriseura",
    "hoito-ohje", "käypähoito", "hoitoprotokolla",
    "lääkehoito suosit", "aloitetaan kun", "annostellaan",
]
# EI KÄYTÖSSÄ
def _recommendation_score(text: str) -> int:
    """Laskee suositussanaston esiintymismäärän tekstissä."""
    lower = text.lower()
    return sum(1 for kw in _RECOMMENDATION_KEYWORDS if kw in lower)


async def _select_best_chunk(query: str, docs: list) -> int:
    """
    Pyytää LLM:ltä indeksin (1-N) parhaalle hoitosuosituksia sisältävälle
    chunkille. Palauttaa 0-pohjaisen indeksin (oletuksena 0 virhetilanteessa).
    """
    snippets = "\n\n".join(
        f"[{i+1}] {doc.page_content[:500]}..."
        for i, doc in enumerate(docs)
    )
    prompt = (
        "You are helping a patient find the most relevant health guideline.\n"
        "Patient question: " + query + "\n\n"
        "Excerpts from Finnish health guideline PDFs:\n" + snippets + "\n\n"
        "Which excerpt number (1-" + str(len(docs)) + ") most directly answers "
        "the patient's question with concrete guidance (e.g. when to start/stop "
        "treatment, what to do)? Prefer text that answers the question directly, "
        "not tables of numeric thresholds or treatment algorithms. "
        "Reply with ONLY the number."
    )
    try:
        result = await selector_llm.ainvoke(prompt)
        idx = int(result.content.strip()) - 1
        return max(0, min(idx, len(docs) - 1))
    except Exception:
        return 0  # Fallback: ensimmäinen


async def _extract_relevant_sentences(query: str, chunk: str) -> str:
    """
    Pyytää LLM:ltä 2-3 lausetta chunkista, jotka vastaavat suoraan kysymykseen.
    Palauttaa alkuperäiset lauseet sellaisenaan — ei muotoile eikä lisää sisältöä.
    Fallback: _trim_to_sentence virhetilanteessa.
    """
    prompt = (
        "From the following health guideline text, copy the 2-3 sentences that "
        "most directly answer the question: '" + query + "'\n\n"
        "Guideline text:\n" + chunk + "\n\n"
        "Rules:\n"
        "- Copy sentences verbatim from the text, do not rephrase or add information.\n"
        "- Always return only the sentence(s) themselves — no preamble, no explanation, "
        "no phrases like 'The most relevant sentence is' or 'No sentence answers'.\n"
        "- If no sentence directly answers the question, copy the single most relevant sentence."
    )
    try:
        result = await llm.ainvoke(prompt)
        extracted = result.content.strip()
        # Poistetaan mahdollinen LLM-preamble (esim. "The most relevant sentence is: ...")
        extracted = re.sub(
            r'^(?:No sentence[^.]*\.\s*)?(?:The (?:most relevant|best matching) sentence is:?\s*)',
            '', extracted, flags=re.IGNORECASE
        ).strip()
        return extracted if extracted else _trim_to_sentence(chunk, max_chars=500)
    except Exception:
        return _trim_to_sentence(chunk, max_chars=500)


def _verify_verbatim(extracted: str, source: str) -> bool:
    """
    Tarkistaa, että jokainen extracted-lauseista löytyy sanatarkasti source-tekstistä
    (whitespace normalisoituna, kirjainkoosta riippumatta).
    """
    def _norm(t: str) -> str:
        return re.sub(r'\s+', ' ', t).strip().lower()

    source_norm = _norm(source)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', extracted) if len(s.strip()) > 15]
    if not sentences:
        return False
    return all(_norm(s) in source_norm for s in sentences)


async def get_guideline_excerpt(query: str, score_threshold: float = 0.65) -> dict | None:
    """
    Hakee relevanteimman Chroma-chunkin kyselyn perusteella.
    Palauttaa {"text": str, "source": str} tai None.
    Hakee k=10 kandidaattia, suodattaa laaturoskan, pyytää LLM:ltä
    parhaan indeksin, ja poimii LLM:llä relevanteimmat lauseet.
    """
    try:
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 10, "score_threshold": score_threshold}
        )
        docs = await retriever.ainvoke(query)
        if not docs:
            return None

        # Suodata laaturoskasta
        quality_docs = []
        for doc in docs:
            text = _clean_chunk_text(doc.page_content)
            if text and _is_quality_excerpt(text):
                quality_docs.append(doc)

        if not quality_docs:
            return None

        # LLM valitsee parhaan indeksin
        best_idx = await _select_best_chunk(query, quality_docs)
        best_doc = quality_docs[best_idx]
        text = _clean_chunk_text(best_doc.page_content)

        # LLM poimii relevanteimmat lauseet kysymykseen nähden
        extracted = await _extract_relevant_sentences(query, text)

        # Varmistetaan, että LLM ei parafrasoinut — jos ei löydy lähdetekstistä, käytetään mekaanista trimmeriä
        if not _verify_verbatim(extracted, text):
            print("DEBUG _verify_verbatim failed — falling back to _trim_to_sentence")
            extracted = _trim_to_sentence(text, max_chars=500)

        return {
            "text": extracted,
            "source": best_doc.metadata.get("source", "käypähoito.fi")
        }

    except Exception as e:
        print(f"get_guideline_excerpt error: {e}")
        return None

# -----------------------------
# 5) Julkaistava funktio, jolla saa RAG-vastauksen
# -----------------------------
async def get_rag_response(
    user_input: str,
    chat_history: list[dict] | None = None,
) -> dict:
    """
    Kysyy RAG-ketjulta (Chroma+GEMINI) ja palauttaa vastauksen sekä lähteet.
    Vastauksen muodostamiseen käytetään annettua chat-historiaa.
    """
    filtered_history = _filter_chat_history(chat_history)
    history_messages = _normalize_chat_history(filtered_history)

    # Hae dokumentit threshold + fallback -logiikalla
    relevant_docs = await retrieve_with_fallback(user_input, vectorstore)

    if not relevant_docs:
        no_info_msg = (
            "Valitettavasti minulla ei ole riittävästi tietoa kysymääsi aiheeseen. "
            "Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon."
        )
        return {
            "answer": no_info_msg,
            "sources": []
        }

    context_text, sources = _build_context_and_sources(relevant_docs)

    # Vastauksen generointi
    response = await rag_chain.ainvoke({
        "context": context_text,
        "chat_history": history_messages,
        "input": user_input
    })

    return {
        "answer": response.content,
        "sources": sources
    }

async def translate_excerpt(text: str, target: str = "en") -> str:
    """
    Kääntää hoitosuositusotteen kohde kielelle.
    target="en" → englanniksi, target="fi" → suomeksi.
    Palauttaa alkuperäisen tekstin virhetilanteessa.
    """
    lang = "Finnish" if target == "fi" else "English"
    prompt = (
        f"Translate the following health guideline excerpt to {lang}. "
        "Translate faithfully — do not add, remove, or interpret any medical content. "
        "Return only the translated text, nothing else.\n\n"
        + text
    )
    try:
        result = await llm.ainvoke(prompt)
        return result.content.strip()
    except Exception:
        return text


async def generate_draft_response(user_input: str, chat_history: list[dict] | None = None) -> str:
    """Generoi RAG-luonnosvastauksen ilman muistiin tallennusta."""
    result = await get_rag_response(
        user_input,
        chat_history=chat_history
    )
    return result["answer"]
