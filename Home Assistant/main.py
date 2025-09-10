import uuid
import time
from tqdm import tqdm

import torch
from transformers import pipeline

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.store.memory import InMemoryStore
from langchain_core.runnables import RunnableConfig

from init_graph.instance import graph as instance_graph

from components.utils import extract_thought_and_speech, plot_graph
from components.voice.speech_to_text import listen
from components.voice.text_to_speech import speak
from components.voice.wake_word_detection import wake_word_detector


def init():
    # === LangGraph config ===
    config = RunnableConfig(
        run_name="graph_test_run",
        configurable={"thread_id": "test-thread-1"},
        recursion_limit=100
    )

    # === Long-term Memory Configs ===
    in_memory_store = InMemoryStore()

    # === Using device ===
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # === Wake word detector ===
    classifier = pipeline(
        "audio-classification",
        model="MIT/ast-finetuned-speech-commands-v2",
        device=device
    )

    return {
        "langgraph_config": config,
        "wake_word_classifier": classifier,
        "device": device,
        "memory": in_memory_store
    }


def run():
    # === Init objects ===
    print(f"[INFO] Initializing objects")
    object_dict = init()
    config = object_dict['langgraph_config']
    classifier = object_dict['wake_word_classifier']
    count_time = 0

    # === Wake word detection ===
    wake_word_detector(
        classifier,
        debug=True
    )
    speak('Hi, how can i help you?')

    # === Agent thing ===
    while True:
        start_time = time.time()

        # === Input ===
        # user_input_text = input("User: ")
        user_input_text = listen()

        if not user_input_text:
            count_time += 1
            speak("I'm so sorry but the sound wasn't clear. Repeat please!")

            if count_time == 3:
                speak("Seems like that was just a mix signal. Shutting down")
                break
            continue

        print(f"[INFO] Running condition: {user_input_text.lower().strip() not in ['q', 'quit', 'exit', None]}")
        if user_input_text.lower().strip() in ['q', 'quit', 'exit', None]:
            break

        user_input = HumanMessage(content=f"{user_input_text}")

        print("=== Running Graph ===")
        for step in instance_graph.stream({"messages": [user_input]}, config):
            # step is a dict mapping node_name -> output
            for node_name, output in step.items():
                try:
                    if isinstance(output["messages"][-1], AIMessage) and output["messages"][-1].content not in ["", " ", None]:
                        print(f"[DEBUG] Check is AIMessage: {isinstance(output['messages'][-1], AIMessage)}")
                        print("=" * 50)

                        ai_thought, ai_response = extract_thought_and_speech(output["messages"][-1].content)
                        print("Home assistant thinking process:", ai_thought)
                        print("Home assistant:", ai_response)

                        if ai_response is None or ai_response.strip() in ["", " "]:
                            continue
                        speak(ai_response)

                        print("=" * 50)
                        print(f"[INFO] Whole process elapse time: {time.time() - start_time}")
                        print("=" * 50)
                        print()
                except KeyError as e:
                    print(f"[ERROR] {e}")
                except TypeError as e:
                    print(f"[ERROR] {e}")

        for _ in tqdm(range(2), desc="Small break"):
            time.sleep(1)

    print("=== Done ===")


def main():
    plot_graph(instance_graph, "graphs/instance.png")
    run()


if __name__ == "__main__":
    main()
