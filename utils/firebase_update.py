import json
import requests

FIREBASE_URL = 'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app'


def update_device(room, device, status):
    try:
        # Convert the data to JSON format
        data = {
            device: status
        }
        json_data = json.dumps(data)
        curr_url = f"{FIREBASE_URL}{f'/{room}.json'}"
        print(curr_url)
        response = requests.put(curr_url, data=json_data)


        print("Response Code:", response.status_code)
        print("Response Text:", response.text)

        response_dct = eval(response.text)
        for key, value in response_dct.items():
            response_dct[key] = "on" if value == 1 else "off"

        response_dct["room"] = room
        # json.dumps(response_json)
        return json.dumps(response_dct)
    except Exception as e:
        print("Error sending data:", e)
        return {"error": str(e), "room": room}


def fetch_data(status):
    if status == "both":
        fields = [
            "temperature",
            "humidity"
        ]
        urls = [
            'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/temperature.json',
            'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/humidity.json'
        ]
    else:
        fields = [
            status
        ]
        urls = [
            f'https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/{status}.json'
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
            responses["error"] = f"Error fetching data from {urls}: {e}"

    return json.dumps(responses)


def main():
    room = 'living_room'
    data_to_send = {'fan': 1}
    json_response = update_device(room, 'light', 1)  # To send data
    print(json_response)
    data = fetch_data(status="temperature")
    print("Fetched Data:", data)


if __name__ == "__main__":
    main()
