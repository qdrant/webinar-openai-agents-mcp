# Webinar: Using MCP to Orchestrate AI Agents

This repository contains the code for the webinar demonstrating how to use Model Context Protocol (MCP) to orchestrate AI Agents with OpenAI SDK, Augment Code, and Qdrant.

> [!NOTE]
> If you would like to see the Django application created during the webinar, please check the
> [simple-django-app](src/simple-django-app) directory.

## Overview

The project showcases how to:
- Build a pipeline of AI agents for processing documentation
- Use OpenAI's Agent SDK for natural language processing
- Integrate Qdrant's MCP server for vector search capabilities
- Store and retrieve code snippets with semantic context through the [mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant)

## Project Structure

```
.
├── src/
│   └── code-indexing-agents/
│       ├── main.py           # Main application logic
│       ├── models.py         # Pydantic models
│       └── helper.py         # Utility functions
├── poetry.lock              # Poetry dependencies lock file
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Prerequisites

- Python 3.10 or higher
- Poetry package manager
- Qdrant instance (cloud or self-hosted)
- OpenAI API key

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/qdrant/webinar-openai-agents-mcp.git
    cd webinar-openai-agents-mcp
    ```

2. Install dependencies using Poetry:
    ```bash
    poetry install
    ```

3. Create a `.env` file with your configuration:
    ```bash
    QDRANT_URL=<your-qdrant-url>
    QDRANT_API_KEY=<your-qdrant-api-key>
    COLLECTION_NAME=<your-collection-name>
    TOOL_STORE_DESCRIPTION=<description-for-store-tool>
    TOOL_FIND_DESCRIPTION=<description-for-find-tool>
    ```

## Usage

Run the main script to collect and process documentation:

```bash
poetry run python src/code-indexing-agents/main.py
```

The script will use the input query to find the documentation of a Python package, parse it, and store the code
snippets in Qdrant through the MCP server.

> [!NOTE]
> Please modify the `main.py` file to pass a different request. By default, we load the docs of django-semantic-search

## License

Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
