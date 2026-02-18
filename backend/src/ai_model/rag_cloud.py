# Jos importit eivät toimi, vaihda interpreteriksi Python 3.10.6 64-bit
from google.cloud import storage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain_chroma import Chroma
from PyPDF2 import PdfReader
import os
import io
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.memory import ConversationBufferMemory

# Google API-key
load_dotenv() # Load .env file
google_api_key = os.getenv('GEMINI_API')

# Google Cloud Storage asetukset
bucket_name = "training_data-1" 

# ChromaDB:n tallennuskansio
persist_directory = "/app/chroma"

# -----------------------------
# 1) Ladataan PDF:t (tarvittaessa), alustetaan Chroma
# -----------------------------

if os.path.exists(persist_directory + "/chroma.sqlite3"):
    print("Käytetään aiemmin prosessoitua dataa...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=google_api_key
    )
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
else:
    # Ladataan PDF:t GCS:stä
    print("Ladataan ja prosessoidaan kaikki PDF-tiedostot bucketista...")

    def download_pdfs_from_bucket(bucket_name):
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs()

        all_texts = []
        for blob in blobs:
            if blob.name.endswith(".pdf"):
                print(f"Ladataan {blob.name} bucketista {bucket_name}...")
                pdf_stream = io.BytesIO()
                blob.download_to_file(pdf_stream)
                pdf_stream.seek(0)
                print(f"Tiedosto {blob.name} ladattu muistiin.")

                reader = PdfReader(pdf_stream)
                text = "\n".join(
                    [page.extract_text() for page in reader.pages if page.extract_text()]
                )
                all_texts.append(text)
        return all_texts

    all_texts = download_pdfs_from_bucket(bucket_name)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300,
        separators=["\n\n", "\n", " ", ""],
    )
    docs = text_splitter.create_documents(all_texts)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=google_api_key
    )
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )

# -----------------------------
# 2) Luodaan RAG-ketju (retriever + LLM + prompt)
# -----------------------------
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold", # Vain dokumentit, jotka ovat riittävän lähellä käyttäjän kysymystä, otetaan mukaan.
    search_kwargs={"k": 6, "score_threshold": 0.6} # Kysytään 6 eniten samankaltaista dokumenttia, joista vain ne, joiden samankaltaisuus on yli 0.6, otetaan mukaan.
)

llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-001', # Gemini 2.0 Flash
    temperature=0.3, # Alustava lämpötila
    max_tokens=1000,    # nostettu 500 -> 1000
    top_p=0.9,
    google_api_key=google_api_key
)

# Alustetaan keskustelumuisti
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

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

question_answer_chain = create_stuff_documents_chain(llm, prompt)
#rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# -----------------------------
# 3) Julkaistava funktio, jolla saa RAG-vastauksen
# -----------------------------
async def get_rag_response(user_input: str) -> str:
    """ Kysyy RAG-ketjulta (Chroma+GEMINI) ja palauttaa vastauksen tekstinä. """
    memory.chat_memory.add_user_message(user_input)

    # Ensihaku (asynkroninen invoke)
    relevant_docs = await retriever.ainvoke(user_input)

    # Fallback tarvittaessa
    if not relevant_docs:
        print("⚠️ Ei tarpeeksi relevantteja osumia threshold-hausta – otetaan käyttöön fallback MMR...")
        fallback_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5}#, "fetch_k": 20, "lambda_mult": 0.5}
        )
        relevant_docs = await fallback_retriever.ainvoke(user_input)

        if not relevant_docs:
            no_info_msg = (
                "Valitettavasti minulla ei ole riittävästi tietoa kysymääsi aiheeseen. "
                "Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon."
            )
            memory.chat_memory.add_ai_message(no_info_msg)
            return no_info_msg

    # Vastauksen generointi (asynkronisesti)
    response = await question_answer_chain.ainvoke({
        "input": user_input,
        "context": relevant_docs,
        "chat_history": memory.buffer
    })

    memory.chat_memory.add_ai_message(response)
    return response


async def generate_draft_response(user_input: str) -> str:
    """Generoi RAG-luonnosvastauksen ilman muistiin tallennusta."""
    relevant_docs = await retriever.ainvoke(user_input)

    if not relevant_docs:
        fallback_retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5}
        )
        relevant_docs = await fallback_retriever.ainvoke(user_input)

        if not relevant_docs:
            return (
                "Valitettavasti minulla ei ole riittävästi tietoa kysymääsi aiheeseen. "
                "Suosittelen ottamaan yhteyttä asiantuntijaan tai hoitavaan tahoon."
            )

    response = await question_answer_chain.ainvoke({
        "input": user_input,
        "context": relevant_docs,
        "chat_history": []
    })

    return response


def clear_conversation_memory():
    """ Tyhjentää keskustelumuistin """
    memory.clear()
