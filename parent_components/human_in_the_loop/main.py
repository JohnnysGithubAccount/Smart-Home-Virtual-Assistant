from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display


class State(TypedDict):
    input: str


def step_1(state):
    print("---Step 1---")
    pass


def step_2(state):
    print("---Step 2---")
    pass


def step_3(state):
    print("---Step 3---")
    pass


builder = StateGraph(State)
builder.add_node("step_1", step_1)
builder.add_node("step_2", step_2)
builder.add_node("step_3", step_3)
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", "step_3")
builder.add_edge("step_3", END)

# Set up memory
memory = MemorySaver()

# Add
graph = builder.compile(checkpointer=memory, interrupt_before=["step_3"])

# View
display(Image(graph.get_graph().draw_mermaid_png()))


if __name__ == "__main__":
    initial_input = {"input": "hello world"}

    thread = {"configurable": {"thread_id": 1}}

    for event in graph.stream(initial_input, thread, stream_mode='values'):
        print(event)

    user_approval = input("Do you want to got to Step 3? (yes or no): ")

    if user_approval.lower() == "yes":
        for event in graph.stream(None, thread, stream_mode="values"):
            print(event)
    else:
        print("Operation cancelled by user")