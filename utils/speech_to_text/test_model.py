from transformers import pipeline
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

classifier = pipeline(
    "audio-classification", model="MIT/ast-finetuned-speech-commands-v2", device=device
)

print(classifier.model.config.id2label)