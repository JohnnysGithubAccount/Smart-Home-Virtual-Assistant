import pyttsx3
import numpy as np
import sounddevice as sd
import torch
import edge_tts
import asyncio
from pydub import AudioSegment
import io


device = 'cuda' if torch.cuda.is_available() else 'cpu'


def using_pyttsx3(text):
    tts_engine = pyttsx3.init()
    tts_engine.say(text)
    tts_engine.runAndWait()
    del tts_engine


async def using_model(text, voice="en-NZ-MitchellNeural", rate="+0%"):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    buffer.seek(0)

    # Decode MP3 to raw audio using pydub
    audio_segment = AudioSegment.from_file(buffer, format="mp3")
    samples = np.array(audio_segment.get_array_of_samples())

    # Reshape for stereo if needed
    if audio_segment.channels == 2:
        samples = samples.reshape((-1, 2))

    # Play audio
    sd.play(samples, samplerate=audio_segment.frame_rate)
    sd.wait()


def speak(text, speech_type: str = "edge-tts"):
    print(f"\t\t{'=' * 50}")

    print(f"\t\t[DEBUG] Debugging speak")
    print(f"\t\t\t[DEBUG] Speaking: {text}")
    print(f"\t\t\t[DEBUG] Type: {type(text)}")
    if speech_type == "pyttsx3":
        using_pyttsx3(text)
    else:
        asyncio.run(using_model(text))

    print(f"\t\t{'=' * 50}")


def test():
    speak("Hello master, my name is Marvin, I'm your virtual assistant for smart home, how can I help you")

def main():
    pass


if __name__=="__main__":
    test()
