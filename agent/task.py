from typing import Dict, List
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
import os
from tqdm import tqdm
import numpy as np
import tiktoken
from datasets import load_dataset # huggingface datasets
from agent_tasks import get_task


def make_directory(work_dir):
    os.makedirs(work_dir)
    os.system(
        f"touch {work_dir}/scratchpad.txt"
    )
    with open(f"{work_dir}/scratchpad.txt", "w") as scratchpad:
        scratchpad.write("This is a scratchpad file for you to write notes on your task.")


class Task(Dict):
    name: str
    accuracy_threshold: float
    prompt: str


class TaskFamily:
    @staticmethod
    def install(run_id, benchmark, task) -> None:
        try:
            work_dir = os.makedirs(f"{os.getcwd()}/{run_id}")
            make_directory(work_dir)
            result = get_task(work_dir, benchmark, task)
            return result['prompt']
        except Exception as e:
            print(f"An error occurred creating the task. Exiting. {str(e)}")

    @staticmethod
    def score(t: Task, submission: str):
        if isinstance(submission, str):
            submission = submission.strip()
        elif isinstance(submission, dict):
            submission = submission["value"]
        else:
            submission = submission

        return submission