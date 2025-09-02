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


# === Initialize speech recognizer ===
recognizer = sr.Recognizer()
device =torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
transcriber = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base.en",
    device=device
)
pipe = pipeline(
    "audio-classification",
    model="pipecat-ai/smart-turn-v2",
    feature_extractor="facebook/wav2vec2-base"
)
vad = webrtcvad.Vad(2)  # 0=aggressive, 3=conservative


def listen(using_gg: bool = False, max_retries=3, timeout=5, phrase_time_limit=8, chunk_length_s=5.0, stream_chunk_s=1.0):
    if using_gg:
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
                print(f"❌ Could not understand audio (attempt {retries}/{max_retries})")
                if retries >= max_retries:
                    return "End the conversation, quit!!!"
            except sr.RequestError as e:
                print(f"⚠️ Could not request results; {e}")
                return None
    else:
        sampling_rate = transcriber.feature_extractor.sampling_rate

        mic = ffmpeg_microphone_live(
            sampling_rate=sampling_rate,
            chunk_length_s=chunk_length_s,
            stream_chunk_s=stream_chunk_s,
        )

        print("Start speaking...")

        # for item, vad in zip(transcriber(mic, generate_kwargs={"max_new_tokens": 128}), pipe(mic, top_k=None)[0]):
        #     sys.stdout.write("\033[K")
        #
        #     print(f"Completed turn? {vad['label']}  Prob: {vad['score']:.3f}")
        #
        #     if not item["partial"][0]:
        #         break
        # print(f"User: {item['text']}")
        #
        # return item["text"]
        buffer = []

        for out in transcriber(mic, generate_kwargs={"max_new_tokens": 128}):
            if not out:
                continue

            if "text" in out:
                print(out["text"], end="")

            # Collect raw audio chunks
            if "chunks" in out:
                chunk = out["chunks"]  # depends how mic yields audio
                buffer.append(chunk)

            # Detect end of stream
            if out.get("is_last"):
                # Convert to waveform for the VAD model
                waveform = np.concatenate(buffer)

                # Run Pipecat VAD
                result = pipe(waveform, top_k=None)[0]
                print(f"\n🛑 Completed turn? {result['label']} (prob {result['score']:.3f})")

                buffer = []  # reset for next utterance


def test():
    listen()


if __name__ == "__main__":
    test()
