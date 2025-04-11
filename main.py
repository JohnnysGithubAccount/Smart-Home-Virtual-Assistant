import openai
import json
import instructor

from utils.firebase_update import update_device, fetch_data
from datetime import date

# Define client OpenAI
client = openai.OpenAI(
    api_key="this is a key",
    base_url= "http://localhost:8000/v1"
)

client = instructor.patch(client)


def chat_with_llm_fc(message_input):
    messages = [
        {
            "role":"system",
            "content": "Base on the information return by function calling to answer question."
        },
        {
            "role":"user",
            "content": message_input
        }
    ]

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
                "description": "Get the current temperature and humidity of the smart home from the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Value either being temperature or humidity or both",
                        },
                    },
                    "required": ["status"],
                },
            },
        }
    ]


    # Call model 1st time
    response = client.chat.completions.create(
        model = "functionary", # anything
        messages = messages,
        tools = tools,
        tool_choice="auto"
    )

    # Get response message
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    function_list = {
        "update_device": update_device,
        "fetch_data": fetch_data
    }

    # Kiem tra va goi API tuong ung
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = function_list[function_name]
        function_args = json.loads(tool_call.function.arguments)
        print(function_args)

        # Call function
        if function_name == "update_device":
            function_response = function_to_call(
                room = function_args.get("room"),
                device = function_args.get("device"),
                status = function_args.get("status")
            )
        else:
            function_response = function_to_call(
                status = function_args.get("status")
            )

        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "function",
                "name": "functions." + function_name,
                "content": function_response,
            }
        )

    # Call LLM 2nd time with function response
    second_response = client.chat.completions.create(
        model = "functionary",
        messages = messages,
        temperature=0.1,
    )

    return second_response.choices[0].message.content


def main():
    message_input = "Tell me what is the current temperature"
    bot_message = chat_with_llm_fc(message_input)
    print("#" * 10, " Bot :", bot_message )


if __name__ == "__main__":
    main()
