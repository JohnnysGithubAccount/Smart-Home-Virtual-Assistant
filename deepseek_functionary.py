import openai
import json
import instructor


from utils.firebase_update import update_device, fetch_data

client = openai.OpenAI(
    api_key="sk-36394102ad804cf4801a4938cc925529",
    base_url="https://api.deepseek.com",
)

client = instructor.patch(client)

def chat_with_llm_fc(message_input):
    messages = [
        {
            'role': 'system',
            'content': "Base on the information return by function calling to answer question. Do not use other source."
        },
        {
            'role': 'user',
            'content': message_input
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

    response_llm = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_msg = response_llm.choices[0].message
    print(response_msg)
    tool_calls = response_msg.tool_calls

    function_list = {
        "update_device": update_device,
        "fetch_data": fetch_data
    }

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call= function_list[function_name]
        function_args = json.loads(tool_call.function.arguments)

        function_response = function_to_call(
            status=function_args.get("status")
        )

        messages.append({
            "role": "function",
            "tool_call_id": tool_call.id,
            "name": "functions."+function_name,
            "content": function_response
        })

    second_response = client.chat.completions.create(
        model='deepseek-chat',
        messages=messages
    )

    print(second_response.choices[0].message)
    return second_response.choices[0].message99


def main():
    message_input = "Can you help me get the temperature of the house right now"
    bot_msg = chat_with_llm_fc(message_input=message_input)
    print("*" * 10)
    print(bot_msg)


if __name__ == "__main__":
    main()


