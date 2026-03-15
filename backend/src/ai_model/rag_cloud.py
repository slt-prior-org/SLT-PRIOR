from config import settings
from .vectorstore import initialize_vectorstore

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
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
    model='gemini-2.0-flash-001',  # Gemini 2.0 Flash
    temperature=0.3,  # Alustava lämpötila
    max_tokens=1000,  # nostettu 500 -> 1000
    top_p=0.9,
    google_api_key=settings.GOOGLE_API_KEY
)

# Alustetaan vanha keskustelumuisti yhteensopivuutta varten
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


# -----------------------------
# 4) Julkaistava funktio, jolla saa RAG-vastauksen
# -----------------------------
async def get_rag_response(
    user_input: str,
    save_to_memory: bool = True,
    chat_history: list[dict] | None = None,
) -> str:
    """
    Kysyy RAG-ketjulta (Chroma+GEMINI) ja palauttaa vastauksen tekstinä.
    Draft_response-ominaisuus: save_to_memory=False hakee vastauksen ilman,
    että keskustelumuistiin tallennetaan uusia viestejä.
    """
    use_explicit_history = chat_history is not None
    history_messages = _normalize_chat_history(chat_history) if use_explicit_history else None

    if save_to_memory and not use_explicit_history:
        memory.add_user_message(user_input)

    # Hae dokumentit threshold + fallback -logiikalla
    relevant_docs = await retrieve_with_fallback(user_input, vectorstore)

    if not relevant_docs:
        # Jos uusi chat-kohtainen historia on annettu ja sitä löytyy,
        # annetaan mallin vastata historian perusteella myös ilman haettuja dokumentteja.
        if use_explicit_history and history_messages:
            relevant_docs = []
        else:
            no_info_msg = (
                "Valitettavasti minulla ei ole riittävästi tietoa kysymääsi aiheeseen. "
                "Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon."
            )
            if save_to_memory and not use_explicit_history:
                memory.add_ai_message(no_info_msg)
            return no_info_msg

    if not use_explicit_history:
        history_messages = memory.messages if save_to_memory else []

    # Vastauksen generointi
    response = await rag_chain.ainvoke({
        "context": relevant_docs,
        "chat_history": history_messages,
        "input": user_input
    })

    if save_to_memory and not use_explicit_history:
        memory.add_ai_message(response.content)
        print(f"Chat memory: {memory.messages}")

    return response.content


async def generate_draft_response(user_input: str, chat_history: list[dict] | None = None) -> str:
    """Generoi RAG-luonnosvastauksen ilman muistiin tallennusta."""
    return await get_rag_response(
        user_input,
        save_to_memory=False,
        chat_history=chat_history
    )


def clear_conversation_memory():
    # Tyhjentää vanhan keskustelumuistin
    memory.clear()
