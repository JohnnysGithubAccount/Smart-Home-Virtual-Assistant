
from transformers import pipeline
import torch
from utils.running_utils import speak, chat, wake_word_detector


def main():
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

    speaker = None

    while True:
        wake_word_detgit ector(
            classifier,
            debug=False
        )

        text = chat(transcriber)

        speak(text, speaker)



if __name__ == "__main__":
    main()
