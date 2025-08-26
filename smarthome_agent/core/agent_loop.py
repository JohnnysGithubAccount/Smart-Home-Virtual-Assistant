# from langchain.llms import Ollama
from langchain_ollama import OllamaLLM as Ollama
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from tools import turn_on_lights, turn_off_lights, set_temperature, play_music, shutdown_house
from memory import load_memory, remember_habit, add_schedule
from state import AgentState
import datetime


# 1. LLM Setup
llm = Ollama(model="llama3.2:1b")

# 2. Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful smart home assistant. Always maintain comfort and safety."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])

# 3. Tools
tools = [turn_on_lights, turn_off_lights, set_temperature, play_music, shutdown_house]

# 4. Memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
# memory = AgentTokenBufferMemory(memory_key="chat_history", return_messages=True)
memory = AgentTokenBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    llm=llm  # <--- required!
)

# 5. Agent
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory)

# 6. Human Confirmation Node
def confirm_action(state: AgentState) -> AgentState:
    critical_keywords = ["shutdown", "lock", "security", "fire", "emergency"]
    user_input = state["user_input"]
    if any(word in user_input.lower() for word in critical_keywords):
        print("🧠 [Agent]: This action is critical. Please confirm.")
        confirm = input("⚠️ Confirm this action? (yes/no): ")
        state["confirmed"] = confirm.strip().lower() == "yes"
    else:
        state["confirmed"] = True
    return state

# 7. Execution Node
def execute_action(state: AgentState) -> AgentState:
    if not state["confirmed"]:
        state["action_result"] = "Action was cancelled by user."
        return state
    result = agent_executor.invoke({"input": state["user_input"]})
    state["action_result"] = result.get("output", "No output")
    remember_habit(state["user_input"])
    return state

# 8. LangGraph Wiring
workflow = StateGraph(AgentState)
workflow.add_node("confirm", confirm_action)
workflow.add_node("act", execute_action)
workflow.set_entry_point("confirm")
workflow.add_edge("confirm", "act")
workflow.add_edge("act", END)

# 9. Compiler
graph = workflow.compile()

# 10. Loop
def run_agent():
    print("🛠️ Smart Home Assistant Started. Type 'exit' to quit.")
    while True:
        user_input = input("👤 You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        state = {
            "user_input": user_input,
            "confirmed": False,
            "action_result": None,
            "memory": load_memory()
        }
        result = graph.invoke(state)
        print("🤖 Agent:", result.get("action_result"))

if __name__ == "__main__":
    run_agent()
