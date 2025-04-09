import openai
import json
import instructor

from utils.firebase_update import update_device, fetch_data

client = openai.OpenAI(
    api_key="",
    base_url="http://localhost:8000/v1",
)

client = instructor.patch(client)
