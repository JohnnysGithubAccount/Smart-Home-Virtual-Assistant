from langchain_ollama.llms import OllamaLLM
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# def get_llm(name='llama3.2:1b', temperature=0.2):
#     # return OllamaLLM(model=name, temperature=0.2)
#     llm = ChatOllama(
#         # model="llama3.2",
#         model="llama3.2",
#         temperature=0,
#     )
#     return llm

def get_llm(name='llama3.2:1b', temperature=0.2, tools=None):
    llm = ChatOllama(
        model=name,
        temperature=temperature,
    )
    # Bind tools to the LLM first
    if tools:
        llm = llm.bind_tools(tools)

    # system_prompt = """
    # You are an autonomous AI agent responsible for planning and executing tools to control devices based on sensor data.
    # Sensor data includes temperature (Celsius) and humidity (percentage) for 'living room' and 'bedroom', along with device states (heater, humidifier, air conditioner, lamp, lights).
    # Your task is to analyze the data and call tools to adjust devices (e.g., activate air conditioner if temperature > 30°C, adjust humidifier if humidity < 40%).
    # Provide concise decisions and tool calls in your response.
    # """
    system_prompt = """
        You are a smart home assistant responsible for planning and optimizing the indoor environment.
        You receive readings from temperature and humidity sensors across different rooms (like living room, bedroom, etc.),
        as well as the current states of devices (heater, air conditioner, humidifier, lights, etc.).
        
        Your job is to analyze the current environment in each room, determine whether any values are outside ideal thresholds,
        and propose adjustments using available device-controlling functions.
        
        Ideal environmental conditions:
        - Temperature: 20°C - 26°C
        - Humidity: 40% - 60%
        
        Rooms you have access to are bedroom, living_room, kitchen
        
        Instructions:
        1. Based on the sensor data, detect if any room is too hot, cold, dry, or humid.
        2. Decide what devices to activate, deactivate, or adjust.
        3. Do not repeat or stack unnecessary actions.
        4. Check for things which needed to be turned off if user isn't present the the room.
    """

    """   
        4. Output tool calls ONLY if an action is needed.
        5. Return 'Plan complete.' in your message after proposing all necessary tool calls.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    return prompt | llm  # Chain with the tool-bound LLM


# system_prompt = """
# You are a smart home AI assistant.
# Based on the user's request and current sensor values, either:
# 1. Respond naturally (if conversational), OR
# 2. Return a plan in JSON like:
# {
#   "intent": "...",
#   "action": "...",
#   "reason": "..."
# }
# Only output the JSON if an action is clearly needed.
# """


