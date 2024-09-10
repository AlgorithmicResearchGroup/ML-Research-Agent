import sys
import os
import io
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from agent.utils import clean_message, remove_ascii

python_tool_definitions = [
    {
        "name": "run_python",
        "description": "Run python code on the server. You must print the output",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to a python file.",
                },
            },
            "required": ["filepath"],
        },
    },
]


class StreamToConsole(io.StringIO):
    def __init__(self):
        super().__init__()
        self.console = sys.__stdout__

    def write(self, message):
        super().write(message)
        self.console.write(message)
        self.console.flush()

    def flush(self):
        super().flush()
        self.console.flush()


class PythonRunnerActor:
    def __init__(self):
        # Initialize an IPython shell instance for running Python code interactively
        self.shell = InteractiveShell.instance()

    def execute_python_code(self, filepath, timeout=10000):
        stdout_capture = StreamToConsole()
        stderr_capture = StreamToConsole()

        stdout_original = sys.stdout
        stderr_original = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        result = {
            "tool": "run_python",
            "status": "failure",
            "attempt": filepath,
            "stdout": "",
            "stderr": "",
        }
        try:
            # Execute the code
            if os.path.isfile(filepath):
                with open(filepath, "r") as file:
                    code = file.read()
                    with capture_output() as captured:
                        out = self.shell.run_cell(code)
                    # Printing captured output for real-time display
                    sys.stdout.write(captured.stdout)
                    sys.stderr.write(captured.stderr)
                    if out.success:
                        result["status"] = "success"
                    else:
                        result["stderr"] = stderr_capture.getvalue()

            else:
                raise FileNotFoundError(f"File not found: {filepath}")

            # Capture the last 500 characters of stdout
            result["stdout"] = stdout_capture.getvalue()[-500:]

        except Exception as e:
            # Handling unexpected errors
            result["stderr"] = str(e)
        finally:
            sys.stdout = stdout_original
            sys.stderr = stderr_original

        return result

    def run_code(self, filepath, timeout=None):
        """Wrapper method to execute Python code using the actor's execution method with an optional timeout."""
        return self.execute_python_code(filepath)


def run_python(arguments):  # run python code on the server
    """
    This function is used to run python code.
    Use this function to run the code you need to complete the task.
    """
    if isinstance(arguments, dict):
        script = arguments["code"]
    else:
        script = arguments

    python_runner_actor = PythonRunnerActor()
    result_future = python_runner_actor.run_code(script)
    result = result_future
    result["stdout"] = remove_ascii(result["stdout"])
    return result
