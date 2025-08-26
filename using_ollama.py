import ollama
import asyncio
from utils.general_purpose.functions import get_antonyms, get_flight_times
from utils.smarthome_tasks.firebase_update import control_smarthome_devices, fetch_data
from utils.smarthome_tasks.tools_desc import tools


async def run(model: str, user_input: str):
    client = ollama.AsyncClient()
    # Initialize conversation with a user query
    messages = [
        {
            'role': 'system',
            'content': "You're a virtual assistant for smart home, if the question is related to controlling device or get temperature or humidity, only answer from information got from the functions."
        },
        {
            "role": "user",
            "content": user_input,
        }
    ]

    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
        messages=messages,
        tools=tools
    )

    # Add the model's response to the conversation history
    messages.append(response["message"])

    # print(f"Conversation history:\n{messages}")

    # Check if the model decided to use the provided function
    if not response["message"].get("tool_calls"):
        print("\nThe model didn't use the function. Its response was:")
        print(response["message"]["content"])
        return

    if response["message"].get("tool_calls"):
        # print(f"\nThe model used some tools")
        available_functions = {
            "update_device": control_smarthome_devices,
            "fetch_data": fetch_data,
        }
        # print(f"\navailable_function: {available_functions}")
        for tool in response["message"]["tool_calls"]:
            print(f"available tools: {tool}")
            # tool: {'function': {'name': 'get_flight_times', 'arguments': {'arrival': 'LAX', 'departure': 'NYC'}}}
            function_to_call = available_functions[tool["function"]["name"]]
            print(f"function to call: {function_to_call}")

            function_response = None
            if function_to_call == control_smarthome_devices:
                function_response = function_to_call(
                    room=tool["function"]["arguments"]["room"],
                    device=tool["function"]["arguments"]["device"],
                    status=tool["function"]["arguments"]["status"]
                )
            else:
                function_response = function_to_call(
                    status=tool["function"]["arguments"]["status"]
                )

            print(function_response)

            if function_response:
                messages.append(
                    {
                        "role": "tool",
                        "content": function_response,
                    }
                )

    second_response = await client.chat(
        model=model,
        messages=messages,
    )
    print(second_response["message"]["content"])


while True:
    msg_input = input("You: ")
    if not msg_input:
        msg_input = "What is the flight time from NYC to LAX?"
    if msg_input.lower() == "exit":
        break
    print("Processing")
    asyncio.run(run("llama3.2:1b", msg_input))
    print("-" * 10)