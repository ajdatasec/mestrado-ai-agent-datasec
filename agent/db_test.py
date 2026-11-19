import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

with conn.cursor() as cur:
    cur.execute("""
        SELECT
            cliente_id,
            nome,
            pais,
            regiao
        FROM clientes
        ORDER BY cliente_id;
    """)

    rows = cur.fetchall()

    for row in rows:
        print(row)

conn.close()

print("\nConexão e consulta realizadas com sucesso.")
