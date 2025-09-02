from langgraph.constants import END
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver

# === Modules ===
from components.tools import tools, tool_names, chat_tool_names, chat_tools
from components.llm import get_llm
from components.nodes import Tools, Sensors, ToolRouter, Agent, ChatRouter, ChatClassifier
from components.nodes import LongTermMemory, UserChecking, IsContinueRouter
from components.utils import State, plot_graph, load_configs


# === Get configs ===
configs = load_configs("../Home Assistant/configs.json")

# === Initialize Components ===
tool_llm = get_llm(
    name=configs["instance"]["models"]["tool_llm"]["model"],
    temperature=configs["instance"]["models"]["tool_llm"]["temperature"],
    tools=tools
)
router_llm = get_llm(
    name=configs["instance"]["models"]["router_llm"]["model"],
    temperature=configs["instance"]["models"]["router_llm"]["temperature"],
    tools=None,
    isRouter=True
)
chat_llm = get_llm(
    name=configs["instance"]["models"]["chat_llm"]["model"],
    temperature=configs["instance"]["models"]["chat_llm"]["temperature"],
    tools=None
)
summarize_llm = get_llm(
    name=configs["instance"]["models"]["summarize_llm"]["model"],
    temperature=configs["instance"]["models"]["summarize_llm"]["temperature"],
    tools=None,
    isSummarize=True
)
checking_llm = get_llm(
    name=configs["instance"]["models"]["checking_llm"]["model"],
    temperature=configs["instance"]["models"]["checking_llm"]["temperature"],
    tools=None,
    isSummarize=True
)


# === Long-term memory ===
memory = InMemorySaver()

# === Defines nodes ===
chat_classifier = ChatClassifier(llm=router_llm)
chat_agent = Agent(chat_llm)
tool_agent = Agent(tool_llm, isToolCallingModel=True)
tool_node = Tools(tools=tools)
chat_tool_node = Tools(tools=chat_tools)
long_term_memory_node = LongTermMemory(
    url=configs["graph database"]["url"],
    username=configs["graph database"]["username"],
    password=configs["graph database"]["password"],
    llm=summarize_llm
)
checking_user = UserChecking(llm=checking_llm)

# === Defines routers ===
router_agent = ChatRouter()
tool_router = ToolRouter(
    known_tool_names=tool_names,
    target_node1="executing tools",
    target_node2="check user"
)
is_continue_router = IsContinueRouter()

# === Graph Nodes Definition ===
graph_builder = StateGraph(State)
graph_builder.add_node("chat_classifier", chat_classifier)
graph_builder.add_node("chat_agent", chat_agent)
graph_builder.add_node("tool_agent", tool_agent)
graph_builder.add_node("tools_execution", tool_node)
graph_builder.add_node("chat_tools", chat_tool_node)
graph_builder.add_node("user_checking", checking_user)
graph_builder.add_node("long_term_memory", long_term_memory_node)

# === Graph Edges Definition ===
graph_builder.add_edge(START, "chat_classifier")
# graph_builder.add_edge("chat_agent", "user_checking")
graph_builder.add_edge("tools_execution", "tool_agent")
graph_builder.add_edge("long_term_memory", END)
graph_builder.add_edge("chat_tools", "chat_agent")

# === Conditional edges ===
graph_builder.add_conditional_edges(
    "chat_classifier",
    router_agent,
    {
        "normal Q&A": "chat_agent",
        "control devices": "tool_agent"
    }
)
graph_builder.add_conditional_edges(
    "tool_agent",
    tool_router,
    {
        "executing tools": "tools_execution",
        "check user": "user_checking",
    }
)
graph_builder.add_conditional_edges(
    "chat_agent",
    tool_router,
    {
        "executing tools": "chat_tools",
        "check user": "user_checking",
    }
)
graph_builder.add_conditional_edges(
    "user_checking",
    is_continue_router,
    {
        "continue": "chat_classifier",
        "saving conversation": "long_term_memory",
    }
)

# === Compile graph ===
graph = graph_builder.compile(
    checkpointer=memory
)


# === Entrypoint ===
def main():
    plot_graph(graph, "graphs/instance.png")


if __name__ == "__main__":
    main()
