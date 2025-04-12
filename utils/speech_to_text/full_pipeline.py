from transformers import pipeline
import torch
import sys
from utils import launch_fn, transcribe


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    classifier = pipeline(
        "audio-classification", model="MIT/ast-finetuned-speech-commands-v2", device=device
    )

    transcriber = pipeline(
        "automatic-speech-recognition", model="openai/whisper-base.en", device=device
    )

    launch_fn(
        debug=True,
        transcriber=transcriber,
        classifier=classifier
    )


if __name__ == "__main__":
    main()
