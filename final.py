import time
from transformers import pipeline
import torch
from utils.running_utils import speak, chat, wake_word_detector
from utils.text_to_speech.utils import init_bark, init_speecht5
import warnings
from utils.configs import chat_model, speaker_using, debug_virtual_assistant, bark_index


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def main(debug = False):
    start_time = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    classifier = pipeline(
        "audio-classification",
        model="MIT/ast-finetuned-speech-commands-v2",
        device=device
    )

    transcriber = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-base.en",
        device=device
    )

    if debug:
        print(f"Speaker using is {speaker_using}")

    if speaker_using == "bark":
        processor, model, voice_preset, sample_rate = init_bark(
            device=device,
            index=bark_index
        )
    else:
        processor, model, vocoder, speaker_embeddings = init_speecht5(
            device
        )
    if debug:
        print(f"[INFO] Finished initialization with elapsed time: {time.time() - start_time}")

    while True:
        messages = [
            {
                'role': 'system',
                'content': "You're a helpful and hilarious virtual assistant for smart home."
                           "From now on, your response with anything with number must be turned into words."
                           "For example, 100 means one hundred, 90 means ninety, 30.5 means thirty point five, similarly with other numbers. "
                           "And if you see information about temperature, its unit is Celsius."
                           "Always check if the user wanted to ask anything else."
                           "Try to give short, compact, human-like, informative and funny responses. "
                           "If you doesn't have an answer, just tell the user that you don't know, don't try too hard to give a answer. "
                           "Do not assume the question, if the user's query was unclear, just tell the user"
                           "You also have access to these following functions, use them only to answer if you were asked about the current temperature or humidity or controlling devices in the smart home."
            },
        ]

        wake_word_detector(
            classifier,
            debug=debug
        )
        if debug:
            print("[INFO] Wake word detected")

        if speaker_using == "bark":
            speak(
                "Greeting mediocre creature. I'm Marvin [laughs], your virtual assistant. How can I help you",
                speaker=speaker_using,
                processor=processor,
                model=model,
                voice_preset=voice_preset,
                sample_rate=sample_rate,
                device=device,
            )
        else:
            speak(
                "Greeting mediocre creature. I'm Marvin, your virtual assistant. How can I help you",
                speaker=speaker_using,
                processor=processor,
                model=model,
                vocoder=vocoder,
                speaker_embeddings=speaker_embeddings,
                device=device,
                verbose=True
            )

        while True:
            text = chat(transcriber, debug=debug, model=chat_model, messages=messages)

            if text == "exit":
                speak(
                    "Sleeping, call me whenever you need me",
                    speaker=speaker_using,
                    processor=processor,
                    model=model,
                    voice_preset=voice_preset,
                    sample_rate=sample_rate,
                    device=device,
                    verbose=True
                )
                break

            if speaker_using == "bark":
                speak(
                    text,
                    speaker=speaker_using,
                    processor=processor,
                    model=model,
                    voice_preset=voice_preset,
                    sample_rate=sample_rate,
                    device=device,
                    verbose=True
                )

            else:
                speak(
                    text,
                    speaker=speaker_using,
                    processor=processor,
                    model=model,
                    vocoder=vocoder,
                    speaker_embeddings=speaker_embeddings,
                    device=device,
                    verbose=True
                )


if __name__ == "__main__":
    main(
        debug=debug_virtual_assistant
    )
