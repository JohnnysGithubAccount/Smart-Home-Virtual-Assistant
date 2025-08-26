import ollama
import asyncio
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
from utils.smarthome_tasks.firebase_update import update_device, fetch_data
from utils.smarthome_tasks.tools_desc import tools
from utils.speech_to_text.utils import transcribe
from utils.text_to_speech.utils import using_bark, using_speecht5


def wake_word_detector(
    classifier,
    wake_word="marvin",
    prob_threshold=0.5,
    chunk_length_s=1.0,
    stream_chunk_s=1,
    debug=False,
):
    if wake_word not in classifier.model.config.label2id.keys():
        raise ValueError(
            f"[ERROR]Wake word {wake_word} not in set of valid class labels, pick a wake word in the set {classifier.model.config.label2id.keys()}."
        )

    sampling_rate = classifier.feature_extractor.sampling_rate

    mic = ffmpeg_microphone_live(
        sampling_rate=sampling_rate,
        chunk_length_s=chunk_length_s,
        stream_chunk_s=stream_chunk_s,
    )
    if debug:
        print("[INFO] Listening for wake word...")
    for prediction in classifier(mic):
        prediction = prediction[0]
        if prediction["label"] == wake_word and prediction["score"] > prob_threshold:
            if debug:
                print(f"[INFO] Detected wake word")
            break


