import winsound
import pyttsx3
# from RealtimeTTS import TextToAudioStream, ZipVoiceEngine, ZipVoiceVoice
# import numpy as np
# import sounddevice as sd
# from TTS.api import TTS


def speak(text, isPyttsx3: bool = False):
    print(f"\t\t{'=' * 50}")

    print(f"\t\t[DEBUG] Debugging speak")
    print(f"\t\t\t[DEBUG] Speaking: {text}")
    print(f"\t\t\t[DEBUG] Type: {type(text)}")
    if isPyttsx3:
        tts_engine = pyttsx3.init()
        tts_engine.say(text)
        tts_engine.runAndWait()
        del tts_engine
    else:
        pass

    print(f"\t\t{'=' * 50}")


def test():
    tts = TTS("tts_models/en/vctk/vits")
    print("Available speakers:", tts.speakers)

def main():
    pass


if __name__=="__main__":
    test()