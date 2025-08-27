# 🤖 Marvin: Smart Home Virtual Assistant

A multi-agent home assistant powered by **LangGraph** and **Ollama**, designed to intelligently respond to user queries and control smart devices. Just say the wake word — **"marvin"** — and let the assistant take care of the rest.

---

## 🚀 Project Overview

**Marvin** is a voice-activated AI agent that listens for a wake word, processes user input, and routes it through a dynamic graph of agents. It uses small language models (SLMs) to classify intent and respond appropriately, either by answering questions or executing smart home actions.

---

## 🖼️ Graph Visualization

<div align="center">
  <img alt="LangGraph Architecture" height="400" width="300" src="Home%20Assistant/graphs/instance.png" title="Workflow architecture" />
</div>

---

## 🧠 Architecture

The assistant operates as a graph-based system with the following flow:

### 1. **Wake Word Detection**
- Listens continuously for the wake word: `"marvin"`
- Once triggered, begins capturing user input

### 2. **Intent Classification (SLM)**
- Input is passed to a Small Language Model (SLM)
- Classifies intent as either:
  - **Chat Query** → routed to `chat_agent`
  - **Device Control** → routed to `tool_agent`

### 3. **Chat Agent Flow**
- A second SLM generates a response to the user's question
- Asks if the user needs anything else
  - If **yes** → loop back to intent classification
  - If **no** → save conversation to graph database (long-term memory)

### 4. **Tool Agent Flow**
- Determines which tool or device to activate
- Executes the action and returns result to user
- Asks if further action is needed
  - If **yes** → loop back to intent classification
  - If **no** → save conversation to graph database

### 5. **Memory Node**
- Both agents converge here to store interactions
- Uses a graph database for long-term memory and context retention

---

## 🧩 Model Assignment Table

| Node Name          | Purpose                             | Model Used (via Ollama) |
|--------------------|-------------------------------------|-------------------------|
| `chat_classifier`  | Classify user intent                | `qwen2.5:0.5b`          |
| `chat_agent`       | Answer general questions            | `qwen2.5:1.5b`          |
| `tool_agent`       | Execute smart home actions          | `qwen3:1.7b`            |
| `user_checking`    | Ask user if further help is needed  | `qwen2.5:0.5b`          |
| `long_term_memory` | Save conversation to graph database | `qwen3:4b`              |

> 💡 All models are served locally via [Ollama](https://ollama.com), enabling fast and private inference.

---

## 🛠️ Technologies Used

- **LangGraph** – for building agent workflows
- **LangChain** – or chaining language model calls and integrating tools
- **Ollama** – for running local language models
- **Graph Database** – for storing long-term memory (Neo4j)
- **Wake Word Engine** – for detecting `"marvin"` (Using HuggingFace)
- **Tooling Layer** – for smart device control (Firebase Real-time Database), confirm user request.
- **Esp32** - for executing physical device actions (e.g., lights, fans, sensors)

---

## ⚙️ Setup Instructions

### 1. Install Ollama

Make sure you have [Ollama](https://ollama.com) installed and running locally.

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Install models

Install models I showed in the table above, or you can find models for yourself on [Ollama Model](https://ollama.com/search).

```bash
ollama pull [model_name]
```

### 3. Clone code
```bash
git clone https://github.com/JohnnysGithubAccount/Smart-Home-Virtual-Assistant.git
cd "Smart-Home-Virtual-Assistant"
```

### 4. Install dependencies

Don't forget to create a venv, recommend using Conda.

```bash
conda create -n assistant python=3.9
conda activate assistant
```

Now install the requirements

```bash
pip install requirements.txt
cd "Home Assistant"
```

### 5. Change the configs

Checkout `configs.json`, change the Firebase url, change the Graph database information.

### 6. Run the Assistant

```bash
python3 main.py
```