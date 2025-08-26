import requests

class Sensors:
    def __call__(self, state: dict):
        print(f'[INFO] Running Sensors node')
        sensors =  {
            'living_room': {
                'sensors': {
                    'temperature': 100, # Celsius
                    'humidity': 100 # Percentage
                },
                'device': {
                    'heater': 70, # degree in Celsius
                    'humidifier': 50, # percentage
                    'air conditioner': 17, # degree in Celsius
                    'lamp': 50, # strength (0-100)
                    'lights': True, # True means on and False means off
                }
            },
            'bedroom': {
                'sensors': {
                    'temperature': 50, # Celsius
                    'humidity': 50 # Percentage
                },
                'device': {
                    'heater': 20, # degree in Celsius
                    'humidifier': 100, # percentage
                    'air conditioner': 26, # degree in Celsius
                    'lamp': 100, # strength (0-100)
                    'lights': False, # True means on and False means off
                }
            },
            'kitchen': {
                'sensors': {
                    'temperature': 20,  # Celsius
                    'humidity': 90  # Percentage
                },
                'device': {
                    'stove': False,  # True means on and False means off
                    'humidifier': 0,  # percentage
                    'air conditioner': 0,  # degree in Celsius
                    'lamp': 0,  # strength (0-100)
                    'lights': False,  # True means on and False means off
                }
            },
        }

        # Base URL (ending in .json to get the data)
        url = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/test.json"

        # GET request
        response = requests.get(url)

        # Check response
        if response.status_code == 200:
            data = response.json()  # This is now a Python dict
            print("Data fetched successfully:")
            print(data)
        else:
            print(f"Error fetching data: {response.status_code}")

        return data


def pretty_print(data, indent=0):
    prefix = "    " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                pretty_print(value, indent + 1)
            else:
                print(f"{prefix}{key}: {value}")
    else:
        print(f"{prefix}{data}")


if __name__ == "__main__":
    s = Sensors()
    result = s(state={})

    print("\n[INFO] Pretty-printing the returned dictionary:\n")
    pretty_print(result)