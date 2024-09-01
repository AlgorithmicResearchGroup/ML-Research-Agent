import re
import tiktoken
import os


def make_directory(run_number):
    try:
        os.makedirs(f"{os.getcwd()}/{run_number}")
    except FileExistsError as e:
        print(f"Directory already exists: {run_number}")

    try:
        os.system(
            f"git clone https://github.com/Artifact-AI/nano_gpt_base {os.getcwd()}/{run_number}/nanoGPT"
        )
        os.system(  
            f"python {os.getcwd()}/{run_number}/nanoGPT/data/wiki/prepare.py"
        )
    #     os.system(
    #         f"rm -rf {os.getcwd()}/{self.run_number}/ai_research_bench/agent-eval"
    #     )
    #     os.system(
    #         f"rm -rf {os.getcwd()}/{self.run_number}/ai_research_bench/agent-runner"
    #     )
    #     os.system(
    #         f"rm -rf {os.getcwd()}/{self.run_number}/ai_research_bench/agent-tasks"
    #     )
    #     os.system(
    #         f"rm -rf {os.getcwd()}/{self.run_number}/ai_research_bench/documentation"
    #     )
    except Exception as e:
        print(f"An error occurred downloading minGPT: {str(e)}")
    return run_number

def count_tokens(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def remove_ascii(text):
    pattern = r"[\x00-\x7F]"
    # Replace all ASCII characters with an empty string
    cleaned_string = re.sub(pattern, "", text)
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    result_cleaned = re.sub(
        r"(^|\n)(Out|In)\[[0-9]+\]: ", r"\1", ansi_escape.sub("", text)
    )
    return result_cleaned


def clean_message(error_message):
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    clean_message = ansi_escape.sub("", error_message)

    # Remove leading/trailing whitespace
    clean_message = clean_message.strip()

    # Replace newline characters with spaces
    clean_message = clean_message.replace("\n", " ")

    # Replace multiple consecutive spaces with a single space
    clean_message = re.sub(r"\s+", " ", clean_message)

    return clean_message


def anthropic_to_openai(anthropic_function_call):
    openai_function_call = {
        "type": "function",
        "function": {
            "name": anthropic_function_call["name"],
            "description": anthropic_function_call["description"],
            "parameters": anthropic_function_call["input_schema"],
        },
    }
    return openai_function_call
