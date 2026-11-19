from agent import ask_agent


question = "Quais clientes fizeram mais pedidos?"

result = ask_agent(question)

print("\n==============================")
print("PERGUNTA")
print("==============================")
print(result["question"])

print("\n==============================")
print("SQL")
print("==============================")
print(result["sql"])

print("\n==============================")
print("RESULTADO")
print("==============================")

print(" | ".join(result["columns"]))

for row in result["rows"]:
    print(" | ".join(str(value) for value in row))

print("\n==============================")
print("RESPOSTA DO AGENTE")
print("==============================")
print(result["answer"])