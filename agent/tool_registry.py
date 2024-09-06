from rich import print
from rich.panel import Panel
from rich.text import Text

from agent.tools.bash.bash_tool import run_bash, bash_tool_definitions
from agent.tools.code.code_tool import (
    #read_code_tool,
    write_code,
    insert_code,
    replace_code,
    delete_code,
    code_tool_definitions,
)
from agent.tools.github.github_tool import (
    github_get_readme,
    github_list_files,
    github_get_file_code,
    github_tool_definitions,
)
from agent.tools.semantic_scholar.semantic_scholar_tool import (
    search_papers,
    get_paper_details,
    get_paper_citations,
    download_paper,
    semantic_scholar_tool_definitions,
)
from agent.tools.python.python_tool import run_python, python_tool_definitions
from agent.tools.return_fn.return_fn_tool import return_fn, return_fn_tool_definitions
from agent.tools.scratchpad.scratchpad_tool import (
    use_scratchpad,
    scratchpad_tool_definitions,
)
from agent.tools.thought.thought_tool import use_thought, update_todo, update_multiple_tasks, thought_tool_definitions
from agent.tools.long_term_memory.long_term_memory_tool import use_long_term_memory, long_term_memory_tool_definitions

def collect_all_tools(*lists):
    merged_list = []
    for lst in lists:
        merged_list.extend(lst)
    return merged_list


all_tools = collect_all_tools(
    bash_tool_definitions,
    code_tool_definitions,
    github_tool_definitions,
    semantic_scholar_tool_definitions,
    python_tool_definitions,
    return_fn_tool_definitions,
    scratchpad_tool_definitions,
    thought_tool_definitions,
    long_term_memory_tool_definitions,
)


worker_action_map = {
    "run_python": "filepath",
    "run_bash": "script",
    "return_fn": ["submission", "model_path"],
    "write_code": ["path", "code"],
    "insert_code": ["path", "target", "new_code"],
    "replace_code": ["path", "old_code", "new_code"],
    "delete_code": ["path", "target"],
    "scratchpad": ["path", "note", "action"],
    "github_get_readme": "repo_url",
    "github_list_files": "repo_url",
    "github_get_file_code": ["repo_url", "file_path"],
    "search_papers": "query",
    "get_paper_details": "paper_id",
    "get_paper_abstract": "paper_id",
    "get_paper_citations": "paper_id",
    "download_paper": "paper_id",
    "thought": "thought",
    "long_term_memory": ["query", "run_id"],
    "update_todo": "todo",
    "update_multiple_tasks": "tasks",
    # "lookup_papers": "query",
    # "lookup_code": "query"
}


class Tool:
    def __init__(self, task):
        self.task = task

    def print_human_readable(self, data, action):
        if isinstance(data, dict):
            output = []
            for key, value in data.items():
                output.append(f"{key.capitalize()}: {value} \n")
            text = "\n".join(output)
            panel = Panel(Text(f"{action} --- {text}"), style="on blue")
            print(panel)
        elif isinstance(data, list):
            output = []
            for item in data:
                output.append(f"[magenta] {item}")
            text = "\n".join(output)
            panel = Panel(Text(f"{action} --- {text}"), style="on green")
            print(panel)
        else:
            panel = Panel(Text(f"{action} --- {data}"), style="on magenta")
            print(panel)

    def run(self):
        function_mapping = {
            "run_python": run_python,
            "run_bash": run_bash,
            "return_fn": return_fn,
            "write_code": write_code,
            "insert_code": insert_code,
            "replace_code": replace_code,
            "delete_code": delete_code,
            "scratchpad": use_scratchpad,
            "github_get_readme": github_get_readme,
            "github_list_files": github_list_files,
            "github_get_file_code": github_get_file_code,
            "search_papers": search_papers,
            "get_paper_details": get_paper_details,
            "get_paper_citations": get_paper_citations,
            "download_paper": download_paper,
            "thought": use_thought,
            "update_todo": update_todo,
            "update_multiple_tasks": update_multiple_tasks,
            "long_term_memory": use_long_term_memory,
            # "code_lookup": code_lookup,
            # "paper_lookup": paper_lookup
        }

        if self.task["type"] == "function":
            function_name = self.task["function"]["name"]
            if function_name in function_mapping:
                self.print_human_readable(
                    self.task["function"]["parameters"], function_name
                )
                return function_mapping[function_name](
                    self.task["function"]["parameters"]
                )
            else:
                return {"subtask_result": "Invalid task", "attempted": "no"}
        else:
            return {"subtask_result": "Invalid task", "attempted": "no"}
