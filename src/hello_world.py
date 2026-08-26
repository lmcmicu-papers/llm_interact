# Simple program to demonstrate the basic communication of questions to an Ollama instance via
# LangChain.

from langchain.chat_models import init_chat_model

model = "llama3.1"
print(f"Initializing Ollama model {model} ...")
llm = init_chat_model(f"ollama:{model}")

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to Italian. Translate the user "
        "sentence.",
    ),
    ("human", "Hello, world!"),
]

ai_msg = llm.invoke(messages)
print(ai_msg)
print(ai_msg.content)
