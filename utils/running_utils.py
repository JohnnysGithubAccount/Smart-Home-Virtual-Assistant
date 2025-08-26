import ollama
import asyncio
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
from utils.smarthome_tasks.firebase_update import update_device, fetch_data
from utils.smarthome_tasks.tools_desc import tools
from utils.speech_to_text.utils import transcribe
from utils.text_to_speech.utils import using_bark, using_speecht5
from utils.running.llm import *
from utils.running.stt import *
from utils.running.tts import *


def chat(
        transcriber,
        messages,
        model:str = "llama3.2:1b",
        verbose:bool = False,
        debug:bool = False
):
    msg_input = transcribe(
        transcriber
    )

    if "exit" in msg_input:
        return "exit"
    print(f"You: {msg_input}")
    if verbose:
        print("Processing")
    return asyncio.run(
        run(
            model,
            msg_input,
            messages=messages,
            debug=debug
        )
    )


def main():
    pass


if __name__ == "__main__":
    main()
