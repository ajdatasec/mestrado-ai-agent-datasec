import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI


# Caminho do projeto AI Agent
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminho da pasta agent
AGENT_DIR = Path.home() / "ai-agent-lab" / "agent"

if str(AGENT_DIR) not in sys.path:
    sys.path.append(str(AGENT_DIR))


from telemetry import tracer
from agent import record_llm_usage


load_dotenv(BASE_DIR / ".env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# PREÇO DO EMBEDDING
# ============================================================

EMBEDDING_INPUT_PRICE = 0.02


# ============================================================
# CUSTO DO EMBEDDING
# ============================================================

def record_embedding_usage(span, response):
    """
    Registra tokens e custo do text-embedding-3-small.
    """

    usage = getattr(
        response,
        "usage",
        None
    )

    if usage is None:

        input_tokens = 0
        total_tokens = 0

    else:

        input_tokens = (
            getattr(
                usage,
                "prompt_tokens",
                0
            )
            or 0
        )

        total_tokens = (
            getattr(
                usage,
                "total_tokens",
                0
            )
            or input_tokens
        )

    cost_usd = (
        input_tokens
        / 1_000_000
        * EMBEDDING_INPUT_PRICE
    )

    span.set_attribute(
        "llm.model",
        "text-embedding-3-small"
    )

    span.set_attribute(
        "llm.input_tokens",
        input_tokens
    )

    span.set_attribute(
        "llm.total_tokens",
        total_tokens
    )

    span.set_attribute(
        "llm.cost_usd",
        cost_usd
    )

    return cost_usd


# ============================================================
# GERAÇÃO DO EMBEDDING
# ============================================================

def generate_embedding(text):

    with tracer.start_as_current_span(
        "generate_embedding"
    ) as span:

        span.set_attribute(
            "agent.component",
            "RAG"
        )

        span.set_attribute(
            "agent.operation",
            "generate_embedding"
        )

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        embedding_cost = record_embedding_usage(
            span,
            response
        )

        embedding = response.data[0].embedding

        span.set_attribute(
            "embedding.dimension",
            len(embedding)
        )

        return {
            "embedding": embedding,
            "cost_usd": embedding_cost,
        }


# ============================================================
# BUSCA VETORIAL
# ============================================================

def search_similar_documents(
    question,
    limit=3
):

    with tracer.start_as_current_span(
        "vector_search"
    ) as span:

        span.set_attribute(
            "agent.component",
            "RAG"
        )

        span.set_attribute(
            "agent.operation",
            "vector_search"
        )

        span.set_attribute(
            "vector.limit",
            limit
        )

        span.set_attribute(
            "db.system",
            "postgresql"
        )

        embedding_result = generate_embedding(
            question
        )

        query_embedding = embedding_result[
            "embedding"
        ]

        embedding_cost = embedding_result[
            "cost_usd"
        ]

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

            span.set_attribute(
                "db.rows_returned",
                len(results)
            )

            if results:

                span.set_attribute(
                    "rag.top_similarity",
                    float(results[0][4])
                )

            return {
                "results": results,
                "embedding_cost_usd": embedding_cost,
            }

        finally:

            conn.close()


# ============================================================
# GERAÇÃO DA RESPOSTA
# ============================================================

def generate_answer(
    question,
    context
):

    with tracer.start_as_current_span(
        "generate_answer"
    ) as span:

        span.set_attribute(
            "agent.component",
            "RAG"
        )

        span.set_attribute(
            "agent.operation",
            "generate_answer"
        )

        span.set_attribute(
            "agent.question",
            question
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

        answer_cost = record_llm_usage(
            span,
            response
        )

        answer = response.output_text.strip()

        span.set_attribute(
            "rag.context_chunks",
            context.count("\n\n") + 1
            if context
            else 0
        )

        return {
            "answer": answer,
            "cost_usd": answer_cost,
        }


# ============================================================
# RAG COMPLETO
# ============================================================

def ask_rag(question):

    with tracer.start_as_current_span(
        "ask_rag"
    ) as span:

        span.set_attribute(
            "agent.question",
            question
        )

        span.set_attribute(
            "agent.component",
            "RAG"
        )

        # ----------------------------------------------------
        # 1. Busca vetorial + embedding
        # ----------------------------------------------------

        search_result = search_similar_documents(
            question
        )

        results = search_result[
            "results"
        ]

        embedding_cost = search_result[
            "embedding_cost_usd"
        ]

        # ----------------------------------------------------
        # 2. Montar contexto
        # ----------------------------------------------------

        context = "\n\n".join(
            result[3]
            for result in results
        )

        # ----------------------------------------------------
        # 3. Gerar resposta
        # ----------------------------------------------------

        answer_result = generate_answer(
            question,
            context
        )

        answer = answer_result[
            "answer"
        ]

        answer_cost = answer_result[
            "cost_usd"
        ]

        # ----------------------------------------------------
        # 4. Custo total do RAG
        # ----------------------------------------------------

        total_cost = (
            embedding_cost
            + answer_cost
        )

        span.set_attribute(
            "rag.results_returned",
            len(results)
        )

        span.set_attribute(
            "agent.embedding_cost_usd",
            embedding_cost
        )

        span.set_attribute(
            "agent.answer_cost_usd",
            answer_cost
        )

        span.set_attribute(
            "agent.cost_usd",
            total_cost
        )

        return {
            "question": question,
            "answer": answer,
            "results": results,
            "cost_usd": total_cost,
            "embedding_cost_usd": embedding_cost,
            "answer_cost_usd": answer_cost,
        }