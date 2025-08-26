Our project includes 2 agent graphs.

# Quick response agent (instance graph)

This is used for finishing user request immediately. When receive user input, a 0.5b model classify the input into either chat/Q&A or the request for doing something with external devices.

If the input got routed to chat agent, that is just a simple chatting query and got handle quickly using the chat_agent.

If the input got routed to tool agent, that is a need for do something with external devices, then the agent (a tool calling large language model) will decide what is the tools will be need to accomplish the task given by the user.

The tool execution node will execute those tools and return the tool running status back to the agent for verification.

# Autonomous Agent (autonomous graph)

This is a larger and stronger llm agent, which will take information from the sensors to plan and execute the necessary tools for controlling the house and make it more proactive for user with their home.

This process will be called periodically at a fixed time.
