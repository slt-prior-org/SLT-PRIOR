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
# 4) Julkaistava funktio, jolla saa RAG-vastauksen
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
