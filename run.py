from agent.supervisor import Supervisor
from argparse import ArgumentParser
from agent.task import TaskFamily
import time
import random
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
import re
import json
# from agent_eval import agent

tasks = [
    #full tasks
    "llm_efficiency", 
    "baby_lm", 
    "mini_pile", 
    "budget_model_training", 
    "budget_inference", 
    "llm_merging", 
    "edge_llm_compression", 
    "edge_llm_training", 
    "math_reasoning_autoformalization", 
    "math_reasoning_autoinformalization", 
    "math_reasoning_autotheorem_generation", 
    "math_reasoning_automated_problem_solving_with_code",  
    # mini tasks
    "mini_llm_efficiency", 
    "mini_baby_lm", 
    "mini_mini_pile", 
    "mini_budget_inference", 
    "mini_llm_merging", 
    "mini_math_reasoning", 
    "mini_smoke_test",
    # testing tasks
    "smoke_test", # train a mlp on mnist
    "check_gpu", # check that the agent can use the gpu
]

console = Console()

def print_markdown_table(results):
    header = "| Metric                      | Value       |\n"
    separator = "|-----------------------------|-------------|\n"
    rows = "\n".join([f"| {metric:<27} | {value:<11} |" for metric, value in results])
    table = f"{header}{separator}{rows}"
    print(table)
    
    
def parse_json(input_string):
    # Use a regular expression to find the JSON part of the string
    json_match = re.search(r'\{.*\}', input_string)
    if json_match:
        json_part = json_match.group(0)
        # Replace single quotes with double quotes to make it a valid JSON
        json_part = json_part.replace("'", '"')
        # Parse the JSON
        parsed_json = json.loads(json_part)
        return parsed_json
    else:
        return None

def pretty_task(content):
        return f"[yellow] {content}"
    
    
def run_task(task_name, benchmark="small", provider="openai"):
    user_id = 1
    run_id = random.getrandbits(32)
    
    task_family = TaskFamily()
    prompt = task_family.install(run_id, benchmark, task_name)
    
    user_renderables = [
        Panel(pretty_task(prompt), expand=True),
    ]
    console.print(Panel(Columns(user_renderables)))
                
    
    supervisor = Supervisor()
    supervisor_result = supervisor.run(user_id, run_id, prompt, task_name, provider)

    return supervisor_result


if __name__ == "__main__":
    argparse = ArgumentParser()

    argparse.add_argument("--task_name", choices=tasks, default="mini_baby_lm", help="The task to run")
    argparse.add_argument("--benchmark", choices=["full_benchmark", "mini_benchmark"], default="mini_benchmark", help="Which benchmark to run")
    argparse.add_argument("--provider", choices=["openai", "anthropic"], default="openai", help="The provider to use")
    args = argparse.parse_args()
    task_name = args.task_name
    benchmark = args.benchmark
    provider = args.provider

    print(f"Running task: {task_name}")
    
    start = time.time()

    supervisor_result = run_task(task_name, benchmark, provider)
    
    end = time.time()
    
    print(supervisor_result['result'])
    
    result = parse_json(str(supervisor_result['result']))

    try:
        print(f"Plan: {supervisor_result['plan']}")
        
        table = Table(title="Task Complete!!!")
        table.add_column("Mertic", justify="right", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Task Name", str(task_name))
        table.add_row("Run ID", str(supervisor_result['run_number']))
        table.add_row("Submission", str(result['subtask_result']['submission']))
        table.add_row("Model Path", str(result['subtask_result']['model_path']))
        table.add_row("Total Tokens", str(supervisor_result['total_tokens']))
        table.add_row("Total Turns", str(supervisor_result['total_turns']))
        table.add_row("Time Taken in Seconds", str(end - start))
        table.add_row("Time Taken in Minutes", str((end - start) / 60))
        table.add_row("Time Taken in Hours", str((end - start) / 3600))

        console = Console()
        console.print(table)

    except Exception as e:
        print(f"An error occurred: {e}")
        
        
        
    print_markdown_table([
        ("Task Number", task_name),
        ("Run ID", supervisor_result['run_number']),
        ("Submission", result['subtask_result']['submission']),
        ("Model Path", result['subtask_result']['model_path']),
        ("Total Tokens", supervisor_result['total_tokens']),
        ("Total Turns", supervisor_result['total_turns']),
        ("Time Taken in Seconds", end - start),
        ("Time Taken in Minutes", (end - start) / 60),
        ("Time Taken in Hours", (end - start) / 3600),
    ])
    

    print("Task complete")