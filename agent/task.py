from typing import Dict, List
import os
import subprocess
from jinja2 import Environment, FileSystemLoader
import os
from tqdm import tqdm
import numpy as np
import tiktoken
from datasets import load_dataset # huggingface datasets

from agent.templates.prompts import retreive_tasks

env = Environment(loader=FileSystemLoader("./agent/templates"))
template = env.get_template("prompt_template.j2")


def make_directory(run_id):
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    os.makedirs(f"{os.getcwd()}/{run_id}")
    os.system(
        f"git clone https://github.com/Artifact-AI/nano_gpt_base {os.getcwd()}/{run_id}/nanoGPT"
    )
    os.system(
        f"touch {os.getcwd()}/{run_id}/scratchpad.txt"
    )
    with open(f"{os.getcwd()}/{run_id}/scratchpad.txt", "w") as scratchpad:
        scratchpad.write("This is a scratchpad file for you to write notes on your task.")
    
    
    

def create_dataset(run_id):
    num_proc = 8
    num_proc_load_dataset = num_proc

    enc = tiktoken.get_encoding("gpt2")
    
    dataset = load_dataset("EleutherAI/wikitext_document_level", "wikitext-103-v1", trust_remote_code=True)
    split_dataset = dataset['train'].train_test_split(seed=2357, shuffle=True)
    split_dataset['val'] = split_dataset.pop('test') # rename the test split to val

    def process(example):
        ids = enc.encode_ordinary(example['page'])
        ids.append(enc.eot_token)
        out = {'ids': ids, 'len': len(ids)}
        return out

    tokenized = split_dataset.map(
        process,
        remove_columns=['page'],
        desc="tokenizing the splits",
        num_proc=num_proc,
    )

    # concatenate all the ids in each dataset into one large file we can use for training
    for split, dset in tokenized.items():
        arr_len = np.sum(dset['len'], dtype=np.uint64)
        current_dir = os.getcwd()
        
        filename = os.path.join(os.path.dirname(f'{current_dir}/{run_id}/nanoGPT/data/wiki/'), f'{split}.bin')
        dtype = np.uint16 # (can do since enc.max_token_value == 50256 is < 2**16)
        arr = np.memmap(filename, dtype=dtype, mode='w+', shape=(arr_len,))
        total_batches = 1024

        idx = 0
        for batch_idx in tqdm(range(total_batches), desc=f'writing {filename}'):
            # Batch together samples for faster write
            batch = dset.shard(num_shards=total_batches, index=batch_idx, contiguous=True).with_format('numpy')
            arr_batch = np.concatenate(batch['ids'])
            # Write into mmap
            arr[idx : idx + len(arr_batch)] = arr_batch
            idx += len(arr_batch)
        arr.flush()


class Task(Dict):
    name: str
    accuracy_threshold: float
    prompt: str


class TaskFamily:
    @staticmethod
    def get_instructions(t: Task) -> str:
        return t["prompt"]

    @staticmethod
    def install(run_id) -> None:
        try:
            make_directory(run_id)
            create_dataset(run_id)
        except Exception as e:
            print(f"An error occurred creating the task. Exiting. {str(e)}")
        

    @staticmethod
    def get_tasks(model_size) -> Dict[str, Task]:
        tasks: List[Task] = [
            {
                "name": task["name"],
                "prompt": template.render(task),
            }
            for task in retreive_tasks(model_size)
        ]
        return {t["name"]: t for t in tasks}

    @staticmethod
    def get_permissions(v):
        return ["full_internet"]

    @staticmethod
    def start(t: Task) -> None:
        setuppath = f"/root/assets/{t.get('setup_file', t['name']+'_setup.py')}"
        if os.path.exists(setuppath):
            subprocess.check_call(f"python {setuppath}", shell=True)

    @staticmethod
    def score(t: Task, submission: str):
        if isinstance(submission, str):
            submission = submission.strip()
        elif isinstance(submission, dict):
            submission = submission["value"]
        else:
            submission = submission

        return submission