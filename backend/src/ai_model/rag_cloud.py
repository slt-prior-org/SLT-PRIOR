import re
from config import settings
from .vectorstore import initialize_vectorstore

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory

# ----------------------------- 
# 1) Embeddings + Vectorstore 
# -----------------------------
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
)

vectorstore = initialize_vectorstore(embeddings, settings.PERSIST_DIRECTORY, settings.BUCKET_NAME)

# -----------------------------
# 2) Luodaan RAG-ketju (retriever + LLM + prompt)
# -----------------------------

llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-001', # Gemini 2.0 Flash
    temperature=0.3, # Alustava lämpötila
    max_tokens=1000,    # nostettu 500 -> 1000
    top_p=0.9,
    google_api_key=settings.GOOGLE_API_KEY
)

selector_llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-001',
    temperature=0.0,
    max_tokens=5,           # Vain numero vastauksessa
    google_api_key=settings.GOOGLE_API_KEY
)

# Alustetaan keskustelumuisti
memory = InMemoryChatMessageHistory()

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
    "Chat history: {chat_history}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)

rag_chain = prompt | llm

# -----------------------------
# 3) Dokumenttien haku: ensin threshold, tarvittaessa MMR-fallback
# -----------------------------
async def retrieve_with_fallback(user_input: str, vectorstore, top_k: int = 6, score_threshold: float = 0.6, fallback_k: int = 5):
    """
    Hakee ensin dokumentit similarity_thresholdilla. 
    Jos ei löydy tarpeeksi osumia, käyttää MMR-fallbackia.
    Palauttaa listan relevantteja dokumentteja.
    """

     # Threshold-haku
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold", # Vain dokumentit, jotka ovat riittävän lähellä käyttäjän kysymystä, otetaan mukaan.
        search_kwargs={"k": top_k, "score_threshold": score_threshold} # Kysytään 6 eniten samankaltaista dokumenttia, joista vain ne, joiden samankaltaisuus on yli 0.6, otetaan mukaan.
    )   
    
    relevant_docs = await retriever.ainvoke(user_input)

    # Fallback tarvittaessa
    if not relevant_docs:
        print("⚠️ Ei tarpeeksi relevantteja osumia threshold-hausta – otetaan käyttöön fallback MMR...")
        fallback_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": fallback_k}#, "fetch_k": 20, "lambda_mult": 0.5}
        )
        relevant_docs = await fallback_retriever.ainvoke(user_input)

    return relevant_docs

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

    return t if len(t) >= 100 else ""


def _is_quality_excerpt(text: str, min_chars: int = 150) -> bool:
    """
    Palauttaa True jos teksti vaikuttaa oikealta hoitosuositustekstiltä.
    Hylkää navigaatio-, mainos- ja roskatekstit.
    """
    t = text.strip()
    if len(t) < min_chars:
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
        f"[{i+1}] {doc.page_content[:300]}..."
        for i, doc in enumerate(docs)
    )
    prompt = (
        "You are selecting the best health guideline excerpt for a patient.\n"
        "Question: " + query + "\n\n"
        "Excerpts from Finnish health guideline PDFs:\n" + snippets + "\n\n"
        "Which excerpt number (1-" + str(len(docs)) + ") contains the most "
        "specific and actionable recommendation or guideline relevant to the "
        "question? Reply with ONLY the number."
    )
    try:
        result = await selector_llm.ainvoke(prompt)
        idx = int(result.content.strip()) - 1
        return max(0, min(idx, len(docs) - 1))
    except Exception:
        return 0  # Fallback: ensimmäinen


async def get_guideline_excerpt(query: str, score_threshold: float = 0.65) -> dict | None:
    """
    Hakee relevanteimman Chroma-chunkin kyselyn perusteella.
    Palauttaa {"text": str, "source": str} tai None.
    Hakee k=10 kandidaattia, suodattaa laaturoskan, ja pyytää LLM:ltä
    parhaan indeksin. Palautettu teksti on muuttumaton PDF-chunk.
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

        # LLM valitsee parhaan indeksin — teksti pysyy muuttumattomana
        best_idx = await _select_best_chunk(query, quality_docs)
        best_doc = quality_docs[best_idx]
        text = _clean_chunk_text(best_doc.page_content)

        return {
            "text": _trim_to_sentence(text, max_chars=500),
            "source": best_doc.metadata.get("source", "käypähoito.fi")
        }

    except Exception as e:
        print(f"get_guideline_excerpt error: {e}")
        return None

# -----------------------------
# 5) Julkaistava funktio, jolla saa RAG-vastauksen
# -----------------------------
async def get_rag_response(user_input: str, save_to_memory: bool = True) -> str:
    """
    Kysyy RAG-ketjulta (Chroma+GEMINI) ja palauttaa vastauksen tekstinä. 
    Draft_response-ominaisuus: save_to_memory=False hakee vastauksen ilman, 
    että keskustelumuistiin tallennetaan uusia viestejä.
    """
    if save_to_memory:
        memory.add_user_message(user_input)

    # Hae dokumentit threshold + fallback -logiikalla
    relevant_docs = await retrieve_with_fallback(user_input, vectorstore)

    if not relevant_docs:
        no_info_msg = (
            "Valitettavasti minulla ei ole riittävästi tietoa kysymääsi aiheeseen. "
            "Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon."
        )
        if save_to_memory:
            memory.add_ai_message(no_info_msg)
        return no_info_msg

    # Vastauksen generointi (asynkronisesti)
    response = await rag_chain.ainvoke({
        "context": relevant_docs,
        "chat_history": memory.messages if save_to_memory else [],
        "input": user_input
    })

    if save_to_memory:
        memory.add_ai_message(response.content)
        print(f"Chat memory: {memory.messages}")

    return response.content

async def translate_excerpt(text: str) -> str:
    """
    Kääntää suomenkielisen hoitosuositusotteen englanniksi.
    Palauttaa alkuperäisen tekstin virhetilanteessa.
    """
    prompt = (
        "Translate the following Finnish health guideline excerpt to English. "
        "Translate faithfully — do not add, remove, or interpret any medical content. "
        "Return only the translated text, nothing else.\n\n"
        + text
    )
    try:
        result = await llm.ainvoke(prompt)
        return result.content.strip()
    except Exception:
        return text  # Fallback: alkuperäinen suomenkielinen teksti


async def generate_draft_response(user_input: str) -> str:
    """Generoi RAG-luonnosvastauksen ilman muistiin tallennusta."""
    return await get_rag_response(user_input, save_to_memory=False)


def clear_conversation_memory():
    # Tyhjentää keskustelumuistin
    memory.clear()
