# llms/openai_model.py

import json
import os
import sys
from openai import OpenAI
from typing import Any, Dict, Optional, Union
from ..interfaces.llm import LLM, PredictionRequest, PredictionResponse

openai = OpenAI()

class OpenAIPredictionRequest(PredictionRequest):
    def __init__(self, model: str, messages: list, max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None, top_p: Optional[float] = None,
                 tools: Optional[Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.messages = messages
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.tools = tools

class OpenAIPredictionResponse(PredictionResponse):
    def __init__(self, text: str, model: str, message: Any, other_metadata: Optional[Any] = None):
        super().__init__(text, model, other_metadata)
        self.message = message

class OpenAIModel(LLM):
    def __init__(self, agent, opts: Dict[str, Optional[str]]):
        self.agent = agent
        self.api_key = opts.get("apiKey", os.environ.get("OPENAI_API_KEY", ""))
        
        self.name = os.environ.get("OPENAI_MODEL", "gpt-4-1106-preview")
        self.messages = [
            {
                "role": "system",
                "content": agent.system_message or "You are a helpful assistant",
            },
        ]

    def predict(self, request):
        try:
            # Remove 'prompt' key from the request if it exists
            filtered_request = {k: v for k, v in request.items() if k != 'prompt'}
            model = request.get("model", "gpt-4-1106-preview")
            
            # Make an asynchronous call to OpenAI API
            response = openai.chat.completions.create(**filtered_request)
            if response and hasattr(response, 'choices') and response.choices:
                choice = response.choices[0].message
                tool_calls = getattr(choice, 'tool_calls', [])
                content = getattr(choice, 'content', '')

                text = tool_calls if tool_calls else content or ""

                return OpenAIPredictionResponse(text=text, model=model, message=choice, other_metadata=None)
            else:
                return OpenAIPredictionResponse(text="", model= model, message=None, other_metadata=None)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(f"An error occurred: {e}")
            raise

    async def interact(self, use_delegate: bool = False) -> Union[str, None]:
        decision = await self.agent.think()
        if isinstance(decision.text, list):
            tool_calls = decision.text
        else:
            tool_calls = []

        content = decision.text if isinstance(decision.text, str) else None
        self.agent.messages.append(decision.message)

        if content:
            if use_delegate:
                return content
            else:
                if "both" in self.agent.options['speech'] or "output" in self.agent.options['speech']:
                    await self.agent.speak(content)
                self.agent.display_message(content)
        else:
            for tool_call in tool_calls:
                action_name = tool_call.function.name if tool_call.function and tool_call.function.name else ""
                args = tool_call.function.arguments if tool_call.function and tool_call.function.arguments else ""
                result = ""
                if (self.agent.memory.last_action == action_name and 
                    self.agent.memory.last_action_status == "failure"):
                    continue  # Skip the repeated action if it previously failed

                try:
                    args = json.loads(args)
                    if not self.agent.options["allow_code_execution"]:
                        # Prompt logic for execution confirmation
                        # This might be different in Python. You might need to use an alternative to 'prompts'
                        answer = input(f"Do you want to execute the code? (y/n): ").lower() == 'y'
                        if not answer:
                            result = "Code execution cancelled for current action only"
                        else:
                            result = await self.agent.act(action_name, args)
                    else:
                        result = await self.agent.act(action_name, args)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    result = str(e)

                self.agent.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": action_name,
                    "content": result
                })

            return await self.interact(use_delegate)