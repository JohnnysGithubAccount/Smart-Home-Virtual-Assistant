import os
import json
import time
import asyncio
from typing import List, Annotated
from typing_extensions import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.constants import END
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, AnyMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# === Replace these with your own ===
from tools import tools, tool_names
from utils import plot_graph  # plot_graph(graph, "graph.png")
from llm import get_llm  # get_llm(name="llama3.2", tools=tools)
from nodes import BasicToolNode, Sensors, ToolRouter  # Your basic nodes
from nodes import Agent, WaitNode
from utils import State


# === Initialize Components ===
llm = get_llm(name="llama3.2", temperature=0, tools=tools)
memory = InMemorySaver()

initial_sensors_node = Sensors()
evaluation_sensors_node = Sensors()
planning_agent = Agent(llm)
tool_node = BasicToolNode(tools=tools)
wait_node = WaitNode(wait_seconds=int(60 * 1))

tool_router = ToolRouter(known_tool_names=tool_names)

# === Graph Definition ===
graph_builder = StateGraph(State)
graph_builder.add_node("initial_sensors", initial_sensors_node)
graph_builder.add_node("planning_agent", planning_agent)
graph_builder.add_node("tools_execution", tool_node)
# graph_builder.add_node("sensors_evaluation", evaluation_sensors_node)
graph_builder.add_node("wait_node", wait_node)

graph_builder.add_edge(START, "initial_sensors")
graph_builder.add_edge("initial_sensors", "planning_agent")
graph_builder.add_edge("tools_execution", "wait_node")

graph_builder.add_conditional_edges(
    "planning_agent",
    tool_router,
    {
        "tools_execution": "tools_execution",
        "wait_node": "wait_node"
    }
)

# graph_builder.add_edge("tools_execution", "sensors_evaluation")
# graph_builder.add_edge("sensors_evaluation", "planning_agent")
graph_builder.add_edge("wait_node", "initial_sensors")

graph = graph_builder.compile(checkpointer=memory)


# === Main Loop ===
async def run_autonomous_loop():
    print("ITERATION")
    print("=" * 50)

    initial_input = {"messages": [HumanMessage(content="Start autonomous monitoring.")]}
    config: RunnableConfig = {
        "thread_id": 1,
        "recursion_limit": 100
    }

    async for event in graph.astream_events(input=initial_input, config=config):
        if "sensor_data" in event:
            print(f"[SENSOR] {event['sensor_data']}")
        if "messages" in event:
            content = event['messages'][-1].content
            print(f"[MSG] {content[:80]}..." if len(content) > 80 else f"[MSG] {content}")

    print("=" * 50)

# === Entrypoint ===
def main():
    plot_graph(graph, "graph.png")
    asyncio.run(run_autonomous_loop())


if __name__ == "__main__":
    main()
