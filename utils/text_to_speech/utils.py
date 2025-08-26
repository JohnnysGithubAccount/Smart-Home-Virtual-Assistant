import time

import numpy as np
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan, AutoProcessor
import torch
import sounddevice as sd
from datasets import load_dataset
from transformers import pipeline
from transformers import BarkModel
import torch


def init_speecht5(device):
    processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")

    model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(device)
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(device)

    embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)

    return processor, model, vocoder, speaker_embeddings


def using_speecht5(text, processor, model, vocoder, speaker_embeddings, device, verbose: bool = False):
    if verbose:
        print(f"Assistant: {text}")
    inputs = processor(text=text, return_tensors="pt")
    speech = model.generate_speech(
        inputs["input_ids"].to(device), speaker_embeddings.to(device), vocoder=vocoder
    )
    speech_numpy = speech.cpu().numpy()
    sd.play(speech_numpy.astype(np.float32), samplerate=16000)
    sd.wait()


def init_bark(device, index: int = 6):
    processor = AutoProcessor.from_pretrained("suno/bark")
    model = BarkModel.from_pretrained(
        "suno/bark-small",
        torch_dtype=torch.float16,
        # attn_implementation="flash_attention_2"
    ).to(device)
    model.enable_cpu_offload()
    # model = model.to_bettertransformer()
    voice_preset = f"v2/en_speaker_{index}"
    sample_rate = model.generation_config.sample_rate

    return processor, model, voice_preset, sample_rate


def using_bark(text, model, voice_preset, processor, sample_rate, device='cpu'):
    print(text)
    inputs = processor(text, voice_preset=voice_preset)
    # print(type(inputs))
    # inputs = {key: value.to(device) for key, value in inputs.items()}
    audio_array = model.generate(**inputs)
    audio_array = audio_array.cpu().numpy().squeeze()
    print("Speaking")
    sd.play(audio_array.astype(np.float32), samplerate=sample_rate)
    sd.wait()


def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    processor, model, voice_preset, sample_rate = init_bark(
        device=device,
        index=6
    )

    start_time = time.time()
    using_bark(
        text="Hello, my name is Marvin. And, I'm your virtual assistant. [laughs] How can I help you? [laughter]",
        model=model,
        voice_preset=voice_preset,
        processor=processor,
        device=device,
        sample_rate=int(sample_rate)
    )
    print(time.time() - start_time)


if __name__ == "__main__":
    main()
