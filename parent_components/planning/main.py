from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM as Ollama

from IPython.display import Image, display

from utils import *
from llm import *


# No need for API keys
llm = Ollama(model="llama3.2:1b", temperature=0)

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

try:
    # display(Image(graph.get_graph().draw_mermaid_png()))
    with open("graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

except Exception as e:
    print(e)
    pass

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "q", "exit"]:
        print("Assistant: Goodbye!")
        break
    initial_state = {
        'messages': [
            {
                "role": "user",
                "content": user_input
            }
        ]
    }
    result = graph.invoke(initial_state)
    assistant_message = result['messages'][-1].content
    print(f"Assistant: {assistant_message}")