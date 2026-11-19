import os

import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from telemetry import tracer


ENV_FILE = os.path.join(
    os.path.dirname(__file__),
    ".env"
)

load_dotenv(ENV_FILE)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


# ============================================================
# PREÇOS OPENAI
# Valores em USD por 1 milhão de tokens
# ============================================================

GPT_INPUT_PRICE = 0.20
GPT_CACHED_INPUT_PRICE = 0.02
GPT_OUTPUT_PRICE = 1.20


# ============================================================
# SCHEMA DO BANCO
# ============================================================

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

Tabela: tecnologias_rede
Colunas:
- tecnologia_id: identificador único da tecnologia
- nome: nome da tecnologia (SNMP, NETCONF, YANG ou RESTCONF)
- categoria: categoria da tecnologia
- finalidade: finalidade e objetivo da tecnologia
- transporte: protocolo de transporte utilizado
- portas: portas padrão utilizadas
- formato_dados: formato dos dados
- utiliza_yang: indica se utiliza modelos YANG
- seguranca: mecanismos de segurança
- operacoes: operações suportadas

Regras de seleção:
- Perguntas sobre clientes devem consultar clientes.
- Perguntas sobre pedidos devem consultar pedidos.
- Perguntas sobre tecnologias de redes devem consultar tecnologias_rede.
- Não utilize pedidos para responder perguntas sobre tecnologias.
- Não utilize JOIN quando a consulta envolver somente uma tabela.
"""


# ============================================================
# FUNÇÕES DE CUSTO
# ============================================================

def extract_usage(response):
    """
    Extrai informações de tokens da resposta da Responses API.
    """

    usage = getattr(response, "usage", None)

    if usage is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cached_tokens": 0,
        }

    input_tokens = (
        getattr(usage, "input_tokens", 0)
        or 0
    )

    output_tokens = (
        getattr(usage, "output_tokens", 0)
        or 0
    )

    total_tokens = (
        getattr(usage, "total_tokens", 0)
        or input_tokens + output_tokens
    )

    cached_tokens = 0

    input_details = getattr(
        usage,
        "input_tokens_details",
        None
    )

    if input_details is not None:
        cached_tokens = (
            getattr(
                input_details,
                "cached_tokens",
                0
            )
            or 0
        )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": cached_tokens,
    }


def calculate_llm_cost(
    input_tokens,
    output_tokens,
    cached_tokens=0
):
    """
    Calcula o custo de uma chamada ao GPT em USD.
    """

    non_cached_input_tokens = max(
        input_tokens - cached_tokens,
        0
    )

    input_cost = (
        non_cached_input_tokens
        / 1_000_000
        * GPT_INPUT_PRICE
    )

    cached_input_cost = (
        cached_tokens
        / 1_000_000
        * GPT_CACHED_INPUT_PRICE
    )

    output_cost = (
        output_tokens
        / 1_000_000
        * GPT_OUTPUT_PRICE
    )

    return (
        input_cost
        + cached_input_cost
        + output_cost
    )


def record_llm_usage(span, response):
    """
    Registra tokens e custo no span do OpenTelemetry.

    Retorna o custo da chamada.
    """

    usage = extract_usage(response)

    cost_usd = calculate_llm_cost(
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        cached_tokens=usage["cached_tokens"],
    )

    span.set_attribute(
        "llm.model",
        "gpt-5.6-luna"
    )

    span.set_attribute(
        "llm.input_tokens",
        usage["input_tokens"]
    )

    span.set_attribute(
        "llm.output_tokens",
        usage["output_tokens"]
    )

    span.set_attribute(
        "llm.total_tokens",
        usage["total_tokens"]
    )

    span.set_attribute(
        "llm.cached_tokens",
        usage["cached_tokens"]
    )

    span.set_attribute(
        "llm.cost_usd",
        cost_usd
    )

    return cost_usd


# ============================================================
# GERAÇÃO DO SQL
# ============================================================

def generate_sql(question):
    """
    Recebe uma pergunta em linguagem natural
    e retorna o SQL gerado pelo LLM.
    """

    with tracer.start_as_current_span(
        "generate_sql"
    ) as span:

        span.set_attribute(
            "agent.question",
            question
        )

        span.set_attribute(
            "agent.component",
            "NL2SQL"
        )

        span.set_attribute(
            "agent.operation",
            "generate_sql"
        )

        system_prompt = f"""
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

- Para perguntas sobre clientes, consulte a tabela clientes.
- Para perguntas sobre pedidos, consulte a tabela pedidos.
- Para perguntas sobre tecnologias de redes, consulte a tabela tecnologias_rede.
- Não utilize pedidos para responder perguntas sobre tecnologias de redes.

