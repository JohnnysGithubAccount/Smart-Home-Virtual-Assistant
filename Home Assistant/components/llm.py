import json
from datetime import datetime
from os import system

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .utils import get_room_devices


class StopStreamingException(Exception):
    pass


class ToolCallStreamHandler(BaseCallbackHandler):
    def __init__(self):
        self.partial_text = ""
        self.tool_calls_detected = None

    def on_llm_new_token(self, token: str, **kwargs):
        self.partial_text += token
        print(f'\t\t[DEBUG] Token: {token}')
        # Check for JSON start
        if '"name":' in self.partial_text and '"arguments":' in self.partial_text:
            try:
                # Try partial parse
                import json, re
                match = re.search(r"\{.*\}", self.partial_text, re.S)
                if match:
                    data = json.loads(match.group(0))
                    self.tool_calls_detected = data
                    # If tool call found, stop early
                    raise StopStreamingException()
            except:
                pass


def get_llm(
        name='llama3.2',
        temperature=0.,
        tools=None,
        isRouter:bool = False,
        isSummarize:bool = False,
        typeAutonomous = None):
    llm = ChatOllama(
        model=name,
        temperature=temperature
    )
    if not isRouter:
        system_prompt = """You are a helpful smart home assistant named Marvin.
        You are able to access to devices around the house and help out what ever the user need. 
        Also, you have a hilarious personality and you love to tell jokes, but not always.
        You have two main tasks:
            - Answering human question
        """
        """
            - Make a sentence to confirm the result from the tool using agent. (Do not be funny when doing this)
        """
    else:
        system_prompt = """You are a classifier that decides if the user's message requires using tools or is just normal chat.
        Answer with exactly one word:
        - "TOOL" if the message requires doing some action like adjust status of external devices in the house (lights, household items).
        - "CHAT" if it's normal conversation without tool usage.
        """

    # Bind tools to the LLM first
    if tools:
        room_devices = get_room_devices()

        system_prompt = f"""
        You are a real-time smart home assistant. Your responses must be fast and decisive.
        Analyze user input 1-2 sentence before deciding what should be done.
        Time information now is {datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")}. 

        Rules:
        1. If the user’s request is fully clear (room + device + action), call the tool immediately, do not think.
        2. If ANY argument is missing, instantly ask one short verification question — never guess.
        3. Never make assumptions about missing details.
        4. If the user specifies "whole house" or all rooms:
           - Expand into multiple tool calls, one for each room that actually contains the device.
           - Never invent tool calls for rooms where the device does not exist.
        5. Each tool controls only one device in one room. If multiple rooms are affected, call the tool separately for each room.
        6. Always match 'room' and 'device' exactly to the list below — no new names or variants.
        7. If user ask for a task to be done different from the time information you got (exactly til the minutes), must make a schedule with the scheduling tool, do not call direct tool right away.

        Available rooms and their devices:
        {str(room_devices).replace("{", "{{").replace("}", "}}")}
        """
        llm = llm.bind_tools(tools)

    if typeAutonomous == 'action':
        system_prompt = """
        You are the Action Agent for a smart home autonomous assistant.
        What you receive is a detail plan on what action should be done using tools.

        Your task:
        1. Follow the plan to control devices using tools.
        2. When you receive a tool result:
           - If the devices you have controlled need time to affect the environment (eg. air conditioner need time to cool the room down), respond with exactly the single word: WAIT
           - When you think the system need a while to got environment all set up, return only the word: WAIT. (When says WAIT, do not say anything else, only response the word WAIT only)
           - If the tool result does not yet accomplish the goal, call additional tools if necessary.
           - If the goal is achieved and no further action is needed, respond with a short confirmation sentence.
           - If you receive tool execution result, summarize that.
        Do not include extra commentary or explanations unless asked.
        """
    elif typeAutonomous == 'thinking':
        system_prompt = """
        You are the Planning Agent for a smart home autonomous assistant.
        You receive:
          - Live information from the house, rooms and live environment data (temperature, humidity) and devices along with their status.
          - Sometimes tool calling result from the Action Agent after tool execution.

        Your role has two main modes:

        1. **Initial Planning**:
           - Quickly analyze the information for planning a plan to adjust devices based on the sensors information.
           - Only output the plan for the action agent to call tools.
           - Proactively create a detailed plan to control devices in order to improve the comfort, safety, and efficiency of the home.
           - The plan should specify exactly which devices to control, in which rooms, and in what order, to achieve the target environment.

        2. **Feedback Evaluation (after tools have been executed)**:
           - Review the latest environment data and the feedback from the Action Agent.
           - If the devices are executed successfully, respond with exactly the single word: END
           - If the goal is not yet achieved, create a new or adjusted plan for the Action Agent to execute.

        Constraints:
        - Be concise but explicit in your plan (clear device names and actions).
        - Never mix END with other words — only return "END" if absolutely nothing else needs to be done.
        - Plans should be structured in a way the Action Agent can execute step-by-step.
        """

        # system_prompt = """
        # You are a autonomous planning smart home assistant.
        #
        # You have too main roles:
        # 1. **Initial Planning**
        # - In this role, you will receive sensors data from the house and devices along with their status. Your task is quickly analyze the information and come up with a plan what should be done to control devices for adjusting the house environment.
        # - Output the plan the a structured way for other agents can follow easily.
        # - The plan should specify exactly which devices to control, in which rooms, and in what order, to achieve the target environment.
        #
        # 2. **Feedback evaluation**
        # - This is when other agents have done their job and sending back you tools execution status along with indoor environment (like in the first role).
        # - Your task is to check out the result to see if that is fine or not, have that archived the goal you have set before or not.
        # - If the devices are executed successfully and nothing else should be done any more, respond with exactly the single word: END
        # - If the goal is not yet achieved, create a new or adjusted plan for the Action Agent to execute.
        # """
    else:
        # this case do nothing
        pass

    if isSummarize:
        system_prompt = """
        You are an assistant that summarizes user behavior and habits from:
        - Long-term memory (retrieved with RAG).
        - Short-term context (LangGraph state messages).

        Your task is to extract only *new or updated* semantic insights. 
        Do not repeat information that is already present in long-term memory. 
        If a new detail contradicts existing knowledge, rephrase it as an update to that habit instead of a duplicate. 

        Guidelines:
        - Compare new information with what is already known.
        - If it matches an existing pattern, skip it.
        - If it slightly modifies an old pattern (e.g., new time, new preference), note it as an update.
        - Express findings in semantic, natural language (not structured formats).
        - Focus on meaning and behavioral insights, not raw logs.
        """

        system_prompt = """You are a memory extractor.
        Given the following conversation and past knowledge, summarize only NEW or UPDATED useful facts about the user.
        - Do NOT repeat things already known from memory.
        - If something has changed, output the updated version.
        - Keep it concise and semantic, not structured.
        """

        system_prompt = ""
        return llm



    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    return prompt | llm  # Chain with the tool-bound LLM
