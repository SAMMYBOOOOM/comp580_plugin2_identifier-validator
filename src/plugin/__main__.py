"""MCP stdio server entry point for the Identifier Validator plugin."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from plugin.validate_identifier import validate_identifier

SERVER_NAME = "identifier-validator"

mcp = FastMCP(SERVER_NAME)

IMPLEMENTATIONS = {
    "validate_identifier": validate_identifier,
}

for _tool_name, _tool_fn in IMPLEMENTATIONS.items():
    mcp.add_tool(_tool_fn, name=_tool_name)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()