import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent
SERVER_FILE = ROOT / "server.py"


async def call_tool(session, name, arguments):
    """Call an MCP tool and print its returned content."""
    result = await session.call_tool(name, arguments=arguments)
    if getattr(result, "isError", False):
        print("Tool returned an error.")
    for item in result.content:
        if hasattr(item, "text"):
            print(item.text)
        else:
            print(item)
    return result


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
        cwd=str(ROOT),
    )

    # The client launches server.py and communicates using MCP over stdio.
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            print("\nMINI DEVELOPER AUTOMATION SYSTEM")
            print("--------------------------------")
            print("MCP connection established.")
            print("Discovered tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            while True:
                print("\n1. List workspace files")
                print("2. Check Python syntax")
                print("3. Generate report")
                print("4. Exit")
                choice = input("Choose an option: ").strip()

                try:
                    if choice == "1":
                        directory = input("Directory (press Enter for workspace root): ").strip() or "."
                        await call_tool(session, "list_files", {"directory": directory})

                    elif choice == "2":
                        filename = input("Python filename (e.g. sample.py): ").strip()
                        await call_tool(
                            session,
                            "check_python_syntax",
                            {"filename": filename},
                        )

                    elif choice == "3":
                        target_path = (
                            input(
                                "Workspace file or folder to check "
                                "(press Enter for workspace root): "
                            ).strip()
                            or "."
                        )
                        await call_tool(
                            session,
                            "generate_report",
                            {"target_path": target_path},
                        )

                    elif choice == "4":
                        print("Exiting.")
                        break

                    else:
                        print("Invalid choice. Enter 1, 2, 3, or 4.")

                except Exception as exc:
                    print(f"Operation failed: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
