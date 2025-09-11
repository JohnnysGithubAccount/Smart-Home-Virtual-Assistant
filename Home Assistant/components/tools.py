import os
from datetime import datetime

import requests
from typing import Dict
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from typing import List
from typing import Optional
from langgraph.types import Command, interrupt
from .voice.text_to_speech import speak
from .voice.speech_to_text import listen
from .utils import load_configs
from langchain_core.tools import tool
import sqlite3, json
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil import parser  # More flexible date parsing
import requests


# === Configs ===
configs = load_configs("../Home Assistant/configs.json")

# ==========================================================================
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

    # human_input = input("User: ")
    human_input = listen()
    # human_input = "the whole house"
    print(f"User: {human_input}")

    return {
        # "original_intention": user_intention,
        "question": what_to_ask,
        "human_response": human_input
    }


# ==========================================================================
# COMMON TOOLS

@tool
def get_current_date_time() -> str:
    """Get the current date, time, and weekday as a string."""
    return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")


os.environ["TAVILY_API_KEY"] = "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"
search_tool = TavilySearch(max_results=2)

# ==========================================================================
# SMART HOME TOOLS
BASE_URL = configs["firebase"]

@tool
def get_sensor_information(room: str) -> dict:
    """Get real-time sensor data (temperature, humidity) from a specific room.

    Args:
        room (str): The room you expect to get information from.
    """
    url = f"{BASE_URL}/test/{room}/sensors.json"
    url = f"{BASE_URL}/{room}/sensors.json"
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
    try:
        url = f"{BASE_URL}/test/{room}/device.json"
        url = f"{BASE_URL}/{room}/device.json"
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
    except Exception as e:
        print(f"[ERROR] Function name: control_lights")
        print(f"[ERROR] Error: {e}")
        return {
            "status": "error",
            "message": e
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
         target_temp (int): temperature which user expect to archive from the heater. Or 0 if you want it to be turned off
         room (str): the room you want to control the heater
    """
    room = room.strip().replace(' ', "_")
    return update_device(room, "heater", target_temp)

# ==========================================================================
# SCHEDULE TASKS

scheduler = BackgroundScheduler()
scheduler.start()

tool_registry = [
    control_lights,  # Control lights
    control_heater,  # Control the heater
    control_air_conditioner,  # Control the air conditioner
    control_humidifier,  # Control the humidifier
    control_lamp,  # Control the lamp
    control_stove,  # Control the stove
    control_oven,  # Control the oven
]

tool_registry_names = [func.name for func in tool_registry]

tool_registry_dict = dict(zip(tool_registry_names, tool_registry))


def invoke_tool(tool_warped, args):
    return tool_warped.invoke(args)


@tool
def schedule_tool_call(tool_name: str, arguments: dict, run_date: str, repeat_type: str):
    """
    Schedule a tool function to run at a specific time, either once or on a recurring basis.

    This function allows the AI agent to register a future task using one of the available smart home tools.
    It supports both single execution and daily repetition. The scheduled job will be managed by APScheduler
    and executed with the provided arguments at the designated time.

    Parameters:
        tool_name (str): The name of the tool function to execute. Must match a key in the tools' registry.
        arguments (dict): A dictionary of keyword arguments to pass to the tool function when it runs.
        run_date (str): The time to run the task, in ISO 8601 format (e.g. "2025-08-27T19:30:00").
        repeat_type (str): The repetition mode. Supported values:
            - "single": Run once at the specified time.
            - "daily": Run every day at the same time.

    Example Usage:
        "Turn on the bedroom lights every day at 19:30"
        schedule_tool_call(
            function_name="control_lights",
            arguments={"room": "bedroom", status: "on"},
            run_date="2025-08-27T19:30:00",
            repeat_type="daily"
        )
    """

    func = tool_registry_dict[tool_name]
    run_time = parser.parse(run_date)

    job_id = f"{tool_name}_{run_time.strftime('%Y%m%d%H%M%S')}_{arguments}"

    if repeat_type == "single":
        scheduler.add_job(
            invoke_tool,
            trigger='date',
            run_date=run_time,
            args=[func, arguments],
            id=job_id,
            name=tool_name
        )
    elif repeat_type == "daily":
        scheduler.add_job(
            invoke_tool,
            trigger='cron',
            hour=run_time.hour,
            minute=run_time.minute,
            args=[func, arguments],
            id=job_id,
            name=tool_name
        )
    else:
        return {"status": "failed", "message": f"Failed to set the schedule due to some formating error"}

    print(f"\t[DEBUG]Scheduled '{tool_name}' with repeat_type '{repeat_type}' at {run_time}")

    return {'status': "success", "message": "set schedule task"}


# === Tools ===
tools = [
    human_assistance,  # Human in the loop
    # check_if_user_needs_anything_else,  # Check if user needs anything else before ending
    get_sensor_information,  # Get sensors information (temperature, humidity)
    schedule_tool_call,
    # search_tool,
    # get_current_date_time,

    control_lights,  # Control lights
    control_heater,  # Control the heater
    control_air_conditioner,  # Control the air conditioner
    control_humidifier,  # Control the humidifier
    control_lamp,  # Control the lamp
    control_stove,  # Control the stove
    control_oven,  # Control the oven
]

tool_names = [func.name for func in tools]

chat_tools = [
    human_assistance,
    get_current_date_time,
    search_tool
    # web_search
]

chat_tool_names = [func.name for func in chat_tools]