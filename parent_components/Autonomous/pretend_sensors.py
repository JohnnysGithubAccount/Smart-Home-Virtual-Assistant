import requests
import time
import random
from tqdm import tqdm

# Constants
FIREBASE_URL = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app"
ROOMS = ["bedroom", "kitchen", "living_room"]

def get_data(path):
    """GET data from Firebase."""
    url = f"{FIREBASE_URL}/{path}.json"
    res = requests.get(url)
    return res.json()

def update_data(path, data):
    """PATCH data to Firebase."""
    url = f"{FIREBASE_URL}/{path}.json"
    requests.patch(url, json=data)

def clamp(value, min_val=0, max_val=100):
    return max(min_val, min(max_val, round(value, 1)))

def simulate_room(room):
    device_path = f"test/{room}/device"
    sensor_path = f"test/{room}/sensors"

    devices = get_data(device_path)
    if not devices:
        print(f"No devices found for room: {room}")
        return

    # Base levels
    temperature = 25 + random.uniform(-0.5, 0.5)  # small baseline variation
    humidity = 50 + random.uniform(-1, 1)

    # Adjust temperature
    temperature += devices.get("heater", 0) * (0.05 + random.uniform(-0.01, 0.01))
    temperature -= devices.get("air_conditioner", 0) * (0.07 + random.uniform(-0.015, 0.015))
    temperature -= devices.get("air_conditioner2", 0) * (0.07 + random.uniform(-0.015, 0.015))

    # Adjust humidity
    humidity += devices.get("humidifier", 0) * (0.1 + random.uniform(-0.02, 0.02))

    # Kitchen cooking effect
    if room == "kitchen":
        if devices.get("oven") == "on":
            humidity += 10 + random.uniform(-1, 1)
        if devices.get("stove") == "on":
            humidity += 5 + random.uniform(-0.5, 0.5)

    # Clamp and update
    updated = {
        "temperature": clamp(temperature),
        "humidity": clamp(humidity)
    }
    update_data(sensor_path, updated)
    print(f"[{room}] Updated sensors: {updated}")

def simulate_all_rooms():
    for room in ROOMS:
        simulate_room(room)

# Repeat loop
if __name__ == "__main__":
    while True:
        simulate_all_rooms()
        for _ in tqdm(range(30)):
            time.sleep(1)
