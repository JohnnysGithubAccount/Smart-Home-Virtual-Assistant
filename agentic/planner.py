import subprocess
import json
import ollama


SYSTEM_PROMPT = """You are a smart home assistant. 
Given a normal conversation, just answer normally and humorously.
Given a user command, break it down into a list of actions using real Python function calls. Use these functions:

- lighting_agent(dim=percent, color='warm', off=True)
- climate_agent(set_temp=degrees)
- security_agent(lock_doors=True/False)
- media_agent(play='playlist or media name')

Think step-by-step. Output only Python code. No explanation."""

def query_llama(user_input):
    response = ollama.chat(
        model='llama3.2:1b',
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    return response['message']['content'].strip()
