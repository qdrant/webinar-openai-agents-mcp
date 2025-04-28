import requests
from agents import function_tool


@function_tool
def fetch_url_content(url: str) -> str:
    """
    Fetch the content of a URL and return it as a string.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text


# TODO: add a tool to extract all the child URLs from a given URL
