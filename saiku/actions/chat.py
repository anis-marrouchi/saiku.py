import os
from pathlib import Path

class ChatAction:
    def __init__(self, agent):
        self.dependencies = []
        self.agent = agent
        self.name = "chat"
        self.description = "Chat with agent on a browser."
        self.parameters = []

    async def run(self, args):
        # Resolve the path to the HTML file
        filename = Path(__file__).parent.parent / 'islands/chat.html'
        # Read the HTML content from the file
        with open(filename, "r", encoding="utf8") as file:
            html_content = file.read()

        # Start the WebSocket server with the HTML content
        response = await self.agent.functions['websocket_server'].run({'htmlContent': html_content})
        return f"Chat Server started: {response}"