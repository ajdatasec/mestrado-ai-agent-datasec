from rag_agent import ask_rag


question = "O que acontece quando um funcionário deixa a organização?"

result = ask_rag(question)

print("\nPergunta:")
print(result["question"])

print("\nResposta:")
print(result["answer"])

print("\nChunks recuperados:")

for chunk in result["results"]:
    print("-" * 80)
    print(f"Chunk: {chunk[2]}")
    print(f"Similaridade: {chunk[4]:.4f}")
    print(f"Conteúdo: {chunk[3]}")
