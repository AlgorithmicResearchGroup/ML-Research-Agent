from rich import print
from rich.panel import Panel
from rich.text import Text

from agent.tools.bash.bash_tool import run_bash, bash_tool_definitions
from agent.tools.code.code_tool import (
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
from agent.tools.thought.thought_tool import use_thought, thought_tool_definitions
from agent.tools.long_term_memory.long_term_memory_tool import (
    use_long_term_memory,
    long_term_memory_tool_definitions,
)

from agent.tools.internet.internet_tool import search_the_internet, internet_search_tool_definitions
from agent.tools.paperswithcode.paperswithcode_tool import (
    get_code_links,
    get_paper_details_pwc,
    search_paperswithcode,
    paperswithcode_tool_definitions,
)


def collect_tools(*lists):
    merged_list = []
    for lst in lists:
        merged_list.extend(lst)
    return merged_list


coding_agent_tools = collect_tools(
    code_tool_definitions,
    github_tool_definitions,
    scratchpad_tool_definitions,
    thought_tool_definitions,
)

execution_agent_tools = collect_tools(
    bash_tool_definitions,
    python_tool_definitions,
    return_fn_tool_definitions,
    scratchpad_tool_definitions,
    thought_tool_definitions,
)


research_agent_tools = collect_tools(
    internet_search_tool_definitions,
    semantic_scholar_tool_definitions,
    scratchpad_tool_definitions,
    thought_tool_definitions,
    paperswithcode_tool_definitions,
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
    # "search_papers": "query",
    "get_paper_details": "paper_id",
    "get_paper_abstract": "paper_id",
    "get_paper_citations": "paper_id",
    "download_paper": "paper_id",
    "thought": "thought",
    "search_the_internet": "query",
    "search_paperswithcode": "query",
    "get_code_links": "paper_id",
    "get_paper_details_pwc": "paper_id",
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
            #"search_papers": search_papers,
            "get_paper_details": get_paper_details,
            "get_paper_citations": get_paper_citations,
            "download_paper": download_paper,
            "thought": use_thought,
            "search_the_internet": search_the_internet,
            "search_paperswithcode": search_paperswithcode,
            "get_code_links": get_code_links,
            "get_paper_details_pwc": get_paper_details_pwc,
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
