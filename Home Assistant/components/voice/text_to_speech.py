import pyttsx3
import numpy as np
import sounddevice as sd
import torch
import edge_tts
from pydub import AudioSegment
import io
from utils import clean_text_for_tts, split_into_sentences, playback_worker
import asyncio, threading, queue
import time


device = 'cuda' if torch.cuda.is_available() else 'cpu'


def using_pyttsx3(text):
    tts_engine = pyttsx3.init()
    tts_engine.say(text)
    tts_engine.runAndWait()
    del tts_engine


def wrap_ssml(text, style="general", pitch="default"):
    return f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice name='en-US-AriaNeural'>
            <prosody pitch='{pitch}'>
                <mstts:express-as style='{style}'>
                    {text}
                </mstts:express-as>
            </prosody>
        </voice>
    </speak>
    """


async def using_model(text, voice="en-NZ-MitchellNeural", rate="+0%"):
    # text = wrap_ssml(text=text, style='cheerful', pitch="default")
    start_time = time.time()

    text = clean_text_for_tts(text)

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

    print(time.time() - start_time)


# === TTS for one sentence ===
async def tts_sentence(sentence, voice="en-NZ-MitchellNeural", rate="+20%"):
    communicate = edge_tts.Communicate(text=sentence, voice=voice, rate=rate)
    buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    buffer.seek(0)

    # Decode MP3
    audio_segment = AudioSegment.from_file(buffer, format="mp3")
    samples = np.array(audio_segment.get_array_of_samples())

    # Stereo support
    if audio_segment.channels == 2:
        samples = samples.reshape((-1, 2))

    return samples, audio_segment.frame_rate


async def tts_realtime(text, voice="en-NZ-MitchellNeural"):
    start_time = time.time()

    # Clean text
    cleaned = clean_text_for_tts(text)

    # Split into sentences
    sentences = split_into_sentences(cleaned)
    print(f"[DEBUG] Sentences")
    for sentence in sentences:
        print(f"\t[DEBUG] sentence: {sentence}")

    # Queue for passing audio to playback thread
    q = queue.Queue()
    playback_thread = threading.Thread(target=playback_worker, args=(q,), daemon=True)
    playback_thread.start()

    # Process each sentence asynchronously
    for sentence in sentences:
        samples, rate = await tts_sentence(sentence, voice=voice)
        q.put((samples, rate))

    # Wait for all playback to finish
    q.join()
    q.put(None)  # Stop playback thread

    print(time.time() - start_time)


def speak(text, speech_type: str = "edge-tts"):
    print(f"\t\t{'=' * 50}")

    print(f"\t\t[DEBUG] Debugging speak")
    print(f"\t\t\t[DEBUG] Speaking: {text}")
    print(f"\t\t\t[DEBUG] Type: {type(text)}")

    if speech_type == "pyttsx3":
        using_pyttsx3(text)
    else:
        asyncio.run(using_model(text))
        asyncio.run(tts_realtime(text))

    print(f"\t\t{'=' * 50}")


def test():
    speak("Hello master, my name is Marvin, I'm your virtual assistant for smart home, how can I help you")


def main():
    text = "Why did the computer go to the doctor? 🤒 Because it caught a *virus*! 😂"

    text = """Artificial **intelligence** 🤖 is transforming the way humans interact with machines! 
    From natural language processing to computer vision, AI models are becoming faster, smarter, and more capable...  
    Check this out: https://example.com or www.testsite.org — both should be removed.  

    In the healthcare sector, AI is already assisting doctors by analyzing scans, predicting diseases, and recommending treatments.  
    Meanwhile, in education, personalized _learning_ platforms adapt to each student’s pace and style, making knowledge more accessible than ever before.  

    Transportation is also evolving 🚗🚕🚙, with self-driving cars moving closer to reality and smart traffic systems reducing congestion in major cities.  

    However, alongside these advances, ethical concerns continue to grow.  
    Questions about privacy, bias, and job displacement remain at the center of debates around AI adoption.  

    Some people even write like this~~~ with strange ~~markdown~~ or symbols `code-block`.  

    Despite these challenges, researchers and engineers remain optimistic, pushing the boundaries of what is possible.  
    In the coming decade, artificial intelligence is expected to integrate deeply into daily life,  
    not only enhancing productivity but also reshaping how societies function on a global scale. ✨🌍"""

    speak(text)


if __name__=="__main__":
    main()
