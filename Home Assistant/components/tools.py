import requests
from typing import Dict
from langchain_core.tools import tool
from typing import List
from typing import Optional
from langgraph.types import Command, interrupt
from .voice.text_to_speech import speak
from .voice.speech_recognition import listen
from .utils import load_configs
from langchain_core.tools import tool
import sqlite3, json


# === Configs ===
configs = load_configs("../Home Assistant/configs.json")

# =========================================================================+
# ASSISTANT TOOLS
@tool
def human_assistance(
        what_to_ask: str,
        # user_intention: str
) -> Dict:
    """
    Ask the human a question the clear anything for needed additional data.

    Example:
        user: turn off the lights
        human_assistance(what_to_ask="Which room would you expect me to turn off the lights or just everything?")

    Args:
        what_to_ask (str): The exact question to ask the user.
    """

    print(f"[CURIOSITY] Assistant: {what_to_ask}")
    speak(what_to_ask)

    human_input = input("User: ")
    # human_input = listen()
    # human_input = "the whole house"
    print(f"User: {human_input}")

    return {
        # "original_intention": user_intention,
        "question": what_to_ask,
        "human_response": human_input
    }

@tool
def check_if_user_needs_anything_else(question):
    """
    Check with user if there are anything else to do, just to make sure.

    Args:
        question: the question you want to ask user to make sure there are nothing else user want you to do
    """
    print(f"[CHECKING] Assistant: {question}")
    speak(question)
    # human_input = listen()
    human_input = input("User:")
    return {
        "question": question,
        "human_response": human_input
    }

# =========================================================================+
# SMART HOME TOOLS
# BASE_URL = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app"
BASE_URL = configs["firebase"]

@tool
def get_sensor_information(room: str) -> dict:
    """Get real-time sensor data (temperature, humidity) from a specific room.

    Args:
        room (str): The room you expect to get information from.
    """
    url = f"{BASE_URL}/test/{room}/sensors.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data and "temperature" in data and "humidity" in data:
            return {
                "temperature": data["temperature"],
                "humidity": data["humidity"]
            }
        else:
            return {"error": f"No sensor data found in '{room}'."}
    else:
        return {"error": f"Failed to fetch data: {response.status_code}", "details": response.text}


def update_device(room: str, device: str, value) -> Dict:
    url = f"{BASE_URL}/test/{room}/device.json"
    payload = {device: value}
    response = requests.patch(url, json=payload)
    if response.status_code == 200:
        return {
            "status": "success",
            "room": room,
            "device": device,
            "new_value": value
        }
    else:
        return {
            "status": "error",
            "code": response.status_code,
            "message": response.text
        }


@tool
def control_humidifier(target_percentage: int, room: str) -> dict:
    """Control humidifier in a specific room.

    Args:
        target_percentage (int): Target humidity percentage to set (0–100).
        room (str): The room in which to control the humidifier.
    """
    room = room.strip().replace(' ', "_")
    return update_device(room, "humidifier", target_percentage)


@tool
def control_lamp(strength: int, room: str) -> dict:
    """Control lamp brightness in a specific room.

    Args:
        strength (int): Brightness level from 0 to 100.
        room (str): The room in which to control the lamp.
    """
    room = room.strip().replace(' ', "_")
    return update_device(room, "lamp", strength)


@tool
def control_stove(turn_on: str) -> dict:
    """Turn stove on or off in the kitchen.

    Args:
        turn_on (str): Either 'on' or 'off'
    """
    return update_device('kitchen', "stove", turn_on)


@tool
def control_oven(turn_on: str) -> dict:
    """Turn oven on or off in the kitchen.

    Args:
        turn_on (str): Either 'on' or 'off'
    """
    return update_device('kitchen', "oven", turn_on)


@tool
def control_lights(room: str, status: str) -> dict:
    """Control light in a specific room

    Args:
        room (str): the room the user want to control the light.
        status (str): Either 'on' or 'off'
    """
    room = room.strip().replace(' ', "_")
    return update_device(room, "lights", status)


@tool
def control_air_conditioner(target_temp: int, room: str):
    """Control air conditioner in a specific room

    Args:
        target_temp (int): the temperature will be set for the air conditioner
        room (str): the room you want to control the air conditioner
    """
    room = room.strip().replace(' ', "_")
    return update_device(room, "air_conditioner", target_temp)


@tool
def control_heater(target_temp: int, room: str):
    """Control heater in a specific room

    Args:
         target_temp (int): temperature which user expect to archive from the heater.
         room (str): the room you want to control the heater
    """
    room = room.strip().replace(' ', "_")
    return update_device(room, "heater", target_temp)

# =========================================================================+
# ADVANCE TOOLS

DB_PATH = "schedules.db"

# simple sqlite storage
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS schedules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tool_name TEXT,
                  args TEXT,
                  time TEXT,
                  repeat TEXT)''')
    conn.commit()
    conn.close()


from datetime import datetime, timedelta



# === This is the function your model can call ===
@tool
def make_schedule_tool_call(
    tool_name: str,
    args: dict,
    time: str,
    repeat: str = "once",
    duration: str = None,
    end_time: str = None
) -> str:
    """
    Create a schedule for a tool call.

    Args:
        tool_name (str): Name of the tool to call (e.g., 'control_lights').
        args (dict): Arguments for the tool (e.g., {"room": "kitchen", "status": "on"}).
        time (str): When to start (e.g., '19:00', '2025-08-20T18:00:00', 'every 30m').
        repeat (str, optional): "once", "daily", "weekly", or "periodic". Defaults to "once".
        duration (str, optional): Duration to keep the tool active (e.g., "1h", "30m").
        end_time (str, optional): When to stop repeating (absolute time or "after 1h").

    Returns:
        str: A JSON string representing the schedule.
    """

    schedule = {
        "scheduled": True,
        "tool": tool_name,
        "args": args,
        "time": time,
        "repeat": repeat,
    }

    if duration:
        schedule["duration"] = duration
    if end_time:
        schedule["end_time"] = end_time

    return json.dumps(schedule, indent=2)


# === Tools ===
tools = [
    human_assistance,  # Human in the loop
    # check_if_user_needs_anything_else,  # Check if user needs anything else before ending

    control_lights,  # Control lights
    control_heater,  # Control the heater
    control_air_conditioner,  # Control the air conditioner
    control_humidifier,  # Control the humidifier
    control_lamp,  # Control the lamp
    control_stove,  # Control the stove
    control_oven,  # Control the oven
    get_sensor_information,  # Get sensors information (temperature, humidity)
]

tool_names = [func.name for func in tools]
