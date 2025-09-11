import os
import json
from http.client import responses
from typing import List, Annotated
import time
import requests
from langchain_core.runnables import RunnableConfig
from torch.utils.tensorboard.summary import histogram
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, BaseMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# from tools import tools
# from langgraph.checkpoint.memory import InMemorySaver
from .utils import get_room_devices, State, extract_thought_and_speech
from .llm import StopStreamingException, ToolCallStreamHandler, MyStreamHandler
from .longterm_memory import MemoryHelper
from .voice.text_to_speech import speak
from .voice.speech_to_text import listen
from langchain_core.messages import AIMessageChunk


# === Wait Node ===
class WaitNode:
    def __init__(self, wait_seconds: int = 30):
        self.wait_seconds = wait_seconds

    def __call__(self, state):
        print("=" * 50)
        print(f"[INFO] Waiting {self.wait_seconds} seconds before next cycle...")
        time.sleep(self.wait_seconds)
        return state


# === Fetching sensors information node ===
class Sensors:
    def __init__(self, url=None):
        if url is None:
            self.url = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/test.json"

    def __call__(self, state: State):
        start_time = time.time()

        print("=" * 50)
        print(f'[INFO] Running Sensors node')

        print(f'\t[DEBUG] Debugging isFeedback: {state["isFeedback"]}')

        # GET request
        response = requests.get(self.url)

        # Check response
        sensors = None
        if response.status_code == 200:
            sensors = response.json()  # This is now a Python dict
            # print("Data fetched successfully:")
        else:
            print(f"Error fetching data: {response.status_code}")

        print(f"\t[INFO] Elapse time: {time.time() - start_time}")
        print(f'\t[DEBUG] Debugging isFeedback: {state["isFeedback"]}')
        return {"sensor_data": sensors, "isFeedback": state['isFeedback']}


# === Agent node ===
class Agent:
    """
    A LangGraph-compatible node that calls an LLM agent with tool-calling ability,
    analyzes sensor data, and injects device context if needed.
    """

    def __init__(self, llm, isAutonomous: bool = False, isToolCallingModel: bool = False, vector_index=None):
        self.llm = llm  # LLM with tools already bound
        self.isAutonomous = isAutonomous
        self.isToolCallingModel = isToolCallingModel
        self.handler = MyStreamHandler()
        self.vector_index = vector_index

    def __call__(self, state: State):
        start_time = time.time()

        print("=" * 50)
        print("[INFO] Running Agent node")

        messages = state.get("messages", []).copy()
        print(f"\t\t[DEBUG] Input messages: {messages}")

        # Autonomous mode: replace with sensor data string
        if self.isAutonomous:
            sensor_data = state.get("sensor_data", {})

            print(f"\t\t[DEBUG] isFeedback in the if clause: {state['isFeedback']}")
            if state['isFeedback']:
                add_in_text = f"This is a feedback, do the second role: Feedback Evaluation"
                state['isFeedback'] = False
                print(f"\t[INFO] Setting isFeedback to {state['isFeedback']} at Thinking Agent")
            else:
                add_in_text = f"Do your first role: Initial Planning"
                state['isFeedback'] = True
            messages.append(
                f"Here is the latest sensor data:\n{json.dumps(sensor_data)}. {add_in_text}"
            )


        # === Add all the tool messages ===
        if isinstance(messages[-1], ToolMessage):
            tool_msgs = []
            for msg in reversed(messages):
                if isinstance(msg, ToolMessage):
                    tool_msgs.append(msg)
                else:
                    break
            tool_msgs = list(reversed(tool_msgs))  # restore original order
            input_messages = tool_msgs

            # Remove those tool messages from the state
            state["messages"] = messages[: -len(tool_msgs)]
            print(f"\t\t[DEBUG] state['message'] cut: ", state["messages"])
        else:
            input_messages = [messages[-1]]  # wrap in list for consistency

        # the history is the last 5 messages, if isAutonomous, do not care for history
        # history = state["messages"][-10:]
        history = [m for m in state["messages"] if not isinstance(m, ToolMessage)][-10:]

        print(f"\t\t{'-' * 50}")
        print(f"\t\t[INFO] History")
        for value in history:
            print(f"\t\t\t[DETAILS] {value}")
        print(f"\t\t{'-' * 50}")

        # === Retrieve Context ===
        if isinstance(input_messages[-1], ToolMessage):
            context = []
        else:
            retrieved_docs = self.vector_index.similarity_search(input_messages[-1].content, k=3)
            print(f"\t\t[DEBUG] retrieved_docs: {retrieved_docs}")
            context_as_list = [doc.page_content for doc in retrieved_docs]
            context = "\n".join(context_as_list)
            print(f"\t\t[DEBUG] retrieved_docs before: {context_as_list}")
            print(f"\t\t[DEBUG] retrieved_docs after: {context}")
            context = [context]


        input_dict = {
            "input": input_messages,
            "history": history,
            "context": context
        }

        print(f"\t\t[DEBUG] Input dict: {input_dict}")

        # chunks = []
        # for chunk in self.llm.stream(input_dict, callbacks=[self.handler]):
        #     if chunk.content:
        #         print(chunk.content, end="", flush=True)
        #     chunks.append(chunk)
        #
        # # Manually merge into a full AIMessage
        # final_msg = AIMessage(
        #     content="".join([c.content for c in chunks if c.content]),
        #     tool_calls=[tc for c in chunks for tc in (c.tool_calls or [])],
        #     additional_kwargs={k: v for c in chunks for k, v in (c.additional_kwargs or {}).items()},
        #     response_metadata={k: v for c in chunks for k, v in (c.response_metadata or {}).items()},
        # )
        #
        # llm_response = final_msg.content
        # print("\n\nFinal text:", final_msg.content)
        llm_response = self.llm.invoke(input_dict)
        print(f"\t\t[DEBUG]Tool calls:", llm_response.tool_calls)

        print(f"\t[INFO] Elapse time: {time.time() - start_time}")
        return_dict = {
            "messages": state["messages"] + [llm_response],
        }
        if self.isAutonomous:
            return_dict["isFeedback"] = state["isFeedback"]
        print(f"\t\t[DEBUG] Debug return_dict")
        for key,value in return_dict.items():
            print(f"\t\t\t[DEBUG] {key}:{value}")

        return return_dict


