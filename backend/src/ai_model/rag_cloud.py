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

def _strip_broken_prefix(text: str, min_broken_run: int = 4) -> str:
    """
    Poistaa tekstin alusta PyPDF2:n kirjainryhmiä jotka on eroteltu välilyönnillä
    ('Ko hon neen ve ren'). Tunnistaa jakson jossa min_broken_run+ peräkkäistä
    sanaa on kaikki ≤4 kirjainta ja koostuvat pelkistä kirjaimista.
    Palauttaa tyhjän merkkijonon jos jäljelle ei jää tarpeeksi tekstiä.
    """
    words = text.split()
    i = 0
    while i < len(words) and words[i].isalpha() and len(words[i]) <= 4:
        i += 1
    if i >= min_broken_run:
        remaining = " ".join(words[i:])
        return remaining if len(remaining) >= 100 else ""
    return text

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

_RECOMMENDATION_KEYWORDS = [
    "suositell", "tulisi", "on tärkeää", "hoitosuositus",
    "hoidossa käytetään", "ensisijaisesti", "elintapa", "ohje",
    "voidaan hoitaa", "on suositeltavaa",
]

def _recommendation_score(text: str) -> int:
    """Laskee suositussanaston esiintymismäärän tekstissä."""
    lower = text.lower()
    return sum(1 for kw in _RECOMMENDATION_KEYWORDS if kw in lower)

async def get_guideline_excerpt(query: str, score_threshold: float = 0.65) -> dict | None:
    """
    Hakee relevanteimman Chroma-chunkin kyselyn perusteella
    ILMAN LLM-kutsua. Palauttaa {"text": str, "source": str} tai None.
    Ei fallbackia – None tarkoittaa "ei osuvaa excerptia".
    Käy läpi k=5 kandidaattia järjestettynä suositussanaston mukaan.
    """
    try:
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 5, "score_threshold": score_threshold}
        )
        docs = await retriever.ainvoke(query)
        if not docs:
            return None
        docs_sorted = sorted(docs, key=lambda d: _recommendation_score(d.page_content), reverse=True)
        for doc in docs_sorted:
            text = _strip_broken_prefix(doc.page_content)
            if text and _is_quality_excerpt(text):
                return {
                    "text": _trim_to_sentence(text, max_chars=500),
                    "source": doc.metadata.get("source", "käypähoito.fi")
                }
        return None
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

async def generate_draft_response(user_input: str) -> str:
    """Generoi RAG-luonnosvastauksen ilman muistiin tallennusta."""
    return await get_rag_response(user_input, save_to_memory=False)


def clear_conversation_memory():
    # Tyhjentää keskustelumuistin
    memory.clear()
