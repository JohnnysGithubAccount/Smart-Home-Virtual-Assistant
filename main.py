import openai
import json
import instructor

from utils.smarthome_tasks.firebase_update import update_device, fetch_data

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
            "content": "You're a smart home virtual assistant, you can help user to control device using functions and also answer their normal question. If the query related to controlling device, getting temperature or humidity, only select the function."
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
                            "description": "The desired status of the device, off means 0 and on means 1.",
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
                "description": "Get the current temperature or humidity or both (depended on the will of user).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Value either being 'temperature' or 'humidity' or 'both' depends on the question",
                        },
                    },
                    "required": ["status"],
                },
            },
        }
    ]


    response = client.chat.completions.create(
        model = "functionary",
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

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        print("-" * 10)
        print(function_name)
        function_to_call = function_list[function_name]
        function_args = json.loads(tool_call.function.arguments)
        print("-" * 10)
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
