from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .document_loader import download_pdfs_from_bucket
import os

def initialize_vectorstore(embeddings, persist_directory, bucket_name):
    if os.path.exists(persist_directory + "/chroma.sqlite3"):
        print("Käytetään aiemmin prosessoitua dataa...")
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
    else:
        print("Ladataan ja prosessoidaan kaikki PDF-tiedostot bucketista...")

        page_docs = download_pdfs_from_bucket(bucket_name)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""],
        )

        docs = text_splitter.split_documents(page_docs)

        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=persist_directory
        )

    return vectorstore