from datetime import datetime
import os
import json
import importlib.util
import pathlib
import platform
import sys
from markdown import markdown
import psutil
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from ..llms import OpenAIModel
import pygame

class AttrDict(dict):
    def __init__(self, **entries):
        super().__init__(entries)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"'AttrDict' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"'AttrDict' object has no attribute '{item}'")

        
class Agent:
    def __init__(self, options):
        load_dotenv()
        self.options = {**self.default_options(), **options}
        self.system_message = self.options.get('system_message', 'You are a helpful assistant')
        self.score = 100
        self.messages = []
        self.memory = AttrDict(last_action=None, last_action_status=None)
        self.objectives = []
        self.current_objective = None
        self.current_messages = []
        self.services = {}
        self.functions = {}
        self.init(self.options)
        self.load_all_functions(self.options['actions_path'])
        self.actions = self.get_functions_definitions()

    def default_options(self):
        return {
            'actions_path': "../actions",
            'llm': "OpenAI"
        }

    def init(self, options):
        self.options = options
        llm = self.options.get('llm')
        
        if llm == 'openai':
            self.model = OpenAIModel(self, {
                'apiKey': os.environ.get('OPENAI_API_KEY')
            })
        # elif llm == 'vertexai':
        #     self.model = GoogleVertexAI(self, {
        #         'projectId': os.environ.get('GOOGLE_PROJECT_ID'),
        #         'apiEndpoint': os.environ.get('GOOGLE_API_ENDPOINT'),
        #         'modelId': os.environ.get('GOOGLE_MODEL_ID')
        #     })
        # elif llm == 'ollama':
        #     self.model = Ollama(self, {
        #         'baseURL': os.environ.get('OLLAMA_BASE_URL'),
        #         'model': os.environ.get('OLLAMA_MODEL')
        #     })
        # elif llm == 'huggingface':
        #     self.model = HuggingFace(self, {
        #         'apiKey': os.environ.get('HUGGINGFACE_API_KEY'),
        #         'model': os.environ.get('HUGGINGFACE_MODEL')
        #     })
        # elif llm == 'socket':
        #     self.model = SocketAdapterModel(self, self.options)
        else:
            self.model = OpenAIModel(self, {
                'apiKey': os.environ.get('OPENAI_API_KEY')
            })

    async def listen(self):
        """
        Asynchronously listen to speech and return the converted text.
        """
        if "speech_to_text" in self.functions:
            try:
                return await self.functions["speech_to_text"].run({})
            except Exception as e:
                print(f"Error in speech_to_text function: {e}")
                return ""
        else:
            print("speech_to_text function is not defined")
            return ""

    async def think(self, use_function_calls=True):
        """
        Asynchronously process messages and make a decision using the model.
        """
        try:
            # Prepare the system message
            system_message = {
                "role": "system",
                "content": f"{self.system_message}\n{json.dumps(await self.sense())}"
            }

            # Update the list of messages
            messages = [system_message] + self.messages
            self.current_messages = messages

            # Retrieve the last message from a user
            user_message = next(
                (message for message in reversed(self.current_messages) 
                if isinstance(message, dict) and message.get('role') == 'user'), None
            )
            # user_message = next((message for message in reversed(self.current_messages) if message['role'] == 'user'), None)
            user_message_content = user_message['content'] if user_message else None

            # Limit the number of messages to the last 10, if necessary
            limited_messages = self.current_messages[-10:] if len(self.current_messages) > 10 else self.current_messages

            # Prepare parameters for the model's predict method
            predict_params = {
                "prompt": user_message_content,
                "messages": limited_messages,
                "model": getattr(self.model, "name", None)
            }

            if use_function_calls:
                predict_params.update({"tools": self.actions, "tool_choice": "auto"})

            # Make a decision using the model
            decision = self.model.predict(predict_params)
            return decision

        except Exception as error:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return str(error)

    async def speak(self, text, use_local=False):
        """
        Asynchronously convert text to speech and play it.
        """
        if not use_local:
            # Requesting AI model to generate speech-friendly text
            response = await self.model.predict({
                'messages': [
                    {'role': 'system', 'content': 'Generate a Siri-friendly speech from the following text, capturing all key points while omitting or rephrasing unsuitable content.'},
                    {'role': 'user', 'content': text}
                ],
                'model': os.environ.get('OPENAI_MODEL', 'gpt-4-1106-preview'),
                'max_tokens': 64,
                'temperature': 0.8
            })
            text = response.get('text', text)

        if platform.system() == 'Darwin':
            # On macOS, use `say` command for speech synthesis
            return await self.functions["execute_code"].run({'code': f'say "{text}"', 'language': 'applescript'})
        else:
            # Use a text-to-speech function for other platforms
            filename = await self.functions["text_to_speech"].run({'text': text})
            # Play the audio file
            # Initialize pygame mixer
            pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # Wait for the music to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

    def display_message(self, message):
        """
        Display a message in the terminal, rendering Markdown content.
        """
        console = Console()
        md = Markdown(message)
        console.print(md)

    def load_all_functions(self, actions_path):
        """
        Load all action modules from the specified directory.
        """
        actions_dir = pathlib.Path(__file__).parent.resolve() / actions_path
        for file_path in actions_dir.glob('*.py'):
            if file_path.name == "__init__.py":
                continue

            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            action_class_name = ''.join(word.title() for word in module_name.split('_')) + 'Action'
            action_class = getattr(module, action_class_name, None)
            if action_class:
                action_instance = action_class(self)
                self.functions[action_instance.name] = action_instance

    def load_functions(self, actions_path):
        """
        Load specific action modules from the specified directory based on the .saiku configuration.
        """
        actions_dir = pathlib.Path(__file__).parent.resolve() / actions_path

        # Default activated actions
        activated_actions = ['execute_code', 'chat', 'websocket_server']

        # Load additional activated actions from .saiku file if it exists
        saiku_file_path = actions_dir / 'saiku'
        if saiku_file_path.exists():
            with open(saiku_file_path, 'r', encoding='utf-8') as file:
                saiku = json.load(file)
                activated_actions.extend(saiku.get('activatedActions', []))

        # Iterate through each Python file in the directory
        for file_path in actions_dir.glob('*.py'):
            if file_path.name == "__init__.py":
                continue

            # Dynamically import the module
            module_name = file_path.stem  # Extracts module name without '.py'
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Instantiate the action class if it's in the list of activated actions
            action_class_name = ''.join(word.title() for word in module_name.split('_')) + 'Action'
            action_class = getattr(module, action_class_name, None)
            if action_class:
                action_instance = action_class(self)
                if action_instance.name in activated_actions:
                    self.functions[action_instance.name] = action_instance

    def get_all_functions(self):
        """
        Load and return all action instances from the specified directory.
        """
        actions_dir = pathlib.Path(__file__).parent.resolve() / self.options['actions_path']
        functions = []

        # Iterate through each Python file in the directory
        for file_path in actions_dir.glob('*.py'):
            if file_path.name == "__init__.py":
                continue

            # Dynamically import the module
            module_name = file_path.stem  # Extracts module name without '.py'
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Instantiate the action class and add it to the list
            action_class = getattr(module, 'Action', None)
            if action_class:
                action_instance = action_class(self)
                functions.append(action_instance)

        return functions

    async def sense(self):
        """
        Gather and return various system and environment information.
        """
        # System and environment information
        system_info = {
            "agent": {
                "name": "Saiku"
            },
            "os": platform.system(),
            "arch": platform.machine(),
            "version": platform.version(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "used": psutil.virtual_memory().used
            },
            "cpu": {
                "percent": psutil.cpu_percent(interval=1)
            },
            "uptime": psutil.boot_time(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "start_time": datetime.now().strftime("%H:%M:%S"),
            "cwd": os.getcwd(),
            "current_user": {
                "name": os.environ.get("ME"),
                "country": os.environ.get("COUNTRY"),
                "city": os.environ.get("CITY"),
                "company": os.environ.get("COMPANY"),
                "phone": os.environ.get("PHONE")
            },
            "api_services": {
                "weather": os.environ.get("WEATHER_API_KEY"),
                "gitlab": {
                    "version": os.environ.get("GITLAB_VERSION"),
                    "username": os.environ.get("GITLAB_USERNAME"),
                    "api_version": os.environ.get("GITLAB_API_VERSION")
                }
            },
            **self.memory
        }

        return system_info

    async def act(self, action_name, args):
        """
        Execute a specified action and handle success or failure.
        """
        try:
            action = self.functions.get(action_name)
            self.display_message(f"_Executing action **{action_name}: {getattr(action, 'description', 'No description')}**_")

            if action:
                try:
                    output = await action.run(args)
                    self.update_memory({
                        "": action_name,
                        "last_action_status": "success",
                    })
                    return output
                except Exception as error:
                    self.update_memory({
                        "last_action": action_name,
                        "last_action_status": "failure",
                    })
                    return json.dumps({"error": str(error)})

            else:
                self.display_message(f"No action found with name: **{action_name}**")
                return "Action not found"

        except Exception as error:
            return json.dumps({"error": str(error)})

    def evaluate_performance(self):
        """
        Evaluate the agent's performance based on its objectives.
        Returns a score. For now, this is a placeholder value.
        """
        return self.score

    def remember(self, key, value):
        """
        Store a value in the agent's memory under a specific key.
        """
        self.memory[key] = value

    def recall(self, key):
        """
        Retrieve a value from the agent's memory by key.
        """
        return self.memory.get(key)

    def forget(self, key):
        """
        Remove a value from the agent's memory by key.
        """
        if key in self.memory:
            del self.memory[key]

    def save_memory(self):
        """
        Save the agent's memory to a file.
        """
        memory_file_path = pathlib.Path(__file__).parent / "../data/memory.json"
        with open(memory_file_path, "w") as file:
            json.dump(self.memory, file)

    def get_memory(self):
        """
        Retrieve the agent's current memory state.
        """
        return self.memory

    def update_memory(self, args):
        """
        Update the agent's memory with new information.
        """
        self.memory.update(args)

    async def interact(self, delegate=False):
        """
        Interact with the agent's model.
        """
        return await self.model.interact(delegate)

    def get_functions_definitions(self):
        """
        Get the definitions of all loaded functions.
        """
        actions_definitions = []

        for action in self.functions.values():
            action_def = {
                "name": getattr(action, "name", "Unnamed"),
                "description": getattr(action, "description", ""),
                "parameters": getattr(action, "parameters", [])
            }

            function_def = {
                "type": "function",
                "function": {
                    "name": action_def["name"],
                    "description": action_def["description"],
                    "parameters": self._format_parameters(action_def["parameters"])
                }
            }

            actions_definitions.append(function_def)

        return actions_definitions

    def _format_parameters(self, parameters):
        """
        Format the parameters of an action for output.
        """
        param_def = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for param in parameters:
            param_def["properties"][param["name"]] = {
                "type": param.get("type", "unknown"),
                "description": param.get("description", "")
            }
            if param.get("type") == "array" and "items" in param:
                param_def["properties"][param["name"]]["items"] = param["items"]

            if param.get("required", False):
                param_def["required"].append(param["name"])

        return param_def