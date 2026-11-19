import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from telemetry import tracer


BASE_DIR = os.path.dirname(__file__)

load_dotenv(os.path.join(BASE_DIR, ".env"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# Caminho para o RAG
RAG_SCRIPTS_DIR = os.path.expanduser(
    "~/ai-agent-lab/rag/scripts"
)

sys.path.append(RAG_SCRIPTS_DIR)


from rag_agent import ask_rag
from agent import ask_agent, record_llm_usage


def route_question(question):

    with tracer.start_as_current_span(
        "route_question"
    ) as span:

        span.set_attribute(
            "agent.question",
            question
        )

        span.set_attribute(
            "agent.component",
            "ROUTER"
        )

        span.set_attribute(
            "agent.operation",
            "route_question"
        )

        system_prompt = """
Você é o roteador de um AI Agent especializado em
consultas a dados estruturados e conhecimento técnico.

Existem duas ferramentas disponíveis:

RAG:
Use quando a pergunta solicitar explicações,
conceitos, definições, funcionamento, arquitetura,
características técnicas ou informações existentes
nos documentos.

O conteúdo técnico inclui:
- SNMP
- NETCONF
- YANG
- RESTCONF

Exemplos de perguntas RAG:
- O que é SNMP?
- Como funciona o NETCONF?
- Qual é a função do YANG?
- Como funciona o método PATCH no RESTCONF?
- Qual a diferença entre SNMPv2c e SNMPv3?
- Como NETCONF utiliza modelos YANG?

NL2SQL:
Use quando a pergunta solicitar consultas
aos dados estruturados do PostgreSQL, incluindo
listagens, filtros, contagens, agrupamentos,
ordenações, comparações e cálculos.

Os dados estruturados incluem:
- Clientes
- Pedidos
- Produtos
- Valores
- Quantidades
- Status
- Tecnologias de redes
- SNMP
- NETCONF
- YANG
- RESTCONF

Exemplos de perguntas NL2SQL:
- Quantos clientes existem?
- Quais clientes fizeram mais pedidos?
- Qual foi o valor total dos pedidos?
- Quais tecnologias estão cadastradas?
- Quantas tecnologias temos cadastradas?
- Quais tecnologias utilizam TCP?
- Quais tecnologias utilizam YANG?
- Quais tecnologias possuem portas padrão?
- Compare as tecnologias por categoria.

REGRAS DE ROTEAMENTO:

1. Perguntas conceituais, explicativas e técnicas
devem utilizar RAG.

2. Perguntas sobre registros existentes no PostgreSQL,
consultas, filtros, contagens e comparações devem
utilizar NL2SQL.

3. Não escolha RAG apenas porque a pergunta
menciona uma tecnologia de rede.

4. Considere a intenção da pergunta para escolher
a ferramenta adequada.

5. Escolha somente uma ferramenta.

Responda exclusivamente com:
RAG
ou
NL2SQL
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions=system_prompt,
            input=question
        )

        # Registra tokens e custo do Router
        route_cost = record_llm_usage(
            span,
            response
        )

        route = response.output_text.strip().upper()

        if route not in ("RAG", "NL2SQL"):

            span.set_attribute(
                "agent.route",
                "ERROR"
            )

            raise ValueError(
                f"Rota inválida retornada pelo modelo: {route}"
            )

        span.set_attribute(
            "agent.route",
            route
        )

        return {
            "route": route,
            "cost_usd": route_cost,
        }


def ask_hybrid_agent(question):

    with tracer.start_as_current_span(
        "ask_hybrid_agent"
    ) as span:

        span.set_attribute(
            "agent.question",
            question
        )

        span.set_attribute(
            "agent.component",
            "HYBRID_AGENT"
        )

        # ----------------------------------------------------
        # 1. ROUTER
        # ----------------------------------------------------

        route_result = route_question(
            question
        )

        route = route_result["route"]

        route_cost = route_result["cost_usd"]

        span.set_attribute(
            "agent.route",
            route
        )

        span.set_attribute(
            "agent.router_cost_usd",
            route_cost
        )

        # ----------------------------------------------------
        # 2. RAG
        # ----------------------------------------------------

        if route == "RAG":

            result = ask_rag(
                question
            )

            rag_cost = result.get(
                "cost_usd",
                0
            )

            total_cost = (
                route_cost
                + rag_cost
            )

            span.set_attribute(
                "agent.rag_cost_usd",
                rag_cost
            )

            span.set_attribute(
                "agent.cost_usd",
                total_cost
            )

            return {
                "route": "RAG",
                "question": question,
                "answer": result["answer"],
                "results": result["results"],
                "cost_usd": total_cost,
                "router_cost_usd": route_cost,
                "rag_cost_usd": rag_cost,
            }

        # ----------------------------------------------------
        # 3. NL2SQL
        # ----------------------------------------------------

        result = ask_agent(
            question
        )

        nl2sql_cost = result.get(
            "cost_usd",
            0
        )

        total_cost = (
            route_cost
            + nl2sql_cost
        )

        span.set_attribute(
            "agent.nl2sql_cost_usd",
            nl2sql_cost
        )

        span.set_attribute(
            "agent.cost_usd",
            total_cost
        )

        return {
            "route": "NL2SQL",
            "question": question,
            "answer": result["answer"],
            "sql": result["sql"],
            "columns": result["columns"],
            "rows": result["rows"],
            "cost_usd": total_cost,
            "router_cost_usd": route_cost,
            "nl2sql_cost_usd": nl2sql_cost,
        }


def main():

    question = input(
        "Pergunta: "
    )

    result = ask_hybrid_agent(
        question
    )

    print(
        "\nRota escolhida:"
    )

    print(
        result["route"]
    )

    print(
        "\nResposta:"
    )

    print(
        result["answer"]
    )

    print(
        "\nCusto:"
    )

    print(
        f"US$ {result['cost_usd']:.8f}"
    )

    if result["route"] == "RAG":

        print(
            "\nChunks recuperados:"
        )

        for chunk in result["results"]:

            print(
                "-" * 80
            )

            print(
                f"Chunk: {chunk[2]}"
            )

            print(
                f"Similaridade: {chunk[4]:.4f}"
            )

            print(
                f"Conteúdo: {chunk[3]}"
            )

    else:

        print(
            "\nSQL gerado:"
        )

        print(
            result["sql"]
        )

        print(
            "\nDados retornados:"
        )

        for row in result["rows"]:

            print(
                row
            )


if __name__ == "__main__":
    main()