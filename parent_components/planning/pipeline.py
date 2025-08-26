from typing import Annotated

# from posthog.ai.utils import format_response
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM as Ollama
from langchain_core.tools import tool

import os
import json
import subprocess

import requests
from bs4 import BeautifulSoup

from utils import State
from tools import open_chrome, navigate_to_hackernews, get_https_links


class Agent:
    def __init__(self, tools, model="llama3.2", temperature=0):
        self.memory_tasks = []
        self.memory_responses = []

        self.tool_list = {tool.__name__: tool for tool in tools}
        self.tool_names = {tool.__name__ for tool in tools}

        self.llm = Ollama(model=model, temperature=temperature)

        graph_builder = StateGraph(State)
        graph_builder.add_node("chatbot", self.chatbot)
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", END)
        self.graph = graph_builder.compile()

        self.planned_actions = []
        self.url = ""
        self.links = []

        self.planning_system_prompt = """
            % Role: 
            You are an AI assistant helping a user plan a task. You have access to % Tools to help you with the order of tasks.
    
            % Task: 
            Check the user's query and provide a plan for the order of tools to use for the task if appropriate. Do not execute only out line the tasks in order to accomplish the user's query.
    
            % Instructions: 
            Create a plan for the order of tools to use for the task based on the user's query.
            Choose the approapriate tool or tools to use for the task based on the user's query.
            Tools that require content will have a variable_name and variable_value.
            A tool variable value can be another tool or a variable from a previous tool or the variable that is set in memory.
            If a variable is set in memory, use the variable value from memory.
            If the tool doesn't need variables, put the tool name in the variable_name and leave the variable_value empty.
            Memories will be stored for future use. If the output of a tool is needed, use the variable from memory.
    
            % Tools:
            open_chrome - Open Google Chrome
            navigate_to_hackernews - Navigate to Hacker News
            get_https_links - Get all HTTPS links from a page requires URL
    
            % Output:
            Plan of how to accomplish the user's query and what tools to use in order
            Each step should be one a single line with the tool to use and the variables if needed 
        """
        self.system_prompt = None

    def save_graph(self, path: str = 'graph.png'):
        with open(path, "wb") as f:
            f.write(self.graph.get_graph().draw_mermaid_png())

    def update_system_prompt(self):
        self.planning_system_prompt = f"""
            % Role: 
            You are an AI assistant helping a user with a task. You have access to % Tools to help you with the task.
            
            % Task: 
            Check the user's query, if it a normal conversation query from the user, just answer normaly. 
            If user ask you to do something, provide a tool or tools to use for the task if appropriate. 
            Always check the memory for previous questions and answers to choose the appropriate tool.
            
            % Memory:
            You have a memory of the user's questions and your answers.
            Previous Questions: {self.memory_tasks}
            Previous Answers: {self.memory_responses}
            
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

    def chatbot(self, state: State):
        # user_message = state['messages'][-1]['content']
        user_message = state['messages'][-1].content
        assistant_response = self.llm.invoke(user_message)
        return {"messages": state['messages'] + [{"role": "assistant", "content": assistant_response}]}

    def chat(self, user_input, system_prompt, json_format: bool = False):
        # user_message = state['messages'][-1]['content']
        if json_format:
            format_response = {'type': 'json_object'}
        else:
            format_response = {'type': 'text'}

        # user_message = state['messages'][-1].content
        messages = {
            "messages": [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_input
                },
            ]
        }
        # assistant_response = llm.invoke(user_message)
        # assistant_response = self.llm.invoke(messages)
        assistant_response = self.graph.invoke(messages)
        # print(messages)
        # return {"messages": state['messages'] + [{"role": "assistant", "content": assistant_response}]}
        return assistant_response['messages'][-1].content

    ## Plan and Execute
    def run(self, user_input_prompt: str):
        ## Planning
        planning = self.chat(user_input_prompt, self.planning_system_prompt)
        self.planned_actions = planning.split("\n")
        # print('planning\n', planning)

        ## Task Execution
        # print(len(self.planned_actions))
        # print(self.planned_actions)
        self.memory_responses.append(f'User asked: "{user_input_prompt}"')
        for task in self.planned_actions:
            if task in self.tool_names:
                pass
            elif task in ["", " "]:
                continue
            else:
                print(f"[Assistant]: {task}")
                self.memory_tasks.append(task)
                self.memory_responses.append(task)
                self.update_system_prompt()
                print("=" * 50)
                for memory_response in self.memory_responses:
                    print(memory_response)
                print("=" * 50)
                continue

            print(f"\n\nExecuting task: {task}")
            self.memory_tasks.append(task)
            self.update_system_prompt()
            task_call = self.chat(task, self.system_prompt, True)
            self.memory_responses.append(task_call)

            try:
                task_call_json = json.loads(task_call)
            except json.JSONDecodeError as e:
                print(f"Error decoding task call: {e}")
                continue

            tool = task_call_json.get("tool")
            variables = task_call_json.get("variables", [])

            # if tool == "open_chrome":
            #     # self.open_chrome()
            #     self.tool_list[0]()
            #     self.memory_responses.append("open_chrome=completed.")
            #
            # elif tool == "get_https_links":
            #     # self.links = self.get_https_links(self.url)
            #     self.links = self.tool_list[2]()
            #     self.memory_responses.append(f"get_https_links=completed. variable urls = {self.links}")
            #
            # elif tool == "navigate_to_hackernews" :
            #     query = variables[0].get("variable_value", "")
            #     # self.navigate_to_hackernews(query)
            #     self.tool_list[1](query)
            #     self.memory_responses.append(f"navigate_to_hackernews=completed. variable query = {query}")
            #
            if tool in self.tool_names:
                print(f'Using this {tool}')



if __name__ == "__main__":
    agent = Agent(
        tools=[open_chrome, navigate_to_hackernews, get_https_links]
    )
    agent.save_graph('graph.png')

    while True:
        prompt = input("Please enter a prompt (or type 'exit' to quit): ")
        if prompt.lower() == 'exit':
            break
        agent.run(prompt)