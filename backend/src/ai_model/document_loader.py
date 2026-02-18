import io
from typing import List
from google.cloud import storage
from PyPDF2 import PdfReader

def download_pdfs_from_bucket(bucket_name: str) -> List[str]:
    """
    Lataa kaikki PDF-tiedostot GCS-bucketista ja palauttaa niiden tekstin listana (yksi elementti per PDF).
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    all_texts: List[str] = []

    for blob in blobs:
        if blob.name.endswith(".pdf"):
            print(f"Ladataan {blob.name} bucketista {bucket_name}...")
            pdf_stream = io.BytesIO()
            blob.download_to_file(pdf_stream)
            pdf_stream.seek(0)
            print(f"Tiedosto {blob.name} ladattu muistiin.")

            reader = PdfReader(pdf_stream)

            # Kerätään PDF:n sivutekstit listaan
            page_texts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:  # vain ei-tyhjät sivut
                    page_texts.append(text)

            # Yhdistetään kaikki sivutekstit yhdeksi stringiksi
            full_text = "\n".join(page_texts)

            all_texts.append(full_text)

    print(f"Ladattu {len(all_texts)} PDF-tiedostoa bucketista {bucket_name}.")
    return all_texts
