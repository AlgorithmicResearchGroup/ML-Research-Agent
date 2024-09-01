import os
import anthropic
from agent.utils import count_tokens
import json

class AnthropicModel:
    def __init__(self, system_prompt, all_tools):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC"))
        self.system_prompt = system_prompt
        self.all_tools = all_tools
        
        
    def generate_response(self, prompt):
        prompt_tokens = count_tokens(prompt, "cl100k_base")
        system_prompt_tokens = count_tokens(self.system_prompt, "cl100k_base")
        response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    messages=[
                        {"role": "user", "content": self.system_prompt + "\n" + prompt},
                    ],
                    temperature=0,
                    max_tokens=1024,
                    tools=self.all_tools,
            )
        response_data, num_tokens = self.get_anthropic_response(response)
        total_tokens = prompt_tokens + system_prompt_tokens + num_tokens
        
        return response_data, total_tokens
        
        
    def get_anthropic_response(self, response):
        # Initialize default response data
        response_data = None

        # Ensure the 'content' field exists and is not empty
        if hasattr(response, "content") and len(response.content) > 0:
            tool_use_blocks = [
                block for block in response.content if block.type == "tool_use"
            ]
            # Process the first tool use block, if any
            if tool_use_blocks:
                first_tool_use_block = tool_use_blocks[0]

                # Assuming the input or relevant details are in the 'input' attribute of the tool use block
                if (
                    hasattr(first_tool_use_block, "input")
                    and first_tool_use_block.input
                ):
                    response_data = first_tool_use_block.input
                    num_tokens = 0
                return response_data, num_tokens
            else:
                # No tool use blocks found; defaulting to extracting text from text blocks
                text_blocks = [
                    block.text for block in response.content if block.type == "text"
                ]
                response_data = " ".join(text_blocks) if text_blocks else None
                num_tokens = 0

                if response_data:
                    print("Extracted text from text blocks:", response_data)
                    
                else:
                    print("No tool use blocks or text blocks found in the response.")
                    return response_data, num_tokens
        else:
            print("No content found in the response.")
            return response_data, 0
        