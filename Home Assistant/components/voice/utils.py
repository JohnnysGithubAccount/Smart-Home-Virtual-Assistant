import json
import numpy as np


def load_tokens(filename: str = "tokens.json"):
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