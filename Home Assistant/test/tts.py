import asyncio
import edge_tts
import sounddevice as sd
from pydub import AudioSegment
import io
import numpy as np

async def speak(text, voice="en-NZ-MitchellNeural", rate="+0%"):
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

# Run it
asyncio.run(speak("Hello Johnny, this is a speech message from edge text to speech model"))