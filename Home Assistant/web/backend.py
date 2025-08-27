# backend/app.py
import time
import uuid

import torch
from transformers import pipeline

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig

from ..init_graph.instance import graph as instance_graph
from ..components.utils import extract_thought_and_speech


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Initialize objects once ===
config = RunnableConfig(run_name="graph_web_run", configurable={"thread_id": "1"})
in_memory_store = InMemoryStore()

device = "cuda" if torch.cuda.is_available() else "cpu"
classifier = pipeline("audio-classification", model="MIT/ast-finetuned-speech-commands-v2", device=device)


@app.get("/")
def root():
    return {"message": "LangGraph Home Assistant API running 🚀"}


@app.post("/process")
async def process_text(data: dict):
    """Takes user text, runs LangGraph, returns AI response."""
    user_text = data.get("text", "")
    if not user_text:
        return JSONResponse({"error": "No input text"}, status_code=400)

    user_input = HumanMessage(content=user_text)
    ai_response = None
    ai_thought = None

    for step in instance_graph.stream({"messages": [user_input]}, config):
        for _, output in step.items():
            if isinstance(output["messages"][-1], AIMessage):
                ai_thought, ai_response = extract_thought_and_speech(output["messages"][-1].content)

    return {"thought": ai_thought, "response": ai_response}


@app.post("/wake-word")
async def detect_wake_word(file: UploadFile):
    """Optional: send audio, detect wake word using classifier"""
    audio_bytes = await file.read()
    # TODO: preprocess audio (e.g., torchaudio) → model input
    result = classifier(audio_bytes)  # needs correct audio processing
    return {"wake_word_detected": result}
