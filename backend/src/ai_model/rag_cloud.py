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

vectorstore = initialize_vectorstore(
    embeddings,
    settings.PERSIST_DIRECTORY,
    settings.BUCKET_NAME
)

# -----------------------------
# 2) RAG chain
# -----------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-001",
    temperature=0.3,
    max_tokens=1000,
    top_p=0.9,
    google_api_key=settings.GOOGLE_API_KEY
)

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

    "\n\nContext:\n{context}\n\n"
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


async def retrieve_with_fallback(
    user_input: str,
    vectorstore,
    top_k: int = 6,
    score_threshold: float = 0.6,
    fallback_k: int = 5
):
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": top_k, "score_threshold": score_threshold}
    )

    relevant_docs = await retriever.ainvoke(user_input)

    if not relevant_docs:
        print("⚠️ Ei tarpeeksi relevantteja osumia threshold-hausta – fallback MMR...")
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


async def get_rag_response(user_input: str, save_to_memory: bool = True) -> dict:
    """
    Palauttaa sekä vastauksen että lähteet.
    """
    if save_to_memory:
        memory.add_user_message(user_input)

    relevant_docs = await retrieve_with_fallback(user_input, vectorstore)

    if not relevant_docs:
        no_info_msg = (
            "Valitettavasti minulla ei ole riittävästi tietoa kysymääsi aiheeseen. "
            "Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon."
        )
        if save_to_memory:
            memory.add_ai_message(no_info_msg)

        return {
            "answer": no_info_msg,
            "sources": []
        }

    context_text, sources = _build_context_and_sources(relevant_docs)

    response = await rag_chain.ainvoke({
        "context": context_text,
        "chat_history": memory.messages if save_to_memory else [],
        "input": user_input
    })

    if save_to_memory:
        memory.add_ai_message(response.content)
        print(f"Chat memory: {memory.messages}")

    return {
        "answer": response.content,
        "sources": sources
    }


async def generate_draft_response(user_input: str) -> str:
    result = await get_rag_response(user_input, save_to_memory=False)
    return result["answer"]


def clear_conversation_memory():
    memory.clear()