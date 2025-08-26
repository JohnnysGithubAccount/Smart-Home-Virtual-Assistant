class AgentMemory:
    def __init__(self):
        self.history = []

    def add(self, role, content):
        self.history.append({"role": role, "content": content})

    def get(self):
        return self.history[-10:]  # only last 10 for context

    def clear(self):
        self.history = []
