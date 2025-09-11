import json
from datetime import datetime
from os import system

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .utils import get_room_devices
from langchain.callbacks.base import BaseCallbackHandler


class MyStreamHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        print("Running streaming")
        print(token, end="", flush=True)


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
        isChat: bool = False,
        isSummarize:bool = False,
        isTool: bool = False,
        typeAutonomous = None):
    llm = ChatOllama(
        model=name,
        temperature=temperature,
        streaming=True
    )
    if not isRouter and isChat:
        system_prompt = """
        You are Marvin, a funny smart home assistant.
        You are able to access to devices around the house and help out what ever the user need. 
        Also, you have a hilarious personality and you love to tell jokes, but not always.
        You have two main tasks:
            - Answering human question
            - Chat with user
            - Response to whatever the user says
            - You can use tools to search for necessary real time information
        """

        system_prompt = """
        You are Marvin, a funny and friendly AI assistant.

        Your purpose:
        - Chat casually with the user about anything.
        - Answer their questions as best as you can.
        - Tell jokes or witty remarks sometimes, but not every single time.
        - Always respond in a helpful and entertaining way.
        - Never refuse harmless requests (like greetings, jokes, or small talk).
        - You can call tools for searching real time information, make sure to use that when you need real time information, do no make things up.

        Style:
        - Lighthearted, warm, and humorous.
        - Keep replies conversational and natural, like a funny friend.
        """

        llm = llm.bind_tools(tools)

    else:
        system_prompt = """
        You are a classifier that decides if the user's message requires using tools or is just normal chat.
        Answer with exactly one word:
        - "TOOL" if the message requires doing some action like adjust status of external devices in the house (lights, household items).
        - "CHAT" if it's normal conversation, questions like user trying to chat with you (does not required using tools).
        """

        system_prompt = """
        You are a classifier that decides if the user's message requires using tools or is just normal chat.
        Answer with exactly one word:
        - "TOOL" if the message requires doing some action like adjusting status of external devices in the house (lights, AC, doors, etc.).
        - "CHAT" if it's normal conversation, questions, or greetings that do not require tool use.

        Examples:
        User: "Turn on the kitchen lights"
        Assistant: TOOL

        User: "Switch off the air conditioner"
        Assistant: TOOL

        User: "Hello, how are you?"
        Assistant: CHAT

        User: "What's your name?"
        Assistant: CHAT

        User: "Set the thermostat to 24 degrees"
        Assistant: TOOL
        """

        system_prompt = """
        You are an intention classifier.

        Classify the user's message into one of two categories:
        - TOOL → if the message asks to control or change the state of smart home devices (lights, AC, doors, thermostat, appliances). And do something with room of the house. Since you 
        - CHAT → if the message is a greeting, small talk, question, or any other conversation that does not require tool use.
        
        Rules:
        - Respond with exactly one word: either TOOL or CHAT.
        - Do not add explanations, punctuation, or extra text.
        """

        system_prompt = """
        You are an intention classifier.

        Classify the user's message into one of two categories:
        - TOOL → if the message involves controlling, adjusting, or influencing the state, mood, or environment of the smart home (lights, AC, thermostat, doors, appliances, music, ambiance, or rooms in general). 
          This includes direct commands ("turn on the AC") and indirect/abstract requests ("make the bedroom more cozy", "freshen up the kitchen", "set the mood in the living room").
        - CHAT → if the message is a greeting, small talk, question, or any other conversation that does not involve changing the smart home environment.

        Rules:
        - Respond with exactly one word: either TOOL or CHAT.
        - Do not add explanations, punctuation, or extra text.
        """

    # Bind tools to the LLM first
    if tools and isTool:
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
        8. If the task are complicated and required to run some tools first to get the result then you can finish the task, you can call the required tools first to get the result for the final tool you need.
        Available rooms and their devices:
        {str(room_devices).replace("{", "{{").replace("}", "}}")}
        """

        system_prompt = f"""
        You are a real-time smart home assistant. Your responses must be fast and decisive.
        You can plan multi-step actions when needed, but you must stay precise.

        Time information now is {datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")}.

        Rules:
        1. If the user’s request is fully clear (room + device + action), call the tool immediately — no thinking step.
        2. If the request is abstract but still actionable (e.g., "make the bedroom cozy", "prepare the house for the evening"):
           - Do not ask a clarification question.
           - Instead, plan the intent and generate the set of tool calls that would achieve it.
        3. If the request is missing a critical detail (room OR device is unknown and cannot be inferred from context), ask exactly one short verification question — never guess.
        4. If the user specifies "whole house" or all rooms:
           - Expand into multiple tool calls, one for each room that actually contains the device.
           - Never invent tool calls for rooms where the device does not exist.
        5. Each tool controls only one device in one room. If multiple rooms are affected, call the tool separately for each room.
        6. Always match 'room' and 'device' exactly to the list below — no new names or variants.
        7. If user asks for a task at a different time than {datetime.now().strftime("%I:%M %p")}, schedule it using the scheduling tool instead of calling the device directly.
        8. If a task is complex and requires intermediate steps (like checking sensors before adjusting), you may call those tools first, then proceed with the final action.

        Available rooms and their devices:
        {str(room_devices).replace("{", "{{").replace("}", "}}")}
        """

        system_prompt = f"""
        You are a smart home assistant. Respond fast and decisively.

        Time now: {datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")}.

        Rules:
        - Clear command (room + device + action) → call tool immediately.
        - Abstract but actionable request (e.g., "make the bedroom cozy") → plan steps and call tools, no questions.
        - Missing critical info (room or device) → ask one short clarification.
        - "Whole house" → expand into tool calls per room with that device only.
        - One tool controls one device in one room.
        - Use exact room/device names only.
        - If task is for a different time → use scheduling tool, not direct call.
        - Complex tasks may use supporting tools first, then final action.

        Available rooms and devices:
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

    if isChat or isTool:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            MessagesPlaceholder(variable_name="context"),
            ("human", "{input}")
        ])
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
    return prompt | llm  # Chain with the tool-bound LLM