# === Tool execution node ===
class Tools:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
        # print(self.tools_by_name)

    def __call__(self, inputs: dict):
        start_time = time.time()

        print("=" * 50)
        print(f'[INFO] Running BasicToolNode node')
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []

        print(f'\t[INFO] Looping through tools')
        for tool_call in message.tool_calls:
            print(f"\t\t[VALIDATION]{tool_call['name']}")

        print(f"\t[INFO] Running through tools")
        for tool_call in message.tool_calls:
            if 'function' in str(tool_call['args']):
                print(f'\t\t[ADJUST] Original arguments: {tool_call["args"]}')
                tool_call["args"] = tool_call["args"]["parameters"]
                print(f'\t\t[ADJUST] Modified arguments: {tool_call["args"]}')

            print(f"\t\t\t[DEBUG] Tool name: {tool_call['name']}")
            print(f"\t\t\t[DEBUG] Tool arguments: {tool_call['args']}")
            try:
                tool_result = self.tools_by_name[tool_call["name"]].invoke(
                    tool_call["args"]
                )
                tool_result["room"] = tool_call["args"]["room"]
            except Exception as e:
                print(f"\t\t[ERROR] Got error handling the followings")
                print(f"\t\t\tError: {e}")
                print(f"\t\t\tFunction name: {tool_call['name']}")
                print(f"\t\t\tFunction arguments: {tool_call['args']}")

            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            print(f"\t\t\t[DEBUG] Output messages: {outputs[0].content}")

            # inputs["messages"].extend(outputs)

        new_messages = messages + outputs
        print(f"\t\t[DEBUG] New messages:", new_messages)

        print(f"\t[INFO] Elapse time: {time.time() - start_time}")
        return {"messages": new_messages}


