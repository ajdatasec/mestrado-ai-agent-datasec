import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


# Diretório principal do RAG
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega as variáveis do .env
load_dotenv(BASE_DIR / ".env")

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def search_similar_documents(question, limit=3):

    # Gera o embedding da pergunta
    query_embedding = generate_embedding(question)

    conn = psycopg.connect(
        host=os.getenv("RAG_POSTGRES_HOST"),
        port=os.getenv("RAG_POSTGRES_PORT"),
        dbname=os.getenv("RAG_POSTGRES_DB"),
        user=os.getenv("RAG_POSTGRES_USER"),
        password=os.getenv("RAG_POSTGRES_PASSWORD"),
    )

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT
                id,
                document_name,
                chunk_index,
                content,
                1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (
                query_embedding,
                query_embedding,
                limit,
            )
        )

        results = cur.fetchall()

    conn.close()

    return results


def main():

    question = input("Pergunta: ")

    results = search_similar_documents(question)

    print("\nResultados encontrados:\n")

    for result in results:

        document_id = result[0]
        document_name = result[1]
        chunk_index = result[2]
        content = result[3]
        similarity = result[4]

        print(f"ID: {document_id}")
        print(f"Documento: {document_name}")
        print(f"Chunk: {chunk_index}")
        print(f"Similaridade: {similarity:.4f}")
        print(f"Conteúdo: {content}")
        print("-" * 80)


if __name__ == "__main__":
    main()
