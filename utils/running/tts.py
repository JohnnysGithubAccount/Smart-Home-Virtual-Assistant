import ollama
import asyncio
from transformers.pipelines.audio_utils import ffmpeg_microphone_live
from utils.smarthome_tasks.firebase_update import update_device, fetch_data
from utils.smarthome_tasks.tools_desc import tools
from utils.speech_to_text.utils import transcribe
from utils.text_to_speech.utils import using_bark, using_speecht5


def speak(text, speaker="bark", **kwargs):
    """
    speaks out
    :param text: the text
    :param speaker: either bark or t5
    :return: None
    """
    if speaker == "bark":
        using_bark(
            text,
            **kwargs
        )
    else:
        using_speecht5(
            text,
            **kwargs
        )