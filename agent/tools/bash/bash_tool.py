import logging
import shlex
import subprocess
from typing import Dict, Optional
from agent.utils import remove_ascii

bash_tool_definitions = [
    {
        "name": "run_bash",
        "description": "Run a bash script on the server. Doesn't support interactive commands",
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The bash script to run.",
                },
            },
            "required": ["script"],
        },
    },
]


class BashRunnerActor:
    def __init__(self, timeout: int = 1000):
        self.timeout = timeout

    def run(self, command: str) -> Dict[str, Optional[str]]:
        """Method to execute a bash command and return the results."""
        logging.info(f"Executing command: {command}")

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Read the output line by line and print it
            terminal_output = []
            while True:
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    terminal_output.append(output.strip())

            terminal_output = "\n".join(terminal_output)

            error = process.stderr.read()
            if error:
                print("Error:", error.strip())

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(
                    process.args, self.timeout, output=stdout, stderr=stderr
                )

            returncode = process.returncode

            if returncode == 0:
                status = "success"
            else:
                status = "failure"
                logging.error(f"Command failed with returncode: {returncode}")
                logging.error(f"Command stderr:\n{error.strip()}")

            return {
                "tool": "run_bash",
                "status": status,
                "returncode": returncode,
                "attempt": command,
                "stdout": terminal_output,
                "stderr": error.strip(),
            }

        except subprocess.TimeoutExpired as e:
            logging.error(f"Command timed out after {self.timeout} seconds")
            return {
                "tool": "run_bash",
                "status": "failure",
                "returncode": None,
                "attempt": command,
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout} seconds",
            }

        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed with returncode: {e.returncode}")
            logging.error(f"Command stderr:\n{e.stderr}")
            return {
                "tool": "run_bash",
                "status": "failure",
                "returncode": e.returncode,
                "attempt": command,
                "stdout": "",
                "stderr": f"Command failed with returncode: {e.returncode}\nError message: {error.strip()}",
            }

        except Exception as e:
            logging.exception(f"Unexpected error while executing command: {str(e)}")
            return {
                "tool": "run_bash",
                "status": "failure",
                "returncode": None,
                "attempt": command,
                "stdout": "",
                "stderr": f"Unexpected error: {str(e)}",
            }


def run_bash(arguments: dict) -> Dict[str, Optional[str]]:
    """
    This function is used to run a bash script on the server.
    Use this function to run the code you need to complete the task.
    """
    if isinstance(arguments, dict):
        command = arguments["script"]
    else:
        command = arguments

    runner_actor = BashRunnerActor()
    result = runner_actor.run(command)
    result["stdout"] = remove_ascii(result["stdout"])
    return result
