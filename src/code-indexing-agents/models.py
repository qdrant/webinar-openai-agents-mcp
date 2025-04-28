from pydantic import BaseModel, Field


class Package(BaseModel):
    package_name: str = Field(description="Name of the Python package")
    version: str | None = Field(None, description="Version of the Python package. Optional")


class PackageDocumentation(Package):
    package_name: str = Field(description="Name of the Python package")
    version: str | None = Field(None, description="Version of the Python package. Optional")
    documentation_url: str | None = Field(None, description="URL of the main documentation page")


class MarkdownContent(BaseModel):
    markdown_content: str = Field(description="Markdown-formatted content")


class CodeSnippet(BaseModel):
    code_snippet: str = Field(description="Code snippet extracted from the documentation")
    textual_description: str = Field(description="Textual description of the code snippet")
