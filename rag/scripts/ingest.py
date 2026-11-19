
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


# Carrega o .env
BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"

load_dotenv(BASE_DIR / ".env")

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def read_document(document_path):
    with open(document_path, "r", encoding="utf-8") as file:
        return file.read()


def create_chunks(text):
    chunks = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    return chunks


def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def save_chunk(document_name, chunk_index, content, embedding):
    conn = psycopg.connect(
        host=os.getenv("RAG_POSTGRES_HOST"),
        port=os.getenv("RAG_POSTGRES_PORT"),
        dbname=os.getenv("RAG_POSTGRES_DB"),
        user=os.getenv("RAG_POSTGRES_USER"),
        password=os.getenv("RAG_POSTGRES_PASSWORD"),
    )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_chunks
                    (document_name, chunk_index, content, embedding)
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    document_name,
                    chunk_index,
                    content,
                    embedding,
                )
            )

        conn.commit()
    finally:
        conn.close()


def main():
    documents = sorted(DOCUMENTS_DIR.glob("*.txt"))

    if not documents:
        print("Nenhum documento .txt encontrado.")
        return

    print(f"Documentos encontrados: {len(documents)}")

    for document_path in documents:
        print(f"\nProcessando: {document_path.name}")

        text = read_document(document_path)

        print(f"Caracteres encontrados: {len(text)}")

        chunks = create_chunks(text)

        print(f"Chunks criados: {len(chunks)}")

        for index, chunk in enumerate(chunks):
            print(f"Gerando embedding do chunk {index}...")

            embedding = generate_embedding(chunk)

            save_chunk(
                document_path.name,
                index,
                chunk,
                embedding
            )

            print(f"Chunk {index} salvo.")

    print("\nIngestão concluída.")


if __name__ == "__main__":
    main()
