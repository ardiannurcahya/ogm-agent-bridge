"""OpenGraphMemory MCP Server & Agent Skills."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ogm-mcp-skills")
except PackageNotFoundError:
    __version__ = "0.1.7"
