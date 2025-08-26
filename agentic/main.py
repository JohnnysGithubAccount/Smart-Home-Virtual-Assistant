import ollama
import json
import agents
from memory import AgentMemory

memory = AgentMemory()

functions = [
    {
        "name": "lighting_agent",
        "parameters": {
            "type": "object",
            "properties": {
                "dim": {"type": "integer"},
                "color": {"type": "string"},
                "off": {"type": "boolean"}
            }
        }
    },
    {
        "name": "climate_agent",
        "parameters": {
            "type": "object",
            "properties": {
                "set_temp": {"type": "integer"}
            }
        }
    },
    {
        "name": "security_agent",
        "parameters": {
            "type": "object",
            "properties": {
                "lock_doors": {"type": "boolean"}
            }
        }
    },
    {
        "name": "media_agent",
        "parameters": {
            "type": "object",
            "properties": {
                "play": {"type": "string"}
            }
        }
    }
]

def handle_tool_call(name, arguments):
    args = json.loads(arguments)
    func = getattr(agents, name)
    func(**args)
    return f"{name} executed with {args}"

def agent_loop(user_goal):
    memory.clear()
    memory.add("system", "You are an agentic smart home assistant. Your goal is to fulfill the user's intent using tools. Think step-by-step. Use tools only when needed.")
    memory.add("user", user_goal)

    while True:
        response = ollama.chat(
            model="llama3:1b",
            messages=memory.get(),
            functions=functions
        )

        msg = response["message"]
        memory.add(msg["role"], msg["content"] if "content" in msg else "")

        if msg.get("function_call"):
            fn_name = msg["function_call"]["name"]
            fn_args = msg["function_call"]["arguments"]
            print(f"\n📞 Tool call: {fn_name}({fn_args})")

            result = handle_tool_call(fn_name, fn_args)

            memory.add("function", {
                "name": fn_name,
                "content": result
            })
        else:
            print("🤖", msg["content"])
            break  # End if no more function calls or reflection

def main():
    print("🧠 Agentic Smart Home Assistant")
    while True:
        user_input = input("\n🎯 Goal: ")
        if user_input.lower() == "exit":
            break
        agent_loop(user_input)

if __name__ == "__main__":
    main()
