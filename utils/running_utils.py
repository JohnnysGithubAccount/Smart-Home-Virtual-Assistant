import ollama
import asyncio
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
from utils.smarthome_tasks.firebase_update import update_device, fetch_data
from utils.smarthome_tasks.tools_desc import tools
from utils.speech_to_text.utils import transcribe


async def run(model: str, user_input: str):
    client = ollama.AsyncClient()

    # Initialize conversation with a user query
    messages = [
        {
            'role': 'system',
            'content': "You're a virtual assistant for smart home, if the question is related to controlling device or get temperature or humidity, only answer from information got from the functions, else, do just answer and do not recommend functions."
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
    print(response)

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
            "update_device": update_device,
            "fetch_data": fetch_data,
        }
        # print(f"\navailable_function: {available_functions}")
        for tool in response["message"]["tool_calls"]:
            print(f"available tools: {tool}")
            # tool: {'function': {'name': 'get_flight_times', 'arguments': {'arrival': 'LAX', 'departure': 'NYC'}}}
            function_to_call = available_functions[tool["function"]["name"]]
            print(f"function to call: {function_to_call}")

            function_response = None
            if function_to_call == update_device:
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
    return second_response["message"]["content"]


def wake_word_detector(
    classifier,
    wake_word="marvin",
    prob_threshold=0.5,
    chunk_length_s=2.0,
    stream_chunk_s=0.25,
    debug=False,
):
    if wake_word not in classifier.model.config.label2id.keys():
        raise ValueError(
            f"Wake word {wake_word} not in set of valid class labels, pick a wake word in the set {classifier.model.config.label2id.keys()}."
        )

    sampling_rate = classifier.feature_extractor.sampling_rate

    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
    )

    print("Listening for wake word...")
    for prediction in classifier(mic):
        prediction = prediction[0]
        if debug:
            print(prediction)
        if prediction["label"] == wake_word and prediction["score"] > prob_threshold:
            break



def chat(transcriber, verbose:bool = False):
    msg_input = transcribe(
        transcriber
    )
    if verbose:
        print(f"You: {msg_input}")
        print("Processing")
    return asyncio.run(
        run(
            "llama3.2:1b",
            msg_input
        )
    )


def speak(text, speaker):
    pass


def main():
    pass



if __name__ == "__main__":
    main()
