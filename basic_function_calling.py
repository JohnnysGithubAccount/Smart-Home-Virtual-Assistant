import json
import requests
from transformers import pipeline

FIREBASE_URL = 'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app'

def update_device(data, room=""):
    try:
        # Convert the data to JSON format
        json_data = json.dumps(data)
        curr_url = f"{FIREBASE_URL}{f'/{room}.json'}"
        response = requests.put(curr_url, data=json_data)

        print("Response Code:", response.status_code)
        print("Response Text:", response.text)

    except Exception as e:
        print("Error sending data:", e)

def fetch_data(fields):
    responses = {}
    for field in fields:
        url = f"{FIREBASE_URL}{f'/{field}.json'}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                responses[field] = response.json()
            else:
                print(f"Error fetching data from {field}, Response Code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching data from {url}: {e}")
    return responses

# Hugging Face model for function calling
def virtual_assistant(query):
    # Basic command parsing
    if "update" in query:
        # Extract data and room from the query (this is simplified)
        # Example: "update temperature to 25 in living room"
        parts = query.split()
        room = parts[-1]  # Last word as room
        value = int(parts[2])  # Assuming the value is the third word
        data = {"value": value}
        update_device(data, room)
        return f"Updated {room} to {value}."

    elif "fetch" in query:
        # Example: "fetch temperature and humidity"
        fields = [field.strip() for field in query.split("and")]
        data = fetch_data(fields)
        return data

    else:
        return "I can only update or fetch data."

# Example usage
if __name__ == "__main__":
    # Initialize the Hugging Face pipeline (this is just a placeholder)
    assistant = pipeline("text2text-generation", model="facebook/bart-large-cnn")

    # Simulated user queries
    user_queries = [
        "update temperature to 25 in living room",
        "fetch temperature and humidity"
    ]

    for query in user_queries:
        response = virtual_assistant(query)
        print("Assistant:", response)