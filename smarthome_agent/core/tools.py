from langchain.tools import tool

@tool
def turn_on_lights(room: str):
    """Turns on the lights in the specified room."""
    print(f"💡 Lights turned ON in {room}.")
    return f"Lights in {room} turned on."

@tool
def turn_off_lights(room: str):
    """Turns off the lights in the specified room."""
    print(f"💡 Lights turned OFF in {room}.")
    return f"Lights in {room} turned off."

@tool
def set_temperature(value: float):
    """Sets the home temperature to a specific value."""
    print(f"🌡️ Temperature set to {value}°C.")
    return f"Temperature set to {value}°C."

@tool
def play_music(song: str):
    """Plays a specific song."""
    print(f"🎵 Now playing: {song}")
    return f"Playing {song}."

@tool
def shutdown_house():
    """Shuts down all devices and activates security mode."""
    print("🔒 House shutdown initiated.")
    return "House is now in security shutdown mode."
