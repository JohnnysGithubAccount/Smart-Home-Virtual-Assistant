import network
import urequests as requests
import time
import machine
import dht

# ==== CONFIG =====
WIFI_SSID = "your_wifi_name"
WIFI_PASSWORD = "your_wifi_password"
FIREBASE_URL = "https://smarthome-5bd40-default-rtdb.asia-southeast1.firebasedatabase.app/test"

ROOM = "bedroom"  # change to "kitchen" or "living_room"

# ==== CONNECT TO WIFI =====
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

print("Connecting to WiFi...", end="")
while not wifi.isconnected():
    time.sleep(0.5)
    print(".", end="")
print("\nConnected:", wifi.ifconfig())

# ==== DHT22 SENSOR ====
d = dht.DHT22(machine.Pin(4))  # DHT22 on GPIO4

# ==== DEVICE PINS (example setup, change as needed) ====
devices = {
    "air_conditioner": machine.Pin(12, machine.Pin.OUT),
    "heater": machine.Pin(13, machine.Pin.OUT),
    "humidifier": machine.Pin(14, machine.Pin.OUT),
    "lamp": machine.Pin(27, machine.Pin.OUT),
    "lights": machine.Pin(26, machine.Pin.OUT),  # on/off
}

def update_sensor_data():
    d.measure()
    temp = d.temperature()
    hum = d.humidity()
    print("Temp:", temp, "Humidity:", hum)

    url = "{}/{}/sensors.json".format(FIREBASE_URL, ROOM)
    data = {"temperature": temp, "humidity": hum}
    try:
        requests.patch(url, json=data)
    except Exception as e:
        print("Error updating sensor:", e)

def get_and_control_devices():
    url = "{}/{}/device.json".format(FIREBASE_URL, ROOM)
    try:
        res = requests.get(url)
        if res.status_code == 200:
            device_states = res.json()
            print("Device states:", device_states)

            for name, pin in devices.items():
                if name in device_states:
                    val = device_states[name]
                    if isinstance(val, str):  # e.g., "off" / "on"
                        pin.value(1 if val == "on" else 0)
                    elif isinstance(val, int):  # numeric values -> PWM / intensity
                        pin.value(1 if val > 0 else 0)
        res.close()
    except Exception as e:
        print("Error getting devices:", e)

# ==== MAIN LOOP ====
while True:
    update_sensor_data()
    get_and_control_devices()
    time.sleep(5)
