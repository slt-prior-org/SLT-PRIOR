from config import settings
from .vectorstore import initialize_vectorstore

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

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
    model='gemini-2.0-flash-001',  # Gemini 2.0 Flash
    temperature=0.3,              # Alustava lämpötila
    max_tokens=1000,              # nostettu 500 -> 1000
    top_p=0.9,
    google_api_key=settings.GOOGLE_API_KEY
)

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context and chat history to answer the question. "
    "Always check both the retrieved context and the provided chat history before deciding that you do not have enough information. "
    "If the answer is present in the chat history, answer based on it. "
    "You do have access to the provided chat history and must not claim otherwise. "
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

def mongo_docs_to_lc_messages(docs: list[dict]) -> list[BaseMessage]:
    """
    Muuntaa MongoDB:stä haetut chat-viestit LangChainin viestiolioiksi.
    Odottaa docs-listan olevan aikajärjestyksessä (vanhin -> uusin).

    HUOM: yhteensopivuus T:n kanssa:
      sender: "user" | "bot" | "professional" | (mahd. "system")
    """
    messages: list[BaseMessage] = []
    for d in docs:
        sender = d.get("sender")
        content = d.get("content", "")

        if not content:
            continue

        if sender == "user":
            messages.append(HumanMessage(content=content))
        elif sender == "bot":
            messages.append(AIMessage(content=content))
        elif sender == "professional":
            # Ammattilainen käsitellään ihmisenä LLM:lle
            messages.append(HumanMessage(content=content))
        elif sender == "system":
            messages.append(SystemMessage(content=content))

    return messages

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
        search_type="similarity_score_threshold",  # Vain dokumentit, jotka ovat riittävän lähellä käyttäjän kysymystä, otetaan mukaan.
        search_kwargs={"k": top_k, "score_threshold": score_threshold}  # Kysytään 6 eniten samankaltaista dokumenttia, joista vain ne, joiden samankaltaisuus on yli 0.6, otetaan mukaan.
    )

    relevant_docs = await retriever.ainvoke(user_input)

    # Fallback tarvittaessa
    if not relevant_docs:
        print("⚠️ Ei tarpeeksi relevantteja osumia threshold-hausta – otetaan käyttöön fallback MMR...")
        fallback_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": fallback_k}  # , "fetch_k": 20, "lambda_mult": 0.5}
        )
        relevant_docs = await fallback_retriever.ainvoke(user_input)

    return relevant_docs

# -----------------------------
# 4) Julkaistava funktio, jolla saa RAG-vastauksen
# -----------------------------
async def get_rag_response(user_input: str, chat_history_docs: list[dict]) -> str:
    """
    Kysyy RAG-ketjulta (Chroma+GEMINI) ja palauttaa vastauksen tekstinä.
    Chat history tulee ulkoa (MongoDB), ei globaalista muistista.
    """
    chat_history = mongo_docs_to_lc_messages(chat_history_docs)

    # Hae dokumentit threshold + fallback -logiikalla
    relevant_docs = await retrieve_with_fallback(user_input, vectorstore)

    context_str = ""
    if relevant_docs:
        context_str = "\n\n---\n\n".join([d.page_content for d in relevant_docs])

    response = await rag_chain.ainvoke({
        "context": context_str,
        "chat_history": chat_history,
        "input": user_input
    })

    return response.content