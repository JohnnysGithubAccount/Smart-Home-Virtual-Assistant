tools = [
    {
        "type": "function",
        "function": {
            "name": "update_device",
            "description": "Update the value of device on database to control devices in smart home",
            "parameters": {
                "type": "object",
                "properties": {
                    "room": {
                        "type": "string",
                        "description": "The room that user specify.",
                    },
                    "device": {
                        "type": "string",
                        "description": "Name of the device that user specify.",
                    },
                    "status": {
                        "type": "integer",
                        "description": "Either 0 or 1, 0 is off, 1 is on.",
                    },
                },
                "required": ["room", "device", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_data",
            "description": "Get the current temperature and humidity of the smart home from sensors, temperature will be in Celsius and humidity will be in percent (%)",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Value either being 'temperature' or 'humidity' or 'both' if user was asking for both temperature and humidity",
                    },
                },
                "required": ["status"],
            },
        },
    }
]
