# Mini Developer Automation System using MCP

## What it does
A small Python command-line application that demonstrates real Model Context Protocol (MCP) client-server communication. The client starts the MCP server as a subprocess over `stdio`, discovers its tools, and calls them.

### Included MCP tools
1. `list_files` — lists files/folders inside `workspace/`.
2. `check_python_syntax` — parses a Python file and reports syntax errors.
3. `generate_report` — checks Python files in a selected workspace file or folder and saves a timestamped report under `reports/` (outside `workspace/`).

## Requirements
- Python 3.11 or newer recommended
- Internet access for installing the MCP Python SDK

## Setup (Windows / VS Code)
Open a terminal in this folder:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python client.py
```

The client launches `server.py` automatically. You do not need to start the server in a second terminal.

## Setup (macOS / Linux)
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python client.py
```

## Try it
- Choose `1` to list files in the workspace.
- Choose `2`, then enter `sample.py`, to check its syntax.
- Choose `3`, then enter a workspace file or folder (or press Enter for the workspace root). The tool checks Python syntax for each Python file in the target and saves a report under `reports/`.
- Choose `4` to exit.

To test syntax-error handling, temporarily edit `workspace/sample.py` and introduce a Python syntax error, then run option 2 again.

## Architecture
`client.py` → MCP client session → JSON-RPC over stdio → `server.py` → Python tool functions → result returned to client.

## Safety and scope
Source files checked by the tools are constrained to the `workspace/` directory. Generated reports are saved separately under `reports/`. This is a learning micro-project, not a production service. It intentionally does not execute arbitrary shell commands or modify source code.

## Troubleshooting
- If `No module named mcp` appears, activate the virtual environment and run `pip install -r requirements.txt`.
- If a dependency error occurs, check that Python is 3.11+ and reinstall using `python -m pip install -r requirements.txt`.
- Keep standard output free of debug prints in `server.py`, because stdout is used by the MCP stdio protocol.
