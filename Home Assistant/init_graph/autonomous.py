from langchain_core.runnables import RunnableConfig
from langgraph.constants import END
from langgraph.graph import StateGraph, START
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

# === Modules ===
from components.tools import tools, tool_names
from components.llm import get_llm
from components.nodes import Tools, Sensors, WaitNode, ToolRouter, Agent, PlanningRouter, Setup
from components.utils import State, plot_graph


# === Initialize Components ===
llm_action = get_llm(name="qwen3:1.7b", temperature=0, tools=tools[1:], typeAutonomous="action")
llm_thinking = get_llm(name="qwen3:1.7b", temperature=0.2, tools=tools[1:], typeAutonomous="thinking")

memory = InMemorySaver()

# === Defines nodes ===
initial_sensors_node = Sensors()
setup = Setup()

planning_agent = Agent(llm_thinking, isAutonomous=True)
executing_agent = Agent(llm_action)

tool_node = Tools(tools=tools)
wait_node = WaitNode(wait_seconds=5 * 60)  # wait 5 minutes

# === Defines routers ===
tool_router = ToolRouter(
    known_tool_names=tool_names,
    target_node1="tools_execution",
    target_node2="sensors",
    target_node3="wait_node"
)
planning_router = PlanningRouter(execution_node="executing_agent", end_key=END)

# === Graph Definition ===
graph_builder = StateGraph(State)
graph_builder.add_node("sensors", initial_sensors_node)
graph_builder.add_node("setup", setup)
graph_builder.add_node("planning_agent", planning_agent)
graph_builder.add_node("executing_agent", executing_agent)
graph_builder.add_node("tools_execution", tool_node)
graph_builder.add_node("wait_node", wait_node)

graph_builder.add_edge(START, "setup")
graph_builder.add_edge("setup", "sensors")
graph_builder.add_edge("sensors", "planning_agent")
graph_builder.add_edge("tools_execution", "executing_agent")
graph_builder.add_edge("wait_node", "sensors")

graph_builder.add_conditional_edges(
    "planning_agent",
    planning_router,
    {
        "executing_agent": "executing_agent",
        END: END
    }
)
graph_builder.add_conditional_edges(
    "executing_agent",
    tool_router,
    {
        "tools_execution": "tools_execution",
        "sensors": "sensors",
        "wait_node": "wait_node"
    }
)

graph = graph_builder.compile(checkpointer=memory)


# === Entrypoint ===
def main():
    plot_graph(graph, "graphs/autonomous_graph.png")


if __name__ == "__main__":
    main()
