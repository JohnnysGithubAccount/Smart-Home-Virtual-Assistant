from core.memory import add_schedule
from datetime import datetime

def plan_home_arrival(time_str: str):
    """Schedule home prep before arrival time."""
    add_schedule("Prepare home", time_str)
    return f"Home will be ready before {time_str}."