- Para pesquisar termos dentro de colunas de texto, utilize ILIKE com curingas (%).
- Não utilize igualdade exata (=) quando o termo pesquisado puder fazer parte de um texto maior.

- Quando perguntarem quais tecnologias utilizam determinado transporte, retorne nome e transporte.
- Quando perguntarem quais tecnologias utilizam TCP, utilize:
  SELECT nome, transporte
  FROM tecnologias_rede
  WHERE transporte ILIKE '%TCP%';
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            instructions=system_prompt,
            input=question
        )

        cost_usd = record_llm_usage(
            span,
            response
        )

        sql = response.output_text.strip()

        if sql.startswith("```sql"):
            sql = sql[6:]

        if sql.startswith("```"):
            sql = sql[3:]

        if sql.endswith("```"):
            sql = sql[:-3]

        sql = sql.strip()

        span.set_attribute(
            "agent.sql",
            sql
        )

        return {
            "sql": sql,
            "cost_usd": cost_usd,
        }


# ============================================================
# EXECUÇÃO DO SQL
# ============================================================

def execute_sql(sql):
    """
    Executa o SQL no PostgreSQL
    usando o usuário configurado no .env.
    """

    with tracer.start_as_current_span(
        "execute_sql"
    ) as span:

        span.set_attribute(
            "agent.component",
            "NL2SQL"
        )

        span.set_attribute(
            "agent.operation",
            "execute_sql"
        )

        span.set_attribute(
            "db.system",
            "postgresql"
        )

        conn = psycopg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

        try:

            with conn.cursor() as cur:

                cur.execute(sql)

                rows = cur.fetchall()

                columns = [
                    desc.name
                    for desc in cur.description
                ]

            span.set_attribute(
                "db.rows_returned",
                len(rows)
            )

            return columns, rows

        finally:

            conn.close()


# ============================================================
# GERAÇÃO DA RESPOSTA
# ============================================================

def generate_answer(question, columns, rows):
    """
    Recebe o resultado do PostgreSQL
    e transforma em uma resposta em linguagem natural.
    """

    with tracer.start_as_current_span(
        "generate_answer"
    ) as span:

        span.set_attribute(
            "agent.question",
            question
        )

        span.set_attribute(
            "agent.component",
            "NL2SQL"
        )

        span.set_attribute(
            "agent.operation",
            "generate_answer"
        )

        result_text = "\n".join(
            str(dict(zip(columns, row)))
            for row in rows
        )

        prompt = f"""
O usuário fez a seguinte pergunta:

{question}

O banco de dados retornou:

{result_text}

Responda à pergunta do usuário usando somente
os dados retornados pelo banco.

Não invente informações.

Responda em português, de forma clara e objetiva.
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        cost_usd = record_llm_usage(
            span,
            response
        )

        answer = response.output_text.strip()

        span.set_attribute(
            "db.rows_used",
            len(rows)
        )

        return {
            "answer": answer,
            "cost_usd": cost_usd,
        }


# ============================================================
# AGENT COMPLETO
# ============================================================

def ask_agent(question):
    """
    Executa o fluxo completo do NL2SQL Agent.

    Pergunta
       ↓
    LLM → geração SQL
       ↓
    PostgreSQL
       ↓
    LLM → geração resposta
       ↓
    Resposta
    """

    with tracer.start_as_current_span(
        "ask_agent"
    ) as span:

        span.set_attribute(
            "agent.question",
            question
        )

        span.set_attribute(
            "agent.component",
            "NL2SQL"
        )

        # ----------------------------------------------------
        # 1. Gerar SQL
        # ----------------------------------------------------

        sql_result = generate_sql(
            question
        )

        sql = sql_result["sql"]

        sql_cost = sql_result["cost_usd"]

        # ----------------------------------------------------
        # 2. Executar SQL
        # ----------------------------------------------------

        columns, rows = execute_sql(
            sql
        )

        # ----------------------------------------------------
        # 3. Gerar resposta
        # ----------------------------------------------------

        answer_result = generate_answer(
            question,
            columns,
            rows
        )

        answer = answer_result["answer"]

        answer_cost = answer_result["cost_usd"]

        # ----------------------------------------------------
        # 4. Custo total do NL2SQL
        # ----------------------------------------------------

        total_cost = (
            sql_cost
            + answer_cost
        )

        span.set_attribute(
            "db.rows_returned",
            len(rows)
        )

        span.set_attribute(
            "agent.sql_cost_usd",
            sql_cost
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
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "answer": answer,
            "cost_usd": total_cost,
            "sql_cost_usd": sql_cost,
            "answer_cost_usd": answer_cost,
        }