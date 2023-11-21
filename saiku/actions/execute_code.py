import os
import subprocess
import asyncio
import tempfile
from abc import ABC, abstractmethod
import queue
import threading
import time
import traceback

class LanguageRunner(ABC):
    @abstractmethod
    async def run_code(self, code: str):
        pass

class GeneralRunner(LanguageRunner):
    async def run_code(self, command: str):
        process = await asyncio.create_subprocess_shell(
            command, 
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return f"Execution complete. {stdout.decode()}"
        else:
            raise Exception(f"Exit with code: {process.returncode}\nError Output:\n{stderr.decode()}")

class PythonRunner(LanguageRunner):
    async def run_code(self, code: str):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Execute the temporary file
            process = await asyncio.create_subprocess_exec(
                'python3', temp_file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Script exited with code {process.returncode}\nError Output:\n{stderr.decode()}")

            return f"Output:\n{stdout.decode()}"
        finally:
            # Delete the temporary file
            os.remove(temp_file_path)


class ShellRunner(LanguageRunner):
    def __init__(self):
        self.output_queue = queue.Queue()
        self.done = threading.Event()

    def start_process(self, cmd):
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            universal_newlines=True,
            env=my_env,
        )
        threading.Thread(
            target=self.handle_stream_output,
            args=(process.stdout, False),
            daemon=True,
        ).start()
        threading.Thread(
            target=self.handle_stream_output,
            args=(process.stderr, True),
            daemon=True,
        ).start()
        return process

    async def run_code(self, code):
        output_lines = []
        try:
            process = self.start_process(code)
        except:
            return traceback.format_exc()

        while True:
            try:
                output = self.output_queue.get(timeout=0.3)  # Waits for 0.3 seconds
                output_lines.append(output["output"])
            except queue.Empty:
                if self.done.is_set():
                    break
                time.sleep(0.1)

        process.terminate()
        return ''.join(output_lines)

    def handle_stream_output(self, stream, is_error_stream):
        for line in iter(stream.readline, ""):
            self.output_queue.put({"output": line})
            print(line, end="")
        self.done.set()
        
class AppleScriptRunner(LanguageRunner):
    async def run_code(self, code: str):
        process = await asyncio.create_subprocess_shell(
            f"osascript -e \"{code}\"", 
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return stdout.decode()
        else:
            raise Exception(f"Exit with code: {process.returncode}\nError Output:\n{stderr.decode()}")


class ExecuteCodeAction:
    def __init__(self, agent):
        self.agent = agent
        self.dependencies = ["asyncio"]
        self.name = "execute_code"
        self.description = "Execute code in a specific language"
        self.parameters = [
            {
                "name": "language",
                "type": "string",
                "required": True,
                "enum": ["python", "shell", "bash", "applescript", "AppleScript"]
            },
            { 
                "name": "code", 
                "type": "string", 
                "required": True 
            }
        ]
        self.runner_mapping = {
            "python": PythonRunner(),
            "shell": ShellRunner(),
            "bash": ShellRunner(),
            "applescript": AppleScriptRunner(),
            "AppleScript": AppleScriptRunner(),
            # Other mappings as required
        }

    async def run(self, args):
        language = args.get("language")
        code = args.get("code")
        if language not in self.parameters[0]["enum"]:
            raise ValueError(f"Unsupported language: {language}")

        runner = self.runner_mapping.get(language, GeneralRunner())

        if not isinstance(runner, LanguageRunner):
            raise ValueError(f"Invalid runner for language: {language}")

        try:
            output = await runner.run_code(code)
            return f"output is: {output}"
        except Exception as e:
            error_info = {"message": str(e)}
            print(f"Error occurred: {error_info}")
            return str(error_info)

