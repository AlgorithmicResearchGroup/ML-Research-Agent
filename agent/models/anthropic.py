import os
import anthropic
from agent.utils import count_tokens
import json
import tiktoken

class AnthropicModel:
    def __init__(self, system_prompt, all_tools):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC"))
        self.system_prompt = system_prompt
        self.all_tools = all_tools
        self.max_tokens = 200000  # Maximum tokens for Claude-3
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def encode_text(self, text):
        return self.encoding.encode(text, disallowed_special=())

    def decode_tokens(self, tokens):
        return self.encoding.decode(tokens)

    def truncate_prompt(self, prompt, max_tokens):
        tokens = self.encode_text(prompt)
        if len(tokens) <= max_tokens:
            return prompt
        return self.decode_tokens(tokens[:max_tokens])

    def generate_response(self, prompt):
        system_prompt_tokens = len(self.encode_text(self.system_prompt))
        available_tokens = self.max_tokens - system_prompt_tokens - 100

        truncated_prompt = self.truncate_prompt(prompt, available_tokens)
        prompt_tokens = len(self.encode_text(truncated_prompt))

        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            messages=[
                {"role": "user", "content": self.system_prompt + "\n" + truncated_prompt},
            ],
            temperature=0,
            max_tokens=1024,
            tools=self.all_tools,
        )
        response_data, response_tokens = self.get_anthropic_response(response)
        total_tokens = system_prompt_tokens + prompt_tokens + response_tokens

        return response_data, total_tokens, prompt_tokens, response_tokens

    def get_anthropic_response(self, response):
        response_data = None
        response_tokens = 0

        if hasattr(response, "content") and len(response.content) > 0:
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            if tool_use_blocks:
                first_tool_use_block = tool_use_blocks[0]
                if hasattr(first_tool_use_block, "input") and first_tool_use_block.input:
                    response_data = json.loads(first_tool_use_block.input)
                    response_tokens = count_tokens(json.dumps(response_data), "cl100k_base")
            else:
                text_blocks = [block.text for block in response.content if block.type == "text"]
                response_data = " ".join(text_blocks) if text_blocks else None
                response_tokens = count_tokens(response_data, "cl100k_base") if response_data else 0

        return response_data, response_tokens