# === Tool router ===
class ToolRouter:
    def __init__(self, target_node1: str = "tools", target_node2: str = END, target_node3=None, known_tool_names=None):
        """
        Routes to `target_node` if the last AI message contains tool calls,
        otherwise routes to END.
        """
        self.target_node1 = target_node1
        self.target_node2 = target_node2
        self.target_node3 = target_node3

    def __call__(self, state: State):
        start_time = time.time()

        print(f"{'=' * 50}")
        print(f"[DEBUG] Running ToolRouter")

        # Support both list-of-messages and dict-with-messages
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state: {state}")

        # Check if the message contains tool calls
        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            print(f"\t[INFO] Directing to executing on tools")
            print(f"\t[DEBUG] Check tool_calls attribute: {hasattr(ai_message, 'tool_calls')}")
            print(f"\t[DEBUG] Check tool_calls: {ai_message.tool_calls}")

            print(f"\t[INFO] Elapse time: {time.time() - start_time}")
            print(f"{'=' * 50}")
            return self.target_node1

        if extract_thought_and_speech(ai_message.content)[1].strip().upper() == "WAIT" and self.target_node3:
            print(f"\t[INFO] Routing to {self.target_node3}")
            state['isFeedback'] = True
            print(f"\t[INFO] Setting isFeedback to {state['isFeedback']} at {self.target_node3}")
            print(f"{'=' * 50}")
            return self.target_node3

        # Otherwise, finish
        print(f"\t[INFO] Elapse time: {time.time() - start_time}")

        state['isFeedback'] = True
        print(f"\t[INFO] Setting isFeedback to {state['isFeedback']} at {self.target_node2}")
        print(f"{'=' * 50}")
        return self.target_node2


# === Chat router ===
class ChatRouter:
    """
    Routes a message to 'tool agent' or 'chat agent'
    based on classification from a small LLM (self.llm).
    The LLM should already have its system prompt set
    when it is passed to this class.
    """

    def __init__(self):
        pass

    def __call__(self, state: dict) -> str:
        start_time = time.time()

        print("[INFO] Running ChatRouter node")

        decision = state["conversationType"].strip().upper()

        print(f"\t[DEBUG] decision: {decision}")

        if decision == "TOOL":
            print(f"\t[DEBUG] Routing to {decision}")
            print(f"\t[INFO] Elapse time: {time.time() - start_time}")
            return "control devices"
        elif decision == "CHAT":
            print(f"\t[DEBUG] Routing to {decision}")
            print(f"\t[INFO] Elapse time: {time.time() - start_time}")
            return "normal Q&A"
        else:
            print(f"\[ERROR] Wrong input: {state['conversationType']}")
            print(f"\t[INFO] Elapse time: {time.time() - start_time}")
            return "normal Q&A"


# === Chat Classifier ===
class ChatClassifier:
    def __init__(self, llm):
        """
        Args:
            llm: A small, fast LLM for classification.
                 Should already have a system prompt instructing:
                 - Reply with "TOOL" if the message requires tool use.
                 - Reply with "CHAT" otherwise.
        """
        self.llm = llm

    def __call__(self, state: dict):
        start_time = time.time()

        print("[INFO] Running ChatClassifier node")

        # Extract last user message
        if isinstance(state, list):
            user_message = state[-1].content
        elif messages := state.get("messages", []):
            user_message = messages[-1].content
        else:
            raise ValueError("[ERROR] No messages found in state for ChatRouter.")

        return_dict = {}
        try:
            history = state["messages"][-5:]
            result = self.llm.invoke(
                {
                    "input": user_message,
                    "history": history
                }
            ).content
            _, result = extract_thought_and_speech(result)
            print(f"\t[INFO] User input type: {result}")
            decision = result.strip().upper()

            print(f"\t[INFO] Elapse time: {time.time() - start_time}")



            if decision in ["TOOL", "CHAT"]:
                return_dict['conversationType'] = decision
            else:
                print(f"[WARN] Unexpected classification: {decision}, defaulting to chat.")
                return_dict["conversationType"] = "CHAT"

        except Exception as e:
            print(f"[ERROR] Failed to classify message: {e}")
            return_dict["conversationType"] = "CHAT"

        return return_dict


