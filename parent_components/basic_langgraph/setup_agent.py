# agent/setup_agent.py
from llm import get_local_llm, compute_savings
from langchain_core.prompts import ChatPromptTemplate

llm = get_local_llm()

primary_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful assistant that calculates solar savings.
Ask for monthly electricity cost, then call the compute_savings tool.
    """),
    ("placeholder", "{messages}")
])

part_1_tools = [compute_savings]
runnable = primary_prompt | llm.bind_tools(part_1_tools)
