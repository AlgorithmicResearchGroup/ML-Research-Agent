
import requests
import os

internet_search_tool_definitions = [
    {
        "name": "search_the_internet",
        "description": "Search the internet for information on a given query using the YOU API. Use this tool to perform general web searches when you need current or general information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
            },
            "required": ["query"],
        },
    },
]


def search_the_internet(arguments):
    """
    This function searches the internet using the YOU API.
    """
    if isinstance(arguments, dict):
        query = arguments.get("query")
    else:
        query = arguments

    if not query:
        return {
            "tool": "search_the_internet",
            "status": "failure",
            "attempt": "No query provided.",
            "stdout": "",
            "stderr": "Query parameter is missing.",
        }

    try:
        api_key = "191c8cc9-d717-4936-bcaf-6053be8a5fa8<__>1Q2iODETU8N2v5f4Oonuz1G3"
        if not api_key:
            return {
                "tool": "search_the_internet",
                "status": "failure",
                "attempt": f"You tried to search for '{query}'",
                "stdout": "",
                "stderr": "YOU API key not found in environment variables.",
            }

        headers = {"X-API-Key": api_key}
        params = {"query": query}
        response = requests.get("https://api.ydc-index.io/search", headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()

        # Process the search results
        hits = search_results.get("hits", [])
        results = []
        for hit in hits[:5]:  # Limit to top 5 results
            title = hit.get("title", "No Title")
            description = hit.get("description", "")
            url = hit.get("url", "")
            snippets = hit.get("snippets", [])
            snippet_text = "\n".join(snippets)
            results.append(
                f"Title: {title}\nDescription: {description}\nURL: {url}\nSnippets:\n{snippet_text}\n{'-'*50}"
            )

        output = "\n".join(results)
        return {
            "tool": "search_the_internet",
            "status": "success",
            "attempt": f"You searched for '{query}'",
            "stdout": f"Here are the top search results:\n{output}",
            "stderr": "",
        }
    except Exception as e:
        return {
            "tool": "search_the_internet",
            "status": "failure",
            "attempt": f"You tried to search for '{query}'",
            "stdout": "",
            "stderr": str(e),
        }