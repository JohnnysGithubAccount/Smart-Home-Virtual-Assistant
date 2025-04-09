import json
import requests

FIREBASE_URL = 'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app'


def update_device(data, room=""):
    try:
        # Convert the data to JSON format
        json_data = json.dumps(data)
        curr_url = f"{FIREBASE_URL}{f'/{room}.json'}"
        print(curr_url)
        response = requests.put(curr_url, data=json_data)


        print("Response Code:", response.status_code)
        print("Response Text:", response.text)

    except Exception as e:
        print("Error sending data:", e)


def fetch_data(fields):
    urls = [
        'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/temperature.json',
        'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/humidity.json'
    ]

    responses = {}

    for field in fields:
        url = f"{FIREBASE_URL}{f'/{field}.json'}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                responses[field] = response.json()  # Store the JSON response
            else:
                print(f"Error fetching data from {field}, Response Code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching data from {urls}: {e}")

    return responses


def main():
    room = 'living_room'
    data_to_send = {'fan': 1}
    update_device(data_to_send, room)  # To send data
    data = fetch_data(
        fields=[
            "temperature",
            "humidity"
        ]
    )
    print("Fetched Data:", data)


if __name__ == "__main__":
    main()
