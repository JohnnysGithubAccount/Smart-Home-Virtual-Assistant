from typing import Annotated

# from posthog.ai.utils import format_response
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM as Ollama
from utils import State

def update_system_prompt(memory_tasks, memory_responses):
    system_prompt = f"""
       % Role: 
       You are an AI assistant helping a user with a task. You have access to % Tools to help you with the task.

       % Task: 
       Check the user's query and provide a tool or tools to use for the task if appropriate. Always check the memory for previous questions and answers to choose the appropriate tool.

       % Memory:
       You have a memory of the user's questions and your answers.
       Previous Questions: {memory_tasks}
       Previous Answers: {memory_responses}

       % Instructions: 
       Choose the appropriate tool to use for the task based on the user's query.
       Tools that require content will have a variable_name and variable_value.
       A tool variable value can be another tool or a variable from a previous tool.
       Check the memory for previous questions and answers to choose the appropriate variable if it has been set.
       If the tool doesn't need variables, put the tool name in the variable_name and leave the variable_value empty.

       % Tools:
       open_chrome - Open Google Chrome
       navigate_to_hackernews - Navigate to Hacker News
       get_https_links - Get all HTTPS links from a page requires URL

       % Output:
       json only

       {{
           "tool": "tool" or ""
           "variables": [
               {{
                   "variable_name": "variable_name" or ""
                   "variable_value": "variable_value" or ""
               }}
           ]
       }}
       """


def chatbot(state: State, llm, system_prompt, json_format: bool = False):
    # user_message = state['messages'][-1]['content']
    if json_format:
        format_response = {'type': 'json_object'}
    else:
        format_response = {'type': 'text'}

    user_message = state['messages'][-1].content
    messages = [
        {
            'role': 'system',
            'content': system_prompt
        },
        {
            'role': 'user',
            'content': user_message
        }
    ]
    # assistant_response = llm.invoke(user_message)
    assistant_response = llm.invoke(messages)
    return {"messages": state['messages'] + [{"role": "assistant", "content": assistant_response}]}