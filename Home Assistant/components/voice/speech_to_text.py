import time

import torch.cuda
from transformers import pipeline
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
import speech_recognition as sr
import winsound
import sys
import torch
import webrtcvad
import collections
import numpy as np

from pyannote.audio.pipelines import VoiceActivityDetection
from pyannote.audio import Model
from pyannote.audio.core.io import Audio
from pyannote.core import Segment
import ffmpeg
import json
from .utils import load_tokens
import soundfile as sf


# === Get TOKENS ===
TOKEN = load_tokens()["HUGGINGFACE"]

# === Initialize speech recognizer ===
start_time = time.time()

recognizer = sr.Recognizer()
device =torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
transcriber = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base.en",
    device=device
)
model = Model.from_pretrained(
    "pyannote/segmentation",
    use_auth_token=TOKEN,
    device=device
)
pipeline = VoiceActivityDetection(segmentation=model)
pipeline.instantiate(
    {
        "onset": 0.5,
        "offset": 0.5,
        "min_duration_on": 0.0,
        "min_duration_off": 0.0
    }
)
print(f"[INFO] Initializing time: {time.time() - start_time}")


# === Speech-to-Text using Google Speech-to-Text ===
def speech_to_text_google(max_retries=3, timeout=5, phrase_time_limit=8):
    retries = 0

    while retries < max_retries:
        with sr.Microphone() as source:
            print("[INFO] 🎤 Listening...")
            winsound.Beep(1000, 1000)

            recognizer.adjust_for_ambient_noise(source)

            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except sr.WaitTimeoutError:
                print("⌛ No speech detected within timeout")
                retries += 1
                if retries >= max_retries:
                    return "End the conversation, quit!!!"
                continue

        try:
            text = recognizer.recognize_google(audio)
            print(f"🗣 User: {text}")
            return text
        except sr.UnknownValueError:
            retries += 1
            print(f"[ERROR] Could not understand audio (attempt {retries}/{max_retries})")
            if retries >= max_retries:
                return "[INFO] End the conversation, quit!!!"
        except sr.RequestError as e:
            print(f"⚠[ERROR] Could not request results; {e}")
            return ""


# === Voice activate detection function with some sort of model ===
def voice_active_detection(waveform, sample_rate):
    waveform = torch.tensor(waveform, dtype=torch.float32).unsqueeze(0)

    vad_result = pipeline(
        {
            "waveform": waveform,
            "sample_rate": sample_rate
        }
    )

    return vad_result.get_timeline().support()


# === Speech-to-Text using Whisper ===
def speech_to_text_whisper(full_waveform, sample_rate):
    transcript = transcriber(
        {
            "raw": full_waveform.squeeze(0).numpy(),
            "sampling_rate": sample_rate
        },
        generate_kwargs={"max_new_tokens": 128}
    )
    return transcript["text"].strip()


# === Final Speech-to-Text listening ===
def listen(using_gg: bool = False):
    if using_gg:
        text = speech_to_text_google()
    else:
        text = input("User: ")
        # text = transcribe_with_vad()

    return text


# === Transcribe using voice activity detection ===
def transcribe_with_vad(sampling_rate=16_000, chunk_length_s=1.0, stream_chunk_s=1.0, speech_timeout = 1.0):
    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
        stride_length_s=0.0
    )

    buffered_audio = []
    last_speech_end = None

    print("Start speaking...")

    for chunk in mic:
        waveform_np = chunk["raw"]
        sample_rate = chunk["sampling_rate"]

        segments = voice_active_detection(waveform=waveform_np, sample_rate=sample_rate)

        buffered_audio.append(waveform_np)

        if segments:
            last_speech_end = time.time()
            print(f"[INFO]🗣️ Speech detected")
        else:
            if last_speech_end and (time.time() - last_speech_end > speech_timeout):
                print(f"[INFO]🔇 Speech ended — transcribing...")
                buffered_np = np.concatenate(buffered_audio).astype(np.float32)
                full_waveform = torch.tensor(buffered_np, dtype=torch.float32).unsqueeze(0)

                # saving recorded voice for debugging
                # sf.write("debug.wav", buffered_np, sample_rate)  # uncomment this for checking out the voice file

                text = speech_to_text_whisper(full_waveform=full_waveform, sample_rate=sample_rate)

                print(f"🗣 User: {text}")

                return text


# === Main ===
def main():
    pass


# === Testing functions ===
def test():
    print(transcribe_with_vad(chunk_length_s=1.0, stream_chunk_s=1.0))
    # listen(using_gg=False, chunk_length_s=5.0, stream_chunk_s=1.0)


if __name__ == "__main__":
    test()
