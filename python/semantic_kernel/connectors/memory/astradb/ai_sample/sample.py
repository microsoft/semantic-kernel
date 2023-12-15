from semantic_kernel.connectors.memory.astradb.ai_sample.utils import kernel

question = "As a friendly AI Copilot, answer the question: Did Albert Einstein like coffee?"
prompt = kernel.create_semantic_function(question)
print(f"Question: {question}\nAnswer: {prompt()}")
