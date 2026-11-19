import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCHEMA = """
Tabela: clientes
Colunas:
- cliente_id: identificador único do cliente
- nome: nome do cliente
- email: e-mail
- pais: país do cliente
- regiao: região do cliente
- data_cadastro: data de cadastro

Tabela: pedidos
Colunas:
- pedido_id: identificador único do pedido
- cliente_id: identifica o cliente que fez o pedido
- data_pedido: data do pedido
- produto: produto comprado
- categoria: categoria do produto
- quantidade: quantidade comprada
- valor_unitario: valor unitário do produto
- status: status do pedido

Relacionamento:
pedidos.cliente_id = clientes.cliente_id
"""

SYSTEM_PROMPT = f"""
Você é um agente NL2SQL especializado em PostgreSQL.

Sua função é transformar perguntas em linguagem natural
em consultas SQL válidas para PostgreSQL.

Use somente as tabelas e colunas existentes no schema abaixo.

{SCHEMA}

Regras:
- Retorne somente o SQL.
- Não coloque markdown.
- Não explique o SQL.
- Não invente tabelas ou colunas.
- Use JOIN quando necessário.
"""

question = "Quais clientes fizeram mais pedidos?"

response = client.responses.create(
    model="gpt-5.6-luna",
    instructions=SYSTEM_PROMPT,
    input=question
)

sql = response.output_text.strip()

print("\nPergunta:")
print(question)

print("\nSQL gerado:")
print(sql)