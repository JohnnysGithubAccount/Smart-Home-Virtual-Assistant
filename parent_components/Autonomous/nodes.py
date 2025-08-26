import os
import json
from http.client import responses
from typing import List, Annotated

import requests
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# from tools import tools
# from langgraph.checkpoint.memory import InMemorySaver
from utils import State, plot_graph
import time


# === Wait Node ===
class WaitNode:
    def __init__(self, wait_seconds: int = 30):
        self.wait_seconds = wait_seconds

    def __call__(self, state):
        print(f"[INFO] Waiting {self.wait_seconds} seconds before next cycle...")
        time.sleep(self.wait_seconds)
        return state


class Sensors:
    def __init__(self, url=None):
        if url is None:
            self.url = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/test.json"

    def __call__(self, state: dict):
        print(f'[INFO] Running Sensors node')
        # sensors =  {
        #     'living_room': {
        #         'sensors': {
        #             'temperature': 100, # Celsius
        #             'humidity': 100 # Percentage
        #         },
        #         'device': {
        #             'heater': 70, # degree in Celsius
        #             'humidifier': 50, # percentage
        #             'air conditioner': 17, # degree in Celsius
        #             'lamp': 50, # strength (0-100)
        #             'lights': True, # True means on and False means off
        #         }
        #     },
        #     'bedroom': {
        #         'sensors': {
        #             'temperature': 50, # Celsius
        #             'humidity': 50 # Percentage
        #         },
        #         'device': {
        #             'heater': 20, # degree in Celsius
        #             'humidifier': 100, # percentage
        #             'air conditioner': 26, # degree in Celsius
        #             'lamp': 100, # strength (0-100)
        #             'lights': False, # True means on and False means off
        #         }
        #     },
        #     'kitchen': {
        #         'sensors': {
        #             'temperature': 20,  # Celsius
        #             'humidity': 90  # Percentage
        #         },
        #         'device': {
        #             'stove': False,  # True means on and False means off
        #             'humidifier': 0,  # percentage
        #             'air conditioner': 0,  # degree in Celsius
        #             'lamp': 0,  # strength (0-100)
        #             'lights': False,  # True means on and False means off
        #         }
        #     },
        # }

        # GET request
        response = requests.get(self.url)

        # Check response
        sensors = None
        if response.status_code == 200:
            sensors = response.json()  # This is now a Python dict
            # print("Data fetched successfully:")
        else:
            print(f"Error fetching data: {response.status_code}")

        return sensors


# Updated Agent class (replace in nodes.py)
class Agent:
    """
    A LangGraph-compatible node that calls an LLM agent with tool-calling ability,
    analyzes sensor data, and prints the names of the called tools.
    """

    def __init__(self, llm):
        self.llm = llm  # LLM with tools already bound

    def __call__(self, state: dict):
        print("[INFO] Running Agent node")
        messages = state.get("messages", []).copy()
        sensor_data = state.get("sensor_data", {})

        input_dict = {
            "input": f"Here is the latest sensor data:\n{json.dumps(sensor_data, indent=2)}",
            "history": messages
        }

        llm_response = self.llm.invoke(input_dict)
        print(f"\t[INFO] LLM Response")
        print(f"\t{llm_response.content}")

        # Log tool calls (function names)
        function_names = []
        if hasattr(llm_response, "tool_calls"):
            for call in llm_response.tool_calls:
                function_names.append(call["name"])

        if function_names:
            print(f"[AGENT] Planned function(s): {', '.join(function_names)}")
        else:
            print("[AGENT] No functions planned.")

        return {
            "messages": messages + [llm_response]
        }

# class Agent:
#     """A node that runs the agent"""
#
#     def __init__(self, llm, is_router=False):
#         self.llm = llm
#         self.is_router = is_router
#
#     def __call__(self, state: dict):
#         if not self.is_router:
#             llm_response = self.llm.invoke(state["messages"])
#             return {
#                 'messages': [llm_response]
#             }
#         else:
#             prompt = ChatPromptTemplate.from_messages(
#                 [
#                     (
#                         "system",
#                         """
#                         You are a conversation classifier. You only answer in either CHAT or TOOL.
#                         If the user request is just a normal conversation, answer CHAT.
#                         If the user is trying to ask you to do some sort of task, answer TOOL.
#                         """,
#                     ),
#                     ("human", state["messages"]),
#                 ]
#             )
#             chain = prompt | self.llm
#             chain.invoke(
#                 {
#                     "input_language": "English",
#                     "output_language": "German",
#                     "input": "I love programming.",
#                 }
#             )
#             if chain.content.lower() == 'chat':
#                 return 'chat agent'
#             elif chain.content.lower() == 'tool':
#                 return 'tool agent'

class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
        # print(self.tools_by_name)

    def __call__(self, inputs: dict):
        print(f'[INFO] Running BasicToolNode node')
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []

        print(f'\t[INFO] Looping through tools')
        for tool_call in message.tool_calls:
            print(f"\t-{tool_call['name']}")
            print(f"\t\t{tool_call['args']}")
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


class ToolRouter:
    """
    Callable class to route execution to the tool node if the latest message
    contains tool calls; otherwise, it routes to the END.
    """
    def __init__(self, known_tool_names=None):
        self.known_tool_names = set(known_tool_names or [
            "control_stove",
            "control_lights",
            "control_humidifier",
            "control_ac",
            "control_lamp",
            "control_fan",
            # Add more tool names as needed
        ])

    def __call__(self, state: dict) -> str:
        """
        Determine routing based on whether any message content looks like a tool call.
        """
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, AIMessage):
                if msg.tool_calls:
                    return "tools_execution"

                lines = msg.content.strip().splitlines()
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        tool_name, args_json = line.split(",", 1)
                        tool_name = tool_name.strip().strip('"')
                        if tool_name in self.known_tool_names:
                            json.loads(args_json)  # Check valid JSON
                            return "tools_execution"
                    except Exception:
                        continue  # Malformed line
        return "wait_node"
