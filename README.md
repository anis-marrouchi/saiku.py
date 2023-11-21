# Saiku.py - The AI Agent

<!-- <b><a href="https://saiku.mintlify.app/">Read our documentation</a></b> -->

## Table of Contents

- [About](#about)
  - [Why Saiku?](#why-saiku)
  - [What is PEAS?](#what-is-peas)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [1. Using Saiku.py in Your Own Projects](#1-using-saikupy-in-your-own-projects)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Initializing Saiku Agent](#initializing-saiku-agent)
    - [Configuring Saiku](#configuring-saiku)
    - [Interacting with Saiku](#interacting-with-saiku)
- [2. Using the Project Itself](#2-using-the-project-itself)
  - [Usage](#usage-1)
    - [Clone the Repository](#clone-the-repository)
    - [Navigate to Project Folder](#navigate-to-project-folder)
    - [Install Dependencies](#install-dependencies)
    - [Run the Project Locally](#run-the-project-locally)
- [Demo](#demo)
- [Available Commands](#available-commands)
- [Use Cases](#use-cases)
  - [Example Use Cases](#example-use-cases)
- [Future Features](#future-features)
- [Contributing](#contributing)
- [Support Saiku.py](#support-saikupy)
- [Feedback and Issues](#feedback-and-issues)
- [API Rate Limits/Cost](#api-rate-limitscost)
- [Note](#note)
- [License](#license)

## About

Saiku.py is a Python-based project aimed at creating a robust, intelligent AI Agent capable of automating various tasks. The agent follows the PEAS (Performance measure, Environment, Actuators, Sensors) framework, ensuring robustness, scalability, and efficiency.

### Why Saiku?

"Saiku" (細工) in Japanese means detailed or delicate work, symbolizing the intricate and intelligent workings of our AI agent. The name reflects our commitment to precision, innovation, and advanced technology.

### What is PEAS?

PEAS stands for Performance measure, Environment, Actuators, and Sensors. It's a framework used to describe the components of an intelligent agent:

- **Performance Measure**: Evaluating the agent's performance
- **Environment**: The operational domain of the agent
- **Actuators**: Actions the agent can perform
- **Sensors**: How the agent perceives its environment

## Features

- Python-based Modular Design
- OpenAI GPT-4 Integration
- Extensible and Customizable
- Features include text_to_speech, speech_to_text, chat, websocket, execute_code, text_image, and vision (video/image analysis using OpenAI Vision).

## Prerequisites

- Python 3.8+
- OpenAI API key

## 1. Using Saiku.py in Your Own Projects

### Installation

- **Step**: Run `poetry add saiku.py` in your project directory.

### Usage

#### 1. Initializing Saiku Agent

- **Example**: 
  ```python
  from saiku import Agent
  agent = Agent()  # Initialize the agent
  ```

#### 2. Configuring Saiku

- **Example Configuration**:
  ```python
  options = {
      "llm": "openai",
      "allowCodeExecution": True
  }
  agent.options(options)
  ```

#### 3. Interacting with Saiku

- **Example Interaction**:
  ```python
  response = await agent.interact("Hello, how can I help you?")
  print(response)
  ```

## 2. Using the Project Itself

### Usage

#### Clone the Repository
```bash
git clone https://github.com/your-repository/saiku.py.git
```

#### Navigate to Project Folder
```bash
cd saiku.py
```

#### Install Dependencies
```bash
poetry install
```

#### Run the Project Locally
```bash
poetry shell
saikupy
```

## Demo

[Include a link to a demo or screenshots if available]

## Available Actions

- `text_to_speech`: Converts text to spoken audio.
- `speech_to_text`: Transcribes spoken audio to text.
- `chat`: Interactive chat with the AI.
- `websocket`: Sets up a WebSocket server for real-time interaction.
- `execute_code`: Executes a code snippet.
- `text_image`: Generates an image based on text input.
- `vision`: Analyzes videos or images using OpenAI Vision.

## Use Cases

### Example Use Cases

- Transcribing audio to text
- Extracting text from an image
- Summarizing a long article
- Executing a code snippet
- Interactive chat with the AI
- Analyzing videos or images for content

## Future Features

[TODO: Include a list of planned features or enhancements]

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information.

## Support Saiku.py

We are actively seeking support and contributions. If you believe in Saiku.py, consider supporting the project.

## Feedback and Issues

Please open an issue on our GitHub repository for any feedback or problems you encounter.

## API Rate Limits/Cost

Be aware of the rate limits and costs associated with the OpenAI API.

## Note

Saiku.py is still in development, and features are subject to change.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.