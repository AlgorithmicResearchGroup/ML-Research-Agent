import os
import zmq
import json
from dotenv import load_dotenv
from datetime import datetime
import traceback

from rich import print
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.columns import Columns
from sqlalchemy import Text

from agent.memory import AgentMemory
from agent.tool_registry import Tool, worker_action_map
from agent.memory import Base
from agent.tool_registry import research_agent_tools
from agent.prompts import get_research_agent_prompt, get_worker_system_prompt
from agent.models.anthropic import AnthropicModel
from agent.models.openai import OpenAIModel

load_dotenv()
console = Console()


class ResearchAgent:
    def __init__(
        self,
        user_id: int,
        run_id: int,
        user_query: str,
        plan: list,  # Assuming plan is a list of objectives
        worker_number: int,
        provider: str,
        zmq_context=None,
        pub_endpoint="tcp://localhost:5557",
        sub_endpoint="tcp://localhost:5556",
    ) -> None:

        self.user_id = user_id
        self.run_id = run_id
        self.agent_model = provider
        self.user_query = user_query
        self.plan = plan
        self.worker_number = worker_number
        self.task_number = 0
        self.num_tokens = []
        self.run_number = run_id
        self.start_time = datetime.now()
        self.objectives = plan  # List of objectives
        self.completed_objectives = []
        self.in_progress_objective = None

        #self.plan_structure = {"subtasks": [], "completed": [], "in_progress": None}
        self.system_prompt = get_worker_system_prompt(self.run_number)

        self.memory = AgentMemory()

        # ZeroMQ setup
        self.context = zmq_context or zmq.Context.instance()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.connect(pub_endpoint)
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(sub_endpoint)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all topics

    def send_message(self, topic, message):
        self.publisher.send_string(f"{topic} {json.dumps(message)}")

    def receive_messages(self):
        messages = []
        try:
            while True:
                topic, message = self.subscriber.recv_string(flags=zmq.NOBLOCK).split(' ', 1)
                messages.append((topic, json.loads(message)))
        except zmq.Again:
            pass  # No more messages
        return messages

    def handle_messages(self):
        messages = self.receive_messages()
        for topic, message in messages:
            # Handle different message types
            if topic == "task_update":
                self.handle_task_update(message)
            elif topic == "agent_communication":
                self.handle_agent_communication(message)

    def handle_task_update(self, message):
        # Process task updates from other agents or supervisor
        pass  # Implement as needed

    def handle_agent_communication(self, message):
        # Process messages from other agents
        pass  # Implement as needed
    
    
    
    def get_next_objective(self):
        """Retrieve the next objective to work on."""
        for objective in self.objectives:
            if objective not in self.completed_objectives:
                return objective
        return None  # All objectives are completed

    def update_progress(self, objective, status):
        """Update the progress of an objective."""
        if status == "completed" and objective not in self.completed_objectives:
            self.completed_objectives.append(objective)
            print(f"Objective completed: {objective}")

    def is_task_complete(self):
        """Check if all objectives are completed."""
        return set(self.completed_objectives) == set(self.objectives)
    

    def pretty_attempt(self, content):
        return f"[yellow] Total Tokens: {sum(self.num_tokens)} --> Previous Attempt: {content}"

    def pretty_output(self, content):
        return f"[blue] Total Tokens: {sum(self.num_tokens)} --> Previous Output: {content}"

    def run_subtask(
        self,
        previous_subtask_attempt,
        previous_subtask_output,
        previous_subtask_errors,
        elapsed_time,
    ) -> dict:
        # Handle incoming messages
        self.handle_messages()
        

        memories = self.memory.get_conversation_memory(self.run_id)

        self.prompt = get_research_agent_prompt(
            self.user_query,
            self.plan,
            self.run_number,
            memories,
            elapsed_time,
            previous_subtask_attempt,
            previous_subtask_output,
            previous_subtask_errors,
        )

        try:
            if self.task_number > 0:
                if isinstance(previous_subtask_attempt, str):
                    user_renderables = [
                        Panel(
                            self.pretty_attempt(previous_subtask_attempt), expand=True
                        ),
                        Panel(self.pretty_output(previous_subtask_output), expand=True),
                    ]
                    console.print(Panel(Columns(user_renderables)))
                else:
                    print(
                        f"""
                        Previous Attempt: {previous_subtask_attempt}
                        Previous Output: {previous_subtask_output}
                        """
                    )

            if self.agent_model == "openai":
                (
                    response_data,
                    total_tokens,
                    prompt_tokens,
                    response_tokens,
                ) = OpenAIModel(self.system_prompt, research_agent_tools).generate_response(
                    self.prompt
                )
            else:
                (
                    response_data,
                    total_tokens,
                    prompt_tokens,
                    response_tokens,
                ) = AnthropicModel(self.system_prompt, research_agent_tools).generate_response(
                    self.prompt
                )

            self.num_tokens.append(total_tokens)
            print(f"Number of tokens: {total_tokens}")

            if not response_data:
                print("No response data found.")
                return {
                    "subtask_result": "Invalid response",
                    "subtask_status": "failure",
                }

            tool_output = self.process_response(response_data)

            # Send ZeroMQ message about task completion
            self.send_message("task_update", {
                "agent": "ResearchAgent",
                "run_id": self.run_id,
                "task_number": self.task_number,
                "status": "completed",
                "result": tool_output,
            })

            return {
                "subtask_result": tool_output,
                "attempted": "yes",
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "response_tokens": response_tokens,
            }

        except Exception as e:
            print(
                f"An error occurred in the ResearchAgent: {str(e)} on line {e.__traceback__.tb_lineno}"
            )
            traceback.print_exc()
            return {
                "subtask_result": {
                    "tool": "None",
                    "status": "failure",
                    "attempt": f"An error occurred: {str(e)}",
                    "stdout": "None",
                    "stderr": "None",
                },
                "attempted": "no",
                "total_tokens": 0,
                "prompt_tokens": 0,
                "response_tokens": 0,
            }

    def process_response(self, response_data):
        # Process the response from the language model and execute the appropriate tool
        if isinstance(response_data, dict):
            for key, val in worker_action_map.items():
                if isinstance(val, str):
                    if val in response_data:
                        tool_output = Tool(
                            {
                                "type": "function",
                                "function": {
                                    "name": key,
                                    "parameters": response_data[val],
                                },
                            }
                        ).run()
                        return tool_output
                elif isinstance(val, list):
                    if all(k in response_data for k in val):
                        tool_output = Tool(
                            {
                                "type": "function",
                                "function": {
                                    "name": key,
                                    "parameters": {k: response_data[k] for k in val},
                                },
                            }
                        ).run()
                        return tool_output
        else:
            return response_data

    def process_subtasks(self):
        results = []
        
        self.task_number = 0

        previous_subtask_tool = "You are starting the task"
        previous_subtask_attempt = "You are starting the task"
        previous_subtask_result = "This is your first attempt"
        previous_subtask_output = "You are starting the task"
        previous_subtask_errors = "You are starting the task"
        self.task_number = 0

        self.memory.save_conversation_memory(
            self.user_id,
            self.run_id,
            self.task_number,
            previous_subtask_tool,
            previous_subtask_result,
            previous_subtask_attempt,
            previous_subtask_output,
            previous_subtask_errors,
            total_tokens=0,
            prompt_tokens=0,
            response_tokens=0,
        )

        while not self.is_task_complete():
            current_time = datetime.now()
            elapsed_time = current_time - self.start_time
            
            # Get the next objective
            self.in_progress_objective = self.get_next_objective()
            if not self.in_progress_objective:
                print("All objectives are completed.")
                break

            subtask_response = self.run_subtask(
                previous_subtask_attempt,
                previous_subtask_output,
                previous_subtask_errors,
                elapsed_time,
            )

            try:
                previous_subtask_tool = subtask_response["subtask_result"].get("tool", "Unknown")
                previous_subtask_result = subtask_response["subtask_result"].get("status", "Unknown")
                previous_subtask_attempt = subtask_response["subtask_result"].get("attempt", "")
                previous_subtask_output = subtask_response["subtask_result"].get("stdout", "")
                previous_subtask_errors = subtask_response["subtask_result"].get("stderr", "")
                total_tokens = subtask_response["total_tokens"]
                prompt_tokens = subtask_response["prompt_tokens"]
                response_tokens = subtask_response["response_tokens"]

                self.memory.save_conversation_memory(
                    self.user_id,
                    self.run_id,
                    self.task_number,
                    previous_subtask_tool,
                    previous_subtask_result,
                    previous_subtask_attempt,
                    previous_subtask_output,
                    previous_subtask_errors,
                    total_tokens,
                    prompt_tokens,
                    response_tokens,
                )
                
                
                # Evaluate if the objective is completed
                if previous_subtask_result == "success":
                    self.update_progress(self.in_progress_objective, "completed")
                else:
                    print(f"Objective not completed yet: {self.in_progress_objective}")
                    
            except Exception as e:
                print(f"An error occurred while processing subtask response: {e}")
                traceback.print_exc()
                # Handle exceptions appropriately

            results.append(subtask_response)
            self.task_number += 1

            # Check for termination condition
            if "return_fn" in previous_subtask_attempt:
                print(
                    f"Plan execution complete. Worker number {self.worker_number} completed the task"
                )
                return {
                    "plan": self.plan,
                    "result": previous_subtask_attempt,
                    "total_tokens": sum(self.num_tokens),
                    "total_turns": str(self.task_number),
                    "run_number": str(self.run_number),
                }

    def run(self):
        worker_result = self.process_subtasks()
        return worker_result