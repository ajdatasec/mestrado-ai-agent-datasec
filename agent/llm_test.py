import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-5.6-luna",
    input="Responda apenas: OK. A conexão com o LLM está funcionando."
)

print(response.output_text)