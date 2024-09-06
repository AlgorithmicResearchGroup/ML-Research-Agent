import os

thought_tool_definitions = [
    {
        "name": "thought",
        "description": "Record your thoughts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "The thought that you just had.",
                },
            },
            "required": ["thought"],
        },
    },
    {
        "name": "update_todo",
        "description": "Update the todo list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo": {
                    "type": "string",
                    "description": "The todo list.",
                },
            },
            "required": ["todo"],
        },
    },
    {
    "name": "update_multiple_tasks",
    "description": "Update multiple tasks in the todo list.",
    "input_schema": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task to update.",
                        },
                        "status": {
                            "type": "string",
                            "description": "The new status of the task (e.g., 'completed', 'in_progress', 'pending').",
                        },
                    },
                    "required": ["task", "status"],
                },
            },
        },
        "required": ["tasks"],
    },
},
]


class Thought:
    
    def return_thought(self, thought):
        try:
            return {
                "tool": "thought",
                "status": "success",
                "attempt": f"You had a thought",
                "stdout": f"{thought}",
                "stderr": "",
            }
        except Exception as e:
            return {
                "tool": "thought",
                "status": "failure",
                "attempt": "You failed to think",
                "stdout": "You failed to think",
                "stderr": str(e),
            }
    
    def update_todo(self, todo):
        try:
            return {
                "tool": "update_todo",
                "status": "success",
                "attempt": f"You updated the todo list",
                "stdout": f"{todo}",
                "stderr": "",
            }
        except Exception as e:
            return {
                "tool": "update_todo",
                "status": "failure",
                "attempt": "You failed to update the todo list",
                "stdout": "You failed to update the todo list",
                "stderr": str(e),
            }
            
            
    def update_multiple_tasks(self, tasks):
        try:
            updated_tasks = []
            for task in tasks:
                updated_tasks.append(f"Task: {task['task']}, New status: {task['status']}")
            
            return {
                "tool": "update_multiple_tasks",
                "status": "success",
                "attempt": f"You updated multiple tasks in the todo list",
                "stdout": "\n".join(updated_tasks),
                "stderr": "",
            }
        except Exception as e:
            return {
                "tool": "update_multiple_tasks",
                "status": "failure",
                "attempt": "You failed to update multiple tasks in the todo list",
                "stdout": "You failed to update multiple tasks in the todo list",
                "stderr": str(e),
            }


def use_thought(arguments):  # write to the scratchpad file
    """
    This function is used to write to the scratchpad file.
    Use this function to run the code you need to complete the task.
    """
    if isinstance(arguments, dict):
        thought = arguments["thought"]
    else:
        thought = arguments

    thought_tool = Thought()
    result = thought_tool.return_thought(thought)
    return result


def update_todo(arguments):  # write to the todo file
    """
    This function is used to write to the todo file.
    Use this function to update the todo list.
    """
    if isinstance(arguments, dict):
        todo = arguments["todo"]
    else:
        todo = arguments
    
    todo_tool = Thought()
    result = todo_tool.update_todo(todo)
    return result


def update_multiple_tasks(arguments):
    """
    This function is used to update multiple tasks in the todo list.
    """
    if isinstance(arguments, dict) and "tasks" in arguments:
        tasks = arguments["tasks"]
    else:
        raise ValueError("Invalid arguments for update_multiple_tasks")
    
    thought_tool = Thought()
    result = thought_tool.update_multiple_tasks(tasks)
    return result