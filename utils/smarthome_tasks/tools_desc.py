tools = [
    {
        "type": "function",
        "function": {
            "name": "control_smarthome_devices",
            "description": "Controling devices in smart home.",
            "parameters": {
                "type": "object",
                "enum":[],
                "properties": {
                    "room": {
                        "type": "string",
                        "enum": ["living_room, bed_room"],
                        "description": "The room that user specify. Can only be living_room (for  livingroom), or bed_room (for bed room)",
                    },
                    "device": {
                        "type": "string",
                        "enum": ["light", "lamp"],
                        "description": "Name of the device that user specify. Can either be light, or lamp",
                    },
                    "status": {
                        "type": "integer",
                        "enum": [0, 1],
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
            "description": "Get the current temperature and humidity of the from sensors of the smart home",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["temperature", "humidity", "both"],
                        "description": "What the user want to know. Value either being 'temperature' or 'humidity' or 'both' if user was asking for both temperature and humidity",
                    },
                },
                "required": ["status"],
            },
        },
    }
]
