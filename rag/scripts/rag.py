import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def search_similar_documents(question, limit=3):

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


def generate_answer(question, results):

    context = "\n\n".join(
        result[3]
        for result in results
    )

    prompt = f"""
Você é um assistente que responde perguntas
usando exclusivamente o contexto fornecido.

Contexto:

{context}

Pergunta:

{question}

Regras:

- Responda somente com informações presentes no contexto.
- Não invente informações.
- Se o contexto não possuir informação suficiente,
  diga que a informação não foi encontrada nos documentos.
- Responda em português.
- Seja claro e objetivo.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    return response.output_text.strip()


def main():

    question = input("Pergunta: ")

    results = search_similar_documents(question)

    print("\nContexto recuperado:\n")

    for result in results:

        print(f"Chunk: {result[2]}")
        print(f"Similaridade: {result[4]:.4f}")
        print(f"Conteúdo: {result[3]}")
        print("-" * 80)

    answer = generate_answer(
        question,
        results
    )

    print("\nResposta do RAG:\n")
    print(answer)


if __name__ == "__main__":
    main()
