import io
from typing import List
from google.cloud import storage
from PyPDF2 import PdfReader
from langchain_core.documents import Document

def download_pdfs_from_bucket(bucket_name: str) -> List[Document]:
    """
    Lataa kaikki PDF-tiedostot GCS-bucketista ja palauttaa niiden dokumentit listana (yksi elementti per PDF).
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    documents: List[Document] = []

    for blob in blobs:
        if not blob.name.endswith(".pdf"):
            continue

        print(f"Ladataan {blob.name} bucketista {bucket_name}...")
        pdf_stream = io.BytesIO()
        blob.download_to_file(pdf_stream)
        pdf_stream.seek(0)

        reader = PdfReader(pdf_stream)

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": blob.name,
                        "page": page_number,
                        "bucket": bucket_name,
                    },
                )
            )

    print(f"Ladattu {len(documents)} sivudokumenttia bucketista {bucket_name}.")
    return documents
