import ollama

response = ollama.chat(
    model="qwen3:4b",
    messages=[
        {"role": "user", "content": "what is 2 + 2? reply in one sentence"}
    ]
)

print(response.message.content)