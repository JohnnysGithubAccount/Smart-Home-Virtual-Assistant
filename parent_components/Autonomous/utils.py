from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, Optional
import time

import os
import json
from typing import List, Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, AnyMessage


# === State definition ===
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    sensor_data: dict
def plot_graph(graph, path="graph.png"):
    png_data = graph.get_graph().draw_mermaid_png()

    # Save to a file
    with open(path, "wb") as f:
        f.write(png_data)


