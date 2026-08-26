##
# llm_interact - a handy tool for communicating with Ollama LLM models using Python
# Copyright (C) 2025 Michael E. Cuffaro
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

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
