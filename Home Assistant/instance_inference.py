from langchain_core.messages import HumanMessage, AIMessage
from tqdm import tqdm
import time

from init_graph.instance import graph as instance_graph
from langchain_core.runnables import RunnableConfig
from components.utils import extract_thought_and_speech
from components.voice.text_to_speech import speak


def main():

    # Run the graph with basic config
    config = RunnableConfig(
        run_name="graph_test_run",
        configurable={"thread_id": "test-thread-1"}
    )

    while True:
        start_time = time.time()

        # Create a test input
        user_input_text = input("User: ")
        # user_input_text = listen()
        # user_input_text = "turn on the bedroom lights"
        # user_input_text = "turn off the lights"

        print(f"[INFO] Running condition: {user_input_text.lower().strip() not in ['q', 'quit', 'exit', None]}")
        if user_input_text.lower().strip() in ['q', 'quit', 'exit', None]:
            break

        user_input = HumanMessage(content=f"{user_input_text}")

        print("=== Running Graph ===")
        for step in instance_graph.stream({"messages": [user_input]}, config):
            # step is a dict mapping node_name -> output
            for node_name, output in step.items():
                # print(f"\n[Node: {node_name}]")
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


if __name__ == "__main__":
    main()
