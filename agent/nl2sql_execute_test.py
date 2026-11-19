import os

import psycopg
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# =========================
# OpenAI
# =========================

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# =========================
# Schema PostgreSQL
# =========================

SCHEMA = """
Tabela: clientes
Colunas:
- cliente_id: identificador único do cliente
- nome: nome do cliente
- email: e-mail do cliente
- pais: país do cliente
- regiao: região do cliente
- data_cadastro: data de cadastro

Tabela: pedidos
Colunas:
- pedido_id: identificador único do pedido
- cliente_id: identifica o cliente
- data_pedido: data do pedido
- produto: produto comprado
- categoria: categoria do produto
- quantidade: quantidade comprada
- valor_unitario: valor unitário do produto
- status: status do pedido

Relacionamento:
pedidos.cliente_id = clientes.cliente_id
"""

# =========================
# Pergunta
# =========================

question = "Quais clientes fizeram mais pedidos?"

# =========================
# Prompt NL2SQL
# =========================

SYSTEM_PROMPT = f"""
Você é um agente NL2SQL especializado em PostgreSQL.

Transforme perguntas em linguagem natural
em consultas SQL válidas para PostgreSQL.

Use somente as tabelas e colunas existentes
no schema abaixo.

{SCHEMA}

Regras:
- Retorne somente o SQL.
- Não coloque markdown.
- Não explique o SQL.
- Não invente tabelas ou colunas.
- Use JOIN quando necessário.
"""

# =========================
# 1. Gerar SQL
# =========================

response = client.responses.create(
    model="gpt-5.6-luna",
    instructions=SYSTEM_PROMPT,
    input=question
)

sql = response.output_text.strip()

# Remove Markdown caso o modelo coloque ```sql
if sql.startswith("```sql"):
    sql = sql[6:]

if sql.startswith("```"):
    sql = sql[3:]

if sql.endswith("```"):
    sql = sql[:-3]

sql = sql.strip()

# =========================
# 2. Conectar PostgreSQL
# =========================

conn = psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

# =========================
# 3. Executar SQL
# =========================

with conn.cursor() as cur:

    cur.execute(sql)

    rows = cur.fetchall()

    columns = [desc.name for desc in cur.description]

conn.close()

# =========================
# 4. Preparar resultado
# =========================

result_text = "\n".join(
    str(dict(zip(columns, row)))
    for row in rows
)

# =========================
# 5. LLM interpreta resultado
# =========================

answer_prompt = f"""
O usuário fez a seguinte pergunta:

{question}

O banco de dados retornou:

{result_text}

Responda à pergunta do usuário usando somente
os dados retornados pelo banco.

Não invente informações.

Responda em português, de forma clara e objetiva.
"""

answer_response = client.responses.create(
    model="gpt-5.6-luna",
    input=answer_prompt
)

answer = answer_response.output_text.strip()

# =========================
# 6. Mostrar tudo
# =========================

print("\n==============================")
print("PERGUNTA")
print("==============================")
print(question)

print("\n==============================")
print("SQL GERADO")
print("==============================")
print(sql)

print("\n==============================")
print("RESULTADO DO BANCO")
print("==============================")

print(" | ".join(columns))
print("-" * 60)

for row in rows:
    print(" | ".join(str(value) for value in row))

print("\n==============================")
print("RESPOSTA DO AGENTE")
print("==============================")
print(answer)