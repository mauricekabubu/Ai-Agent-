# AI Device Control Agent

A simple AI-powered desktop assistant built with Python, LangGraph, LangChain, and Google's Gemini model. The agent uses natural language to understand user commands and execute actions on a Windows computer through custom tools.

## Features

* Shutdown computer using natural language
* Restart computer using natural language
* Cancel scheduled shutdowns
* Conversational AI interface powered by Gemini
* Tool-calling architecture using LangGraph ReAct agents
* Extensible design for adding more device control capabilities

## Tech Stack

### Backend

* Python 3.x

### AI Frameworks

* LangChain
* LangGraph

### Large Language Model

* Google Gemini Flash Lite

### Environment Management

* python-dotenv

### Operating System Integration

* Python os module

## Project Architecture

```
User
  │
  ▼
Gemini LLM
  │
  ▼
LangGraph ReAct Agent
  │
  ├── Shutdown Tool
  ├── Restart Tool
  └── Cancel Shutdown Tool
  │
  ▼
Windows Operating System
```

## How It Works

1. The user enters a natural language request.

Example:

```
Shut down my computer
```

2. The Gemini model receives the request.

3. LangGraph's ReAct agent analyzes the request and determines whether a tool should be used.

4. If a tool is required, the agent selects the appropriate function.

Example:

```python
shut()
```

5. The tool executes a Windows system command:

```python
os.system("shutdown -s -t 5")
```

6. The operating system schedules the shutdown and the agent returns a confirmation message.

## Available Tools

### Shutdown Tool

Shuts down the computer after 5 seconds.

```python
shutdown -s -t 5
```

### Restart Tool

Restarts the computer after 5 seconds.

```python
shutdown -r -t 5
```

### Cancel Shutdown Tool

Cancels any pending shutdown or restart operation.

```python
shutdown -a
```

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd Ai-Agent
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key
```

### Run Application

```bash
python main.py
```

## Example Usage

```
You: Shut down my computer

Assistant: Computer will shut down in 5 seconds.
```

```
You: Cancel the shutdown

Assistant: Shutdown cancelled.
```

```
You: Restart my PC

Assistant: Computer will restart in 5 seconds.
```

## Security Considerations

This project executes operating system commands directly from AI tool calls. Any additional tools added to the agent should include validation and safety checks to prevent unintended system actions.

## Future Improvements

* Open applications
* Launch websites
* File management
* Voice control
* System monitoring
* Email automation
* WhatsApp automation
* Multi-agent architecture
* Memory and conversation history

## Learning Outcomes

This project demonstrates:

* AI Agents
* Tool Calling
* ReAct Architecture
* LangGraph Workflows
* LLM Integration
* Operating System Automation
* Environment Variable Management
* Python Software Engineering

## License

MIT License
