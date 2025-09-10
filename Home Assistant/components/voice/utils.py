import json
import re
from asyncio import Queue
import sounddevice as sd
import numpy as np


def load_tokens(filename: str = r"D:\UsingSpace\Projects\Artificial Intelligent\Agent\Smart-Home-Virtual-Assistant\Home Assistant\components\voice\tokens.json"):
    with open(filename, "r") as f:
        tokens = json.load(f)

    return tokens


def check_overlap(buffered_audio, check_len=500, tol=1e-4):
    """
    Compare last check_len samples of chunk i with first check_len of chunk i+1.
    If they are too similar, report possible overlap.
    """
    for i in range(len(buffered_audio) - 1):
        a = np.array(buffered_audio[i])
        b = np.array(buffered_audio[i+1])

        # Take tail of a, head of b
        a_tail = a[-check_len:]
        b_head = b[:check_len]

        # Compute difference and correlation
        mse = np.mean((a_tail - b_head) ** 2)
        corr = np.corrcoef(a_tail, b_head)[0,1]

        print(f"Chunk {i} → {i+1}: mse={mse:.6f}, corr={corr:.3f}")

        if mse < tol or corr > 0.95:
            print("  ⚠️ Likely overlap detected here!")


# === Text Clearning ===
def clean_text_for_tts(text: str) -> str:
    text = re.sub(r'[*_~`]', '', text)                # markdown
    text = re.sub(r'http\S+|www\.\S+', '', text)      # urls
    text = re.sub(r'[^\x00-\x7F]+', '', text)         # emojis, non-ASCII
    text = re.sub(r'\s+', ' ', text).strip()          # collapse spaces
    return text


# === Sound playing worker ===
def playback_worker(queue: Queue):
    while True:
        item = queue.get()
        if item is None:
            break
        samples, rate = item
        sd.play(samples, samplerate=rate)
        sd.wait()
        queue.task_done()

# === Sentence splitting ===
def split_into_sentences(text: str):
    # Split by ., !, ? followed by space or end of string
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Remove empty parts
    return [s.strip() for s in sentences if s.strip()]