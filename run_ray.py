import os
import ray
from ray.job_submission import JobSubmissionClient
from rich.console import Console
from rich import print
from dotenv import load_dotenv
from argparse import ArgumentParser

console = Console()
load_dotenv()
env_vars = dict(os.environ)
with open(".env") as f:
    lines = f.readlines()
    env_keys = {line.split('=')[0].strip() for line in lines if '=' in line}
    filtered_env_vars = {k: env_vars[k] for k in env_keys if k in env_vars}
    print(filtered_env_vars)

def submit(agent_path, task_name, model_size, ray_client_url):
    """
    Submit a new task to the Ray job queue with GPU constraints.
    """
    client = JobSubmissionClient(ray_client_url)
    try:
        task_id = client.submit_job(
            entrypoint=f"python run.py --task_name {task_name} --model_size {model_size}",
            runtime_env={
                "working_dir": f"{agent_path}", 
                "pip": f"./requirements.txt",
                "env_vars": filtered_env_vars,
                "excludes": ["*.git*"],
            },
        )
        console.print(f"[green]Task {task_id} submitted successfully with GPU constraint.[/]")
        
    except Exception as e:
        console.print(f"[red]Error submitting task: {str(e)}[/]", style="bold")

if __name__ == '__main__':        
    argparse = ArgumentParser()
    argparse.add_argument("--task_name", choices=["pretraining_efficiency", "pretraining_perplexity", "quantization", "data_augmentation", "data_mixture", "sparse_attention_efficiency", "sparse_attention_lrd", "knowledge_distillation", "mixtures_of_experts", "decoding", "smoke-test"], default="pretraining_efficiency", help="The task to run")
    argparse.add_argument("--model_size", choices=["x-small", "small", "medium", "large", "x-large"], default="small", help="The model size to use")
    
    args = argparse.parse_args()
    task_name = args.task_name
    model_size = args.model_size
        
    submit(agent_path="./", task_name=task_name, model_size=model_size, ray_client_url="http://localhost:8265/")

# to start cluster
# ray up server.yaml 

# to connect to cluster
# ray dashboard server.yaml 

# to stop the job
# ray job stop raysubmit_7yT29Yvh6sghSuWd --address http://localhost:8265/