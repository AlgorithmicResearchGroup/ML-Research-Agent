import os
import random
import json
from openai import OpenAI
import anthropic
from dotenv import load_dotenv
from datetime import datetime, timedelta

from rich import print
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from agent.memory import AgentConversation, AgentMemory
from agent.tool_registry import Tool, worker_action_map
from agent.memory import Base
from agent.tool_registry import all_tools
from agent.prompts import get_worker_system_prompt, get_worker_prompt
from agent.models.anthropic import AnthropicModel
from agent.models.openai import OpenAIModel
from agent.utils import make_directory
from agent.tools.thought.thought_tool import update_multiple_tasks

load_dotenv()
console = Console()


class Worker:
    def __init__(
        self, user_id=int, run_id=int, user_query=str, plan=str, worker_number=int, provider=str
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
        
        self.todo_list = self.initialize_todo_list(plan)

        self.plan_structure = {"subtasks": [], "completed": [], "in_progress": None}
        self.system_prompt = get_worker_system_prompt(self.run_number)
        
        self.memory = AgentMemory()
    
    def initialize_todo_list(self, plan):
        return [{"task": step.strip(), "status": "pending"} for step in plan.split('\n') if step.strip()]
    
    def update_task_status(self, tasks):
        if isinstance(tasks, dict):  # Single task update
            tasks = [tasks]
        
        updated_tasks = []
        for task in tasks:
            task_description = task['task']
            status = task['status']
            updated = False
            for todo_task in self.todo_list:
                if todo_task['task'].strip().lower() == task_description.strip().lower():
                    todo_task["status"] = status
                    updated = True
                    updated_tasks.append(f"Task: {task_description}, New status: {status}")
                    break
            
            if not updated:
                print(f"Task '{task_description}' not found in the todo list.")
    
        # Update the todo list using the update_multiple_tasks tool
        todo_string = self.get_current_todo_status()
        update_result = update_multiple_tasks({"tasks": tasks})
        return update_result
    
    def get_current_todo_status(self):
        return "\n".join([f"[{'x' if task['status'] == 'completed' else ' '}] {task['task']}" for task in self.todo_list])
    
    def print_todo_list(self):
        table = Table(title="Todo List")
        table.add_column("Status", style="cyan", no_wrap=True)
        table.add_column("Task", style="magenta")

        for task in self.todo_list:
            status = "✅" if task["status"] == "completed" else "⏳"
            table.add_row(status, task["task"])

        console.print(table)

    def pretty_attempt(self, content):
        return f"[yellow] Total Tokens: {sum(self.num_tokens)} --> Previous Attempt: {content}"

    def pretty_output(self, content):
        return f"[blue] Total Tokens: {sum(self.num_tokens)} --> Previous Output: {content}"
    
    def run_subtask(self, previous_subtask_attempt, previous_subtask_output, previous_subtask_errors, elapsed_time) -> dict:
        memories = self.memory.get_conversation_memory(self.run_id, previous_subtask_output)
        
        self.prompt = get_worker_prompt(
            self.user_query, 
            self.plan, 
            self.run_number,
            memories, 
            elapsed_time,
            previous_subtask_attempt, 
            previous_subtask_output, 
            previous_subtask_errors,
            self.get_current_todo_status()
        )

        try:
            if self.task_number > 0:  # Only print if it's not the first iteration
                if isinstance(previous_subtask_attempt, str):
                    user_renderables = [
                        Panel(self.pretty_attempt(previous_subtask_attempt), expand=True),
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
                response_data, num_tokens = OpenAIModel(self.system_prompt, all_tools).generate_response(self.prompt)
            else:
                response_data, num_tokens = AnthropicModel(self.system_prompt, all_tools).generate_response(self.prompt)
                
            self.num_tokens.append(num_tokens)
            print(f"Number of tokens: {num_tokens}")
            
            # Process the response to update the todo list
            if isinstance(response_data, dict) and 'completed_step' in response_data:
                update_result = self.update_task_status([{"task": response_data['completed_step'], "status": "completed"}])
                print(f"Todo list update result: {update_result}")
            elif isinstance(response_data, dict) and 'tasks' in response_data:
                update_result = self.update_task_status(response_data['tasks'])
                print(f"Todo list update result: {update_result}")
            
            self.print_todo_list()

            if not response_data:
                print("No response data found.")
                return {
                    "subtask_result": "Invalid response",
                    "subtask_status": "failure",
                }

            if isinstance(response_data, dict):
                # Iterate through the action_map
                for key, val in worker_action_map.items():
                    # Check if val is a string and directly check for existence
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
                            )
                            tool_output = tool_output.run()
                            return {"subtask_result": tool_output, "attempted": "yes"}
                    # If val is a list, iterate through the list and check each item
                    elif isinstance(val, list):
                        if all(
                            k in response_data for k in val
                        ):  # All keys in the list must be in response_data
                            tool_output = Tool(
                                {
                                    "type": "function",
                                    "function": {
                                        "name": key,
                                        "parameters": response_data,
                                    },
                                }
                            )
                            tool_output = tool_output.run()
                            return {"subtask_result": tool_output, "attempted": "yes"}
            else:
                return {"subtask_result": response_data, "attempted": "yes"}

        except Exception as e:
            print(e)
            print(
                f"An error occurred in the Worker: {str(e)} on line {e.__traceback__.tb_lineno}"
            )
            out = {
                "tool": "None",
                "status": "failure",
                "attempt": f"An error occurred {str(e)}",
                "stdout": "None",
                "stderr": "None",
            }
            return {"subtask_result": out, "attempted": "no"}

    def process_subtasks(self):
        results = []

        previous_subtask_tool = "You are starting the task"
        previous_subtask_attempt = "You are starting the task"
        previous_subtask_result = "This is your first attempt"
        previous_subtask_output = "You are starting the task"
        previous_subtask_errors = "You are starting the task"
        self.task_number = 0

        self.memory.save_conversation_memory(
            self.user_id,
            self.run_id,
            previous_subtask_tool, 
            previous_subtask_result, 
            previous_subtask_attempt, 
            previous_subtask_output, 
            previous_subtask_errors
        )

        while True:
            current_time = datetime.now()
            
            elapsed_time = current_time - self.start_time
            subtask_response = self.run_subtask(
                previous_subtask_attempt,
                previous_subtask_output,
                previous_subtask_errors,
                elapsed_time
            )
            if self.task_number > 0:
                try:
                    previous_subtask_tool = subtask_response["subtask_result"]["tool"]
                    previous_subtask_result = subtask_response["subtask_result"]["status"]
                    previous_subtask_attempt = subtask_response["subtask_result"]["attempt"]
                    previous_subtask_output = subtask_response["subtask_result"]["stdout"]
                    previous_subtask_errors = subtask_response["subtask_result"]["stderr"]
                    
                    self.memory.save_conversation_memory(
                        self.user_id,
                        self.run_id,
                        previous_subtask_tool, 
                        previous_subtask_result, 
                        previous_subtask_attempt, 
                        previous_subtask_output, 
                        previous_subtask_errors
                    )
                except:
                    if isinstance(subtask_response, str):
                        panel = Panel(
                            Text(f"Thought: {str(subtask_response)}"), style="on green"
                        )
                        print(panel)
                    else:
                        print(subtask_response)

                    previous_subtask_tool = "thought"
                    previous_subtask_attempt = f"You had the thought: {subtask_response}"
                    previous_subtask_result = "You had a thought"
                    previous_subtask_output = "you must now use a tool to complete the task"
                    previous_subtask_errors = "None"
                    
                    self.memory.save_conversation_memory(
                        self.user_id,
                        self.run_id,
                        previous_subtask_tool, 
                        previous_subtask_result, 
                        previous_subtask_attempt, 
                        previous_subtask_output, 
                        previous_subtask_errors
                    )

            results.append(subtask_response)
            self.task_number += 1
            if "return_fn" in previous_subtask_attempt:
                print(
                    f"Plan execution complete. Worker number {self.worker_number} completed the task"
                )
                return {
                        "plan": self.plan, 
                        "result": previous_subtask_attempt, 
                        "total_tokens": sum(self.num_tokens), 
                        "total_turns": str(self.task_number), 
                        "run_number": str(self.run_number)
                        }

    def run(self):
        worker_result = self.process_subtasks()
        return worker_result
