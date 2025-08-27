# test_graph.py
import langgraph.errors
from langchain_core.messages import AIMessage
from tqdm import tqdm

from autonomous import graph as autonomous_graph
from langchain_core.runnables import RunnableConfig
from components.utils import extract_thought_and_speech
import time
from components.logger import init_loggers


def main():

    # === Init logger ===
    plan_logger, function_logger, error_logger = init_loggers("logs")

    # Run the graph with basic config
    config = RunnableConfig(
        run_name="graph_test_run",
        configurable={"thread_id": "test-thread-2"}
    )

    debug_count = 0

    while True:
        print("=== Running Graph ===")
        try:
            for step in autonomous_graph.stream({"messages": ["Start monitoring"]}, config):
                for node_name, output in step.items():

                    if not output or "messages" not in output:
                        print(f"[INFO] Not usable node: {node_name.upper()}")
                        continue

                    if node_name == "executing_agent":
                        for tool_call in output["messages"][-1].tool_calls:
                            if 'function' in str(tool_call['args']):
                                tool_call["args"] = tool_call["args"]["parameters"]

                            function_logger.info(f"Tool Name: {tool_call['name']}")
                            function_logger.info(f"Tool Args: {tool_call['args']}")
                            function_logger.info(f"{'=' * 50}\n")

                    if isinstance(output["messages"][-1], AIMessage) and output["messages"][-1].content not in ["", " ", None]:
                        print(f"[DEBUG] Check is AIMessage: {isinstance(output['messages'][-1], AIMessage)}")
                        print("=|" * 50)
                        print(f"[INFO] Running node: {node_name}")
                        print("=|" * 50)

                        print("=" * 50)

                        ai_thought, ai_response = extract_thought_and_speech(output["messages"][-1].content)
                        print("Thinking process:", ai_thought)
                        print("=" * 50)
                        print("Decision:", ai_response)
                        # speak(ai_response)

                        plan_logger.info(f"Thought: {ai_thought}")
                        plan_logger.info(f"Response: {ai_response}")
                        plan_logger.info(f"{'=' * 50}\n")

                        # print("=" * 50)
                        # print(f"[INFO] Whole process elapse time: {time.time() - start_time}")
                        # print("=" * 50)
                        print()
            for _ in tqdm(range(15 * 60), desc="Small break"):
                time.sleep(1)
            debug_count += 1

            if debug_count >= 20:
                break
        except langgraph.errors.GraphRecursionError as e:
            print(f"[INFO] Got {e}")
            error_logger.error(f"{e}\n{'=' * 50}", exc_info=True)
            function_logger.info(f"{'=' * 50}\n")

        except UnboundLocalError as e:
            print(f"[INFO] Got {e}")
            error_logger.error(f"{e}\n{'=' * 50}", exc_info=True)
            function_logger.info(f"{'=' * 50}\n")

    print("=== Done ===")


if __name__ == "__main__":
    main()
