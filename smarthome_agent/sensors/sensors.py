import random

def get_sensor_data():
    return {
        "temperature": round(random.uniform(18, 35), 1),
        "humidity": round(random.uniform(30, 80), 1),
        "presence": random.choice([True, False])
    }
