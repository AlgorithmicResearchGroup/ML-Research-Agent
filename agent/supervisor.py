import json
import anthropic
from openai import OpenAI
from argparse import ArgumentParser
from typing import TypedDict
from dotenv import load_dotenv
import os
import tiktoken
import traceback
from agent.coding_agent import CodingAgent
from agent.research_agent import ResearchAgent
from agent.execution_agent import ExecutionAgent
from agent.prompts import get_supervisor_prompt

load_dotenv()

class Supervisor:
    def __init__(self):
        """Initialize the agent.
        input: task, instructions
        output: final_command
        """
        self.agent_model = "openai"
        self.oai_client = OpenAI(api_key=os.getenv("OPENAI"))
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC"))
        self.prompt = get_supervisor_prompt()
        
        
        
        self.oai_planner_tool = [
            {
                "type": "function",
                "function": {
                    "name": "plan_generator",
                    "description": "Generate a plan for an AI agent, given a prompt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plan": {
                                "type": "array",
                                "description": "an array of plans",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["plans"],
                    },
                },
            }
        ]

        self.planner_tool = [
            {
                "name": "plan_generator",
                "description": "Generate a plan for an AI agent, given a prompt",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "plan": {"type": "array", "description": "an array of plans"},
                    },
                    "required": ["plans"],
                },
            }
        ]
    
    def generate_plan(self, task):
        user_query = task
        if self.agent_model == "openai":
            response = self.oai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": user_query},
                ],
                tools=self.oai_planner_tool,
                tool_choice={
                    "type": "function",
                    "function": {"name": "plan_generator"},
                },
            )
            # print("Got response from OpenAI API")
            # print(response)
        else:
            response = self.client.beta.tools.messages.create(
                model="claude-3-opus-20240229",  # Choose the appropriate model for your use case
                messages=[{"role": "user", "content": self.prompt + user_query}],
                temperature=0,  # Adjust based on desired creativity
                max_tokens=1024,  # Adjust based on how detailed the response needs to be
                tools=self.planner_tool,
            )
        return response
    

    def parse_chat_response_to_subtasks(self, chat_response):
        # Initialize the tasks_by_agent dictionary
        tasks_by_agent = {
            "Research Agent": [],
            "Coding Agent": [],
            "Execution Agent": [],
            "Memory Agent": []  # Include Memory Agent if applicable
        }

        # Extract the plan from the chat response
        if self.agent_model == "openai":
            # Handle tool calls to extract the plan
            try:
                first_tool_call = chat_response.choices[0].message.tool_calls[0]
                function_arguments = first_tool_call.function.arguments
                arguments_json = json.loads(function_arguments)
                plan = arguments_json["plan"]
            except (AttributeError, IndexError, KeyError, json.JSONDecodeError) as e:
                print(f"Failed to extract plan from tool calls: {e}")
                # Fallback to parsing the assistant's message content
                plan_text = chat_response.choices[0].message.content.strip()
                plan = self.fallback_plan_parser(plan_text)
        else:
            # Adjusted for other models or if tool calls are not used
            plan_text = chat_response.content[1].input.get("plans", "")
            if not plan_text:
                plan_text = chat_response.completion.strip()
            try:
                plan = json.loads(plan_text)
            except json.JSONDecodeError:
                print("Failed to parse plan from response. Attempting to extract plan manually.")
                plan = self.fallback_plan_parser(plan_text)

        # Debug: Print the plan to check its structure
        print(f"Plan is: {plan}")

        # Parse the plan and assign tasks to agents
        for step in plan:
            if isinstance(step, dict):
                agent = step.get("agent")
                task = step.get("task")
                if agent and task:
                    if agent in tasks_by_agent:
                        tasks_by_agent[agent].append(task)
                    else:
                        print(f"Unknown agent '{agent}' in plan. Adding to tasks_by_agent.")
                        tasks_by_agent.setdefault(agent, []).append(task)
                else:
                    print("Invalid step format in plan. Missing 'agent' or 'task'. Step: {step}")
            else:
                print(f"Invalid step type. Expected dict, got {type(step)}. Step: {step}")

        return tasks_by_agent

    def fallback_plan_parser(self, plan_text):
        # This parser tries to extract steps in the format:
        # {"agent": "Agent Name", "task": "Task Description"}
        steps = []
        lines = plan_text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Try to parse line as JSON
            try:
                step = json.loads(line)
                if isinstance(step, dict) and 'agent' in step and 'task' in step:
                    steps.append(step)
                    continue
            except json.JSONDecodeError:
                pass
            # Try to parse line as 'Agent: Task'
            if ':' in line:
                agent_part, task_part = line.split(':', 1)
                agent = agent_part.strip()
                task = task_part.strip()
                steps.append({'agent': agent, 'task': task})
            else:
                # Can't parse the line
                print(f"Cannot parse line: {line}")
        return steps

    def run(self, user_id, run_id, task, task_name, provider):
        if task:
            try:
                print("Running supervisor agent...")
                agent_plan_text = self.generate_plan(task)
                tasks_by_agent = self.parse_chat_response_to_subtasks(agent_plan_text)
                print(f"Plan generated for {task_name}:\n")
                print(json.dumps(tasks_by_agent, indent=2))


                # Dispatch tasks to agents
                if tasks_by_agent["Research Agent"]:
                    task = tasks_by_agent["Research Agent"]
                    print(f"Running research agent with task: {task}")
                    research_agent = ResearchAgent(user_id, run_id, task, task, 1, provider)
                    research_agent.run()
                if tasks_by_agent["Coding Agent"]:
                    task = tasks_by_agent["Coding Agent"]
                    print(f"Running coding agent with task: {task}")
                    coding_agent = CodingAgent(user_id, run_id, task, task, 2, provider)
                    coding_agent.run()
                if tasks_by_agent["Execution Agent"]:
                    task = tasks_by_agent["Execution Agent"]
                    print(f"Running execution agent with task: {task}")
                    execution_agent = ExecutionAgent(user_id, run_id, task, task, 3, provider)
                    execution_agent.run()
                # Collect results and return
                return "Tasks have been dispatched to agents."

            except Exception as e:
                print(
                    f"An error occurred in the Supervisor: {str(e)} on line {e.__traceback__.tb_lineno}"
                )
                traceback.print_exc()
                return "An error occurred while running the supervisor agent."
        else:
            print("No task chosen. Please run the command again with a valid task.")

