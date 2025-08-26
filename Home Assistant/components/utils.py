import re

import requests
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

import speech_recognition as sr
import pyttsx3
import winsound



# === State definition ===
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    sensor_data: dict
    isFeedback: bool
    isContinue: bool
    conversationType: str


# === Plot the graph ===
def plot_graph(graph, path="graph.png"):
    png_data = graph.get_graph().draw_mermaid_png(max_retries=5, retry_delay=2.0)

    # Save to a file
    with open(path, "wb") as f:
        f.write(png_data)

    print(f"[INFO] Saved graph at {path}")


# === Get house context ===
def get_room_devices():
    url = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/test.json"
    resp = requests.get(url)
    data = resp.json()
    print(f'\t\t{"=" * 30}')
    print(f'\t\t[DEBUG] get_room_devices')
    # print(data)
    print(f"\t\t\t{type(data)}")
    print(f'\t\t{"=" * 30}')

    room_devices = {}
    for room, room_data in data.items():
        devices = room_data.get("device", {})
        room_devices[room] = list(devices)
    return room_devices


# === Remove thinking process ===
def extract_thought_and_speech(text):
    # Find first <think>...</think> block
    thought_match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    # Remove all <think>...</think> blocks for the speech part
    speech = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    return thought, speech


def main():
    pass


if __name__ == "__main__":
    main()
