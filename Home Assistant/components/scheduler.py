from .tools import tools, tool_names


tool_registry = dict(zip(tool_names[4:], tools[4:]))


def get_tool(tool_name):
    return tool_registry[tool_name]