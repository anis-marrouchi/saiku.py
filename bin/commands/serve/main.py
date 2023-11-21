import asyncio
import os
import click
from pathlib import Path
import nest_asyncio

from saiku.agents.agent import Agent  # Replace with your actual Agent import

async def main(opts):
    nest_asyncio.apply()
    opts = {"actionsPath": "../actions", "allowCodeExecution": True, **opts}
    agent = Agent(opts)
    agent.options = {**agent.options, **opts}
    await check_and_install_packages(agent)
    await agent.functions["websocket_server"].run({'htmlContent': "<a href='http://localhost:8080' traget='_blank'>http://localhost:8080</a>"})
    print("Starting the agent...")
    await agent.functions["execute_code"].run({'language': "bash", "code": "cd {} && npm run dev".format(Path(os.getcwd(), "extensions", "ai-chatbot"))})

async def check_and_install_packages(agent):
    node_modules_path = Path(os.getcwd(), "extensions", "ai-chatbot", "node_modules")
    if not node_modules_path.exists():
        print("'node_modules' directory not found. Installing packages...")
        try:
            await agent.functions["execute_code"].run({'language': "bash", "code": "cd {} && pnpm install".format(node_modules_path.parent)})

        except Exception as error:
            print("An error occurred during the installation:", error)
            
@click.command(name='serve', help='Chat with the Saiku agent in the browser')
@click.option('-m', '--llm', default='openai', type=click.Choice(['openai', 'vertexai']), help='The language model to use. Possible values: openai, vertexai.')
def command(llm):
    """Command to start the agent and chat in the browser."""
    opts = {
        'llm': llm
    }
    asyncio.run(main(opts))

if __name__ == "__main__":
    command()