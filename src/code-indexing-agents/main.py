import asyncio
import logging
import os

from agents import Agent, Runner, WebSearchTool, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from dotenv import load_dotenv
from openai import BadRequestError
from requests import HTTPError

import models
from helper import iter_urls, download_html, on_handoff_callback

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Define the connection to Qdrant's MCP server
qdrant_mcp_server = MCPServerStdio(
    params=MCPServerStdioParams(
        command="uvx",
        args=["mcp-server-qdrant", "--transport", "stdio"],
        env={
            "QDRANT_URL": os.environ["QDRANT_URL"],
            "QDRANT_API_KEY": os.environ["QDRANT_API_KEY"],
            "COLLECTION_NAME": os.environ["COLLECTION_NAME"],
            "TOOL_STORE_DESCRIPTION": os.environ["TOOL_STORE_DESCRIPTION"],
            "TOOL_FIND_DESCRIPTION": os.environ["TOOL_FIND_DESCRIPTION"],
        },
    ),
    cache_tools_list=True,
    name="Qdrant MCP",
    client_session_timeout_seconds=20,
)

# The first two agents are responsible for parsing the requests and
# finding the desired package documentation in the web
web_search_agent = Agent(
    name="Web Search Agent",
    instructions=(
        "You are a web search agent. You are given a package name and a version, and you "
        "search for the documentation of the package. If the version is not provided, "
        "then you search for the latest version. You return the URL of the documentation "
        "page. The documentation should be:"
        "1. The main website of the project with usage examples\n"
        "2. If the tool in an SDK of a server-like project, the documentation of the server\n"
        "3. The official developer portal\n"
        "4. A technical documentation generated from the source code\n"
        "Never return PyPI project page or GitHub repository. If none of this is available, "
        "then return an empty list. Always use the web search tool provided. "
        "Please do not include API reference materials, but rather the examples. "
        "Return up to 4 results."
    ),
    tools=[
        WebSearchTool(search_context_size="high"),
    ],
    output_type=list[models.PackageDocumentation],
)
parsing_agent = Agent(
    name="Parsing agent",
    instructions=prompt_with_handoff_instructions(
        "You are a parsing agent. You are given a natural language input from the user, "
        "to pass it to the other agents in the system. Your tasks will be related to "
        "getting the documentation of a Python package, maybe in a specific version. "
        "When you get a task, you extract the name of the package, and return the name of "
        "the package and the version, if provided. If the input does not contain any "
        "information about an existing package, then provide an empty value (NULL) as a "
        "package name. Version is optional, so please only return it if it is provided. "
        "Always handoff the request to the Web Search Agent and pass the parsed package name "
        "and version to it, except when the package name is empty."
    ),
    handoffs=[
        # Here we can define the input format for the handoff
        handoff(
            agent=web_search_agent,
            on_handoff=on_handoff_callback,
            input_type=models.Package,
            # Do not include any tool call results in the handoff
            input_filter=handoff_filters.remove_all_tools,
        ),
    ],
)

# The second group of agents will handle the documentation scraping and parsing
# to the desired format. This time, we'll connect to Qdrant MCP server, and store
# the documentation there.
chunking_agent = Agent(
    name="Chunking Agent",
    instructions=prompt_with_handoff_instructions(
        "You are a seasoned software developer. You are given a Markdown-formatted text, "
        "and you need to split it into chunks of text, so it can be easily ingested by "
        "the AI model. Each chunk contains a single code snippet along with the text "
        "describing its purpose. Do not describe the code snippet in terms of HOW it does "
        "certain things, but rather WHAT it does, as if you were a user of the library. "
        "The textual description should be derived not only from the code snippet, but also "
        "from the surrounding text. Do not return duplicates, or near-duplicates. "
        "Code snippets have to really do something, not just be signatures or object "
        "creation. The description should be rather detailed and include the name of the "
        "library and some general context, to avoid confusion. "
    ),
    # Unfortunately, OpenAI Agents SDK struggles to properly handle the
    # tool calls, so we'll use the MCP server instead
    # mcp_servers=[qdrant_mcp_server],
    output_type=list[models.CodeSnippet],
)
doc_parser_agent = Agent(
    name="Documentation Parser Agent",
    instructions=prompt_with_handoff_instructions(
        "You are a documentation parser agent. You are given a URL of a documentation page, "
        "and you parse the HTML document in a way that removes all the boilerplate, "
        "and only leaves the real content of the page. "
        "Return the content of the page as Markdown-formatted text. Please make sure to "
        "extract the code snippets, as you're mostly dealing with technical documentation. "
        "Please handoff the parsed content to the Chunking Agent, so it can create digestible "
        "chunks of text."
    ),
    handoffs=[
        handoff(
            agent=chunking_agent,
            on_handoff=on_handoff_callback,
            input_type=models.MarkdownContent,
            input_filter=handoff_filters.remove_all_tools,
        )
    ],
)


async def main(query: str):
    # Load the Qdrant MCP server and connect to it
    await qdrant_mcp_server.connect()

    runner = Runner()
    response = await runner.run(parsing_agent, query)

    # We expect structured output from the agent, including the documentation URL
    docs: list[models.PackageDocumentation] = response.final_output
    if len(docs) == 0:
        print("No documentation found")
        exit(1)

    # Now, we need to recursively scrape the documentation and run the doc parsing agents
    url_queue = set(doc.documentation_url for doc in docs)
    visited_urls = set()
    while len(url_queue) > 0:
        url = url_queue.pop()
        if url in visited_urls:
            continue
        visited_urls.add(url)
        logger.info(f"Adding child URLs of {url}")
        try:
            for child_url in iter_urls(url):
                if child_url in visited_urls or child_url in url_queue:
                    continue
                url_queue.add(child_url)
        except HTTPError:
            logger.warning(f"Failed to download {url}", exc_info=False)

    # Display the visited URLs
    for url in visited_urls:
        try:
            logger.info(f"Visiting {url}")
            html_content = download_html(url)
            response = await runner.run(
                doc_parser_agent,
                f"Parse the following HTML document: {html_content}",
            )
            code_snippets: list[models.CodeSnippet] = response.final_output
            # Below, we directly call the MCP server to store the code snippets
            for snippet in code_snippets:
                await qdrant_mcp_server.call_tool(
                    "qdrant-store",
                    arguments={
                        "information": snippet.textual_description,
                        "metadata": {
                            "code": snippet.code_snippet,
                        },
                    },
                )
            logger.info(f"Stored {len(code_snippets)} code snippets from {url}")
        except HTTPError:
            logger.warning(f"Failed to download {url}", exc_info=False)
        except BadRequestError:
            logger.warning(f"Failed to parse {url}", exc_info=False)


if __name__ == "__main__":
    # Run the main function asynchronously
    asyncio.run(main("Please collect the documentation for the django-semantic-search"))