# ==== Planning router ===
class PlanningRouter:
    def __init__(self, end_key=END, execution_node="executing_agent"):
        self.end_key = end_key
        self.execution_node = execution_node

    def __call__(self, state: State) -> str:
        """
        Routes based on planning agent output.
        """
        print(f"{'=' * 50}")
        print("[INFO] Running PlanningRouter node")
        start_time = time.time()

        # Support both list-of-messages and dict-with-messages
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state: {state}")

        # Check if the message is END
        print(f"\t[INFO] Elapse time: {time.time() - start_time}")

        if extract_thought_and_speech(ai_message.content)[1].upper().strip() == "END":
            print(f"\t[DEBUG] Directing to {self.end_key}")
            print(f"{'=' * 50}")
            return self.end_key
        else:
            print(f"\t[DEBUG] Directing to {self.execution_node}")
            print(f"{'=' * 50}")
            return self.execution_node


# === Setup config ===
class Setup:
    def __call__(self, state):
        print(f"[INFO] Running Setup node")
        if "isFeedback" not in state:
            state["isFeedback"] = False

        return state


# === Long Term Memory ===
class LongTermMemory:
    def __init__(self, url, username, password, llm=None, embeddings=None):
        self.memory = MemoryHelper(url, username, password, llm=llm, embeddings=embeddings)

    def __call__(self, state):
        text = self.memory.summarize_messages(state["messages"])
        print(text)
        # _, response = extract_thought_and_speech(text)
        self.memory.text_to_graph(text)


# === Long Term Memory ===
class UserChecking:
    def __init__(self, llm=None):
        system_prompt = f"""
        You are an intention classifier.  
        Your only task is to decide if the user wants to continue the conversation or if they are finished.  

        You must classify the user input into exactly one of these three labels:

        - CONTINUE_IMMEDIATELY: if the user asks a question, says something semantically meaningful, gives instructions, or makes a request.  
        - CONTINUE_CONFIRM: if the user is only responding with a short confirmation (e.g., "yes", "no", "okay", "got it", "sure", "thanks" when it implies readiness to continue).  
        - END: if the user says goodbye, ends the conversation, or indicates no further intention to continue.  

        Rules:
        - Output must be exactly one of: CONTINUE_IMMEDIATELY, CONTINUE_CONFIRM, or END.  
        - Do not explain, do not add punctuation, do not output anything else.
        """
        system_prompt = f""" 
        You are an intention classifier. 
        Your only task is to decide if the user wants to continue the conversation or if they are finished. 
        
        Rules: 
        - If the user sentence means they are still making conversation like asks a question, makes a request, or gives instructions (demand to turn something on or off, demand to adjust some devices, or ask question) → respond with exactly "CONTINUE". 
        - If the user sentence means they want to end the conversation → respond with exactly "END".
        - Do not explain, do not add punctuation, do not output anything else. 
        Your output must be either CONTINUE or END only. 
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        self.llm = prompt | llm  # Chain with the tool-bound LLM

    def __call__(self, state):
        start_time = time.time()

        print("[INFO] Running UserChecking node")

        # Extract last user message
        # print(f"Assistant: Are there anything else?")
        # speak("Are there anything else?")
        # user_message = input("User: ")
        user_message = listen()

        return_dict = {}
        try:
            # Pass the message to the LLM (system prompt is already baked into self.llm)
            result = self.llm.invoke(
                {
                    "input": user_message,
                    "history": []
                }
            ).content
            print(f"\t[INFO] User input type: {type(result)}")
            decision = result.strip()
            _, decision = extract_thought_and_speech(decision)
            decision = decision.strip().upper()
            print(f"\t[DEBUG] Decision: {decision}")

            print(f"\t[INFO] Elapse time: {time.time() - start_time}")

            if decision == "CONTINUE":
                return_dict['isContinue'] = True

                # return_dict["messages"] = state["messages"] + [AIMessage(content="Are there anything else?"), HumanMessage(content=user_message)]
                return_dict["messages"] = state["messages"] + [HumanMessage(content=user_message)]
            elif decision == "END":
                return_dict["isContinue"] = False

            else:
                print(f"[WARN] Unexpected classification: {decision}, defaulting to chat.")
                return_dict["isContinue"] = False

        except Exception as e:
            print(f"[ERROR] Failed to classify message: {e}")
            return_dict["isContinue"] = False

        return return_dict


# === Is continue routing ===
class IsContinueRouter:
    def __init__(self):
        pass


    def __call__(self, state):
        if state["isContinue"]:
            return "continue"
        else:
            return "saving conversation"
