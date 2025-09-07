import sys
import torch
import numpy as np
from pyannote.audio import Model
from pyannote.audio.pipelines import VoiceActivityDetection
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
from utils import load_tokens


# === Get TOKENS ===
TOKEN = load_tokens()["HUGGINGFACE"]

# Load VAD model
device =torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

model = Model.from_pretrained(
    "pyannote/segmentation",
    use_auth_token=TOKEN,
    device=device
)
pipeline = VoiceActivityDetection(segmentation=model)
pipeline.instantiate({
    "onset": 0.5,
    "offset": 0.5,
    "min_duration_on": 0.1,
    "min_duration_off": 0.1
})
transcriber = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base.en",
    device=device
)


# --- Live VAD loop ---
def live_vad(chunk_length_s=1.0, stream_chunk_s=1.0):
    sampling_rate = 16000
    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
    )

    print("🎧 Start speaking...")

    for chunk in mic:
        if "raw" not in chunk or "sampling_rate" not in chunk:
            continue

        waveform_np = chunk["raw"]
        sample_rate = chunk["sampling_rate"]

        # Convert to torch tensor with shape (1, time)
        waveform = torch.tensor(waveform_np, dtype=torch.float32).unsqueeze(0)

        # Run VAD
        vad_result = pipeline({"waveform": waveform, "sample_rate": sample_rate})
        speech_segments = vad_result.get_timeline().support()
        speech_detected = len(speech_segments) > 0
        print(f"[INFO] Speech segments: {speech_segments}")
        print(f"[INFO] Speech detected: {speech_detected}")

        sys.stdout.write("\033[K")
        if speech_detected:
            print("🗣️ SPEECH detected", end="\r")
        else:
            print("🔇 ...silence...", end="\r")


if __name__ == "__main__":
    try:
        live_vad(chunk_length_s=1.0, stream_chunk_s=1.0)
    except KeyboardInterrupt:
        print("\nStopped by user.")
