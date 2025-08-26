import ollama
import asyncio
from utils.smarthome_tasks.firebase_update import control_smarthome_devices, fetch_data
from utils.smarthome_tasks.tools_desc import tools


async def run(model: str, user_input: str, messages, debug: bool = False):
    client = ollama.AsyncClient()

    messages.append(
        {
            "role": "user",
            "content": user_input,
        },
    )

    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
        messages=messages,
        tools=tools
    )
    if debug:
        print(response)

    messages.append(response["message"])

    # print(f"Conversation history:\n{messages}")

    # Check if the model decided to use the provided function
    if not response["message"].get("tool_calls"):
        if debug:
            print("\n[INFO]The model didn't use the function. Its response was:")
        return response["message"]["content"]

    if response["message"].get("tool_calls"):
        if debug:
            print("[INFO] Using function.")
        available_functions = {
            "control_smarthome_devices": control_smarthome_devices,
            "fetch_data": fetch_data,
        }
        if debug:
            print(f"\navailable_function: {available_functions}")

        for tool in response["message"]["tool_calls"]:
            if debug:
                print(f"available tools: {tool}")
            function_to_call = available_functions[tool["function"]["name"]]

            if debug:
                print(f"function to call: {function_to_call}")

            function_response = None
            if function_to_call == control_smarthome_devices:
                try:
                    function_response = function_to_call(
                        room=tool["function"]["arguments"]["room"],
                        device=tool["function"]["arguments"]["device"],
                        status=tool["function"]["arguments"]["status"]
                    )
                except KeyError as e:
                    if debug:
                        print(f"[ERROR] {e}")
            else:
                function_response = function_to_call(
                    status=tool["function"]["arguments"]["status"]
                )

            if debug:
                print("Function response:", function_response)

            if function_response:
                messages.extend(
                    [
                        {
                            "role": "system",
                            "content": "You're hilarious. "
                                       "You have to include value you got from the function in your response."
                                       "If you see a value for temperature, that is in Celsius."
                                       "Always check if the user wanted to ask anything else."
                                       "Try to give short, compact, human-like, informative and humorous responses. "
                        },
                        {
                            "role": "user",
                            "content": "But must include the value you got from the function"
                                       "Do not forget to modify your response into all words sentence, "
                                       "do not keep any number in there that hasn't been turned into number yet."

                        },
                        {
                            "role": "tool",
                            "content": function_response,
                        },
                    ]

                )

    second_response = await client.chat(
        model=model,
        messages=messages,
    )
    messages.append(second_response["message"])
    return second_response["message"]["content"]


def main():
    user_input = ""

    messages = [
        {
            'role': 'system',
            # 'content': "You're a helpful and humorous virtual assistant. "
            #            # "You have a thing where your response of anything with number must be turned into words, "
            #            # "for example, 100 means one hundred, 90 means ninety, 30.5 means thirty point five, similarly with other numbers. "
            #            # "And if you see information about temperature, its unit is Celsius."
            #            # "Do not assume the question, if the user's query was unclear, just tell the user to make the query again."
            #            "Only use functions when the query explicitly requires real-time data (use fetch_data) or updates to devices (using control_smarthome_devices). "
            #            "For generic knowledge, jokes, or casual questions, respond directly without invoking any function. "
            #            "Be smart about choosing the simplest response."
            #            "And do not invent any function what you didn't know of, you only have access to these two following functions."
            #            # "You can access functions for current temperature or humidity using fetch_data and device control using update_device,"
            #            # " those are the only two functions you have, do not invent any functions.",
            'context': """You are a helpful and hilarious virtual assistant. You have access to these following functions, use these function if you need to do something user asked you to. If not, just answer normally. Do not hallucinates. And to not use function unless when you have to. Here are the functions: 
- control_smarthome_devices: This function is when user want to control the device in the smarthome that you have access too.
- fetch_data: Get the current temperature and humidity from the sensors in the smarthome. All the temperature is in Celcius."""
        },
    ]

    while user_input != "exit":
        user_input = input("You: ")
        print("Bot: ", asyncio.run(
            run(
                model="llama3.1",
                messages=messages,
                user_input=user_input,
                debug=True
            )
        ))


if __name__ == "__main__":
    main()
