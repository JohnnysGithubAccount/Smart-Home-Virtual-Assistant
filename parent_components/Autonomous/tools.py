import requests
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal, Optional, Dict
import time
from utils import State
from langchain_core.tools import tool
from typing import List
from langgraph.types import Command, interrupt


@tool
def validate_user(user_id: int, addresses: List[str]) -> bool:
    """Validate user using historical addresses.

    Args:
        user_id (int): the user ID.
        addresses (List[str]): Previous addresses as a list of strings.
    """
    return True




@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]

# =========================================================================+
# SMART HOME TOOLS
BASE_URL = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app"


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
    return update_device(room, "humidifier", target_percentage)

@tool
def control_lamp(strength: int, room: str) -> dict:
    """Control lamp brightness in a specific room.

    Args:
        strength (int): Brightness level from 0 to 100.
        room (str): The room in which to control the lamp.
    """
    return update_device(room, "lamp", strength)

@tool
def control_stove(turn_on: str, room: str) -> dict:
    """Turn stove on or off in the kitchen.

    Args:
        turn_on (str): Either 'on' or 'off'
        room (str): Room in which the stove is located (typically "kitchen").
    """
    return update_device(room, "stove", turn_on)

@tool
def control_lights(room: str, status: str) -> dict:
    """Control light in a specific room

    Args:
        room (str): the room the user want to control the light.
        status (str): Either 'on' or 'off'
    """
    return update_device(room, "lights", status)


@tool
def control_air_conditioner(target_temp: int, room: str):
    """Control air conditioner in a specific room

    Args:
        target_temp (int): the temperature will be set for the air conditioner
        room (str): the room you want to control the air conditioner
    """
    return update_device(room, "air_conditioner", target_temp)


@tool
def control_heater(target_temp: int, room: str):
    """Control heater in a specific room

    Args:
         target_temp (int): temperature which user expect to archive from the heater.
         room (str): the room you want to control the heater
    """
    return update_device(room, "heater", target_temp)


tools = [
    control_lights,
    control_heater,
    control_air_conditioner,
    control_humidifier,
    control_lamp,
    control_stove,
    # validate_user,
    # get_sensor_information,
    # human_assistance,
]

tool_names = [func.name for func in tools]