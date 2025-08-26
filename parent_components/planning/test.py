import os
import json
import asyncio
import operator
from typing import Annotated, List, Tuple, Union, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain_ollama import OllamaLLM as Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START

# --------------------------
# Define Tools
# --------------------------
def open_chrome(url: str = "https://www.google.com") -> str:
    return f"Opening Chrome with URL: {url}"

def search_information(query: str) -> str:
    return f"Searching for information on: {query}"

TOOLS = {
    "open_chrome": open_chrome,
    "search_information": search_information,
}

# --------------------------
# Manual Tool Planner Prompt
# --------------------------
agent_prompt = ChatPromptTemplate.from_template("""
You are a smart home AI assistant. Choose the best tool to perform the user's request.

Respond ONLY in this JSON format:
{{"tool": "tool_name", "input": "your input string here"}}

Available tools:
- open_chrome: Open a web browser to a given URL
- search_information: Search for general information

User request: {input}
""")

# Initialize Ollama model
llm = Ollama(model='llama3.2:1b', temperature=0.0)

# Agent loop for tool calling
def run_tool_agent(user_input: str):
    chain = agent_prompt | llm
    response = chain.invoke({"input": user_input})

    try:
        tool_call = json.loads(response)
        tool_name = tool_call.get("tool")
        tool_input = tool_call.get("input")

        if tool_name in TOOLS:
            result = TOOLS[tool_name](tool_input)
            print(f"\n🔧 Tool result: {result}\n")
            return result
        else:
            print(f"⚠️ Unknown tool: {tool_name}")
            return "Unknown tool"

    except json.JSONDecodeError:
        print("❌ Failed to parse response:", response)
        return response

# Example tool invocation
tool_result = run_tool_agent("Open YouTube")

# --------------------------
# Planning & Execution Workflow
# --------------------------
class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

class Plan(BaseModel):
    steps: List[str] = Field(description="Steps to follow")

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """
For the given objective, come up with a simple step by step plan. 
This plan should involve individual tasks. The final step should lead to the final answer.
    """),
    ("placeholder", "{messages}"),
])

planner = planner_prompt | llm | StrOutputParser()

replanner_prompt = ChatPromptTemplate.from_template("""
For the given objective, come up with a simple step by step plan.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the following steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that.
""")

replanner = replanner_prompt | llm | StrOutputParser()

class Response(BaseModel):
    response: str

class Act(BaseModel):
    action: Union[Response, Plan] = Field(description="Response to user or new plan")

# --------------------------
# Async Agent Steps
# --------------------------
async def execute_step(state: PlanExecute):
    plan = state["plan"]
    task = plan[0]
    print(f"\n🧠 Executing step: {task}")
    result = run_tool_agent(task)
    return {"past_steps": [(task, result)]}

async def plan_step(state: PlanExecute):
    plan_text = await planner.ainvoke({"messages": [("user", state["input"])]})
    plan_lines = plan_text.strip().split("\n")
    return {"plan": [line.strip("- ") for line in plan_lines if line.strip()]}

async def replan_step(state: PlanExecute):
    plan_str = "\n".join(state["plan"])
    past_str = json.dumps(state["past_steps"])
    response = await replanner.ainvoke({
        "input": state["input"],
        "plan": plan_str,
        "past_steps": past_str
    })
    if "response" in response:
        return {"response": response["response"]}
    else:
        return {"plan": [line.strip("- ") for line in response.strip().split("\n") if line.strip()]}

def should_end(state: PlanExecute) -> Literal["agent", "__end__"]:
    return "__end__" if state.get("response") else "agent"

# --------------------------
# Workflow Definition
# --------------------------
workflow = StateGraph(PlanExecute)
workflow.add_node("planner", plan_step)
workflow.add_node("agent", execute_step)
workflow.add_node("replan", replan_step)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", "replan")
workflow.add_conditional_edges("replan", should_end)

app = workflow.compile()

# Save workflow graph image
img_bytes = app.get_graph(xray=True).draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(img_bytes)

# --------------------------
# Run Full Async Agent
# --------------------------
async def run():
    config = {"recursion_limit": 50}
    inputs = {"input": "what is the hometown of the men's 2024 Australia Open winner?"}

    async for event in app.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                print(v)

if __name__ == "__main__":
    asyncio.run(run())
