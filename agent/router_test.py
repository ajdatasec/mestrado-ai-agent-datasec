import os

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = os.path.dirname(__file__)

load_dotenv(os.path.join(BASE_DIR, ".env"))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def route_question(question):

    system_prompt = """
Você é um roteador de um AI Agent.

O agente possui duas fontes de conhecimento:

RAG:
Use RAG quando a pergunta estiver relacionada
a informações contidas em documentos.

NL2SQL:
Use NL2SQL quando a pergunta estiver relacionada
a dados armazenados no banco PostgreSQL,
como clientes, pedidos, produtos, valores,
quantidades ou status.

Responda SOMENTE com uma destas duas opções:

RAG
NL2SQL
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=system_prompt,
        input=question
    )

    return response.output_text.strip()


questions = [
    "O que acontece quando um funcionário deixa a organização?",
    "Quantos pedidos o Antônio Júnior fez?"
]


for question in questions:

    route = route_question(question)

    print("-" * 60)
    print(f"Pergunta: {question}")
    print(f"Rota escolhida: {route}")
