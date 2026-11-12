from pathlib import Path
import ast
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Mini Developer Automation")

# All file access is restricted to this project's workspace folder.
WORKSPACE = (Path(__file__).parent / "workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)
REPORTS_DIRECTORY = (Path(__file__).parent / "reports").resolve()


def safe_path(relative_path: str) -> Path:
    """Resolve a relative path and reject paths outside WORKSPACE."""
    target = (WORKSPACE / relative_path).resolve()
    if not target.is_relative_to(WORKSPACE):
        raise ValueError("Access outside the workspace is forbidden.")
    return target


@mcp.tool()
def list_files(directory: str = ".") -> list[str]:
    """List files and folders in the workspace or one of its subfolders."""
    target = safe_path(directory)
    if not target.exists() or not target.is_dir():
        raise ValueError("The requested workspace directory does not exist.")
    return sorted(
        item.name + ("/" if item.is_dir() else "")
        for item in target.iterdir()
    )


@mcp.tool()
def check_python_syntax(filename: str) -> dict:
    """Check a Python file in the workspace for syntax errors."""
    target = safe_path(filename)
    if not target.is_file() or target.suffix != ".py":
        raise ValueError("Provide an existing .py file inside the workspace.")

    return _check_python_syntax(target, filename)


def _check_python_syntax(target: Path, filename: str) -> dict:
    source = target.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=target.name)
        return {
            "filename": filename,
            "status": "PASSED",
            "message": "No Python syntax errors found."
        }
    except SyntaxError as exc:
        return {
            "filename": filename,
            "status": "FAILED",
            "message": exc.msg,
            "line": exc.lineno,
            "column": exc.offset
        }


@mcp.tool()
def generate_report(target_path: str = ".") -> str:
    """Run syntax checks for Python files in a workspace file or folder and save a report."""
    selected_target = safe_path(target_path)
    if not selected_target.exists():
        raise ValueError("The requested workspace file or directory does not exist.")
    if not selected_target.is_file() and not selected_target.is_dir():
        raise ValueError("Select a workspace file or directory.")

    if selected_target.is_file():
        files = [selected_target]
    else:
        legacy_reports_directory = safe_path("reports")
        files = sorted(
            (
                item
                for item in selected_target.rglob("*")
                if item.is_file()
                and item.resolve().is_relative_to(WORKSPACE)
                and not item.resolve().is_relative_to(legacy_reports_directory)
            ),
            key=lambda item: str(item.relative_to(WORKSPACE)).casefold(),
        )

    entries = []
    passed = 0
    failed = 0
    for item in files:
        relative_path = str(item.relative_to(WORKSPACE))
        if item.suffix.lower() == ".py":
            result = _check_python_syntax(item, relative_path)
            entries.append(f"- {relative_path}: {result['status']} - {result['message']}")
            if result["status"] == "FAILED":
                failed += 1
                entries[-1] += f" (line {result['line']}, column {result['column']})"
            else:
                passed += 1
        else:
            entries.append(f"- {relative_path}: NOT CHECKED (not a Python file)")

    timestamp = datetime.now().astimezone()
    generated = timestamp.isoformat(timespec="seconds")
    title = "Workspace Check Report"
    entry_text = "\n".join(entries) if entries else "- No files found."
    report = (
        f"{title}\n"
        f"{'=' * len(title)}\n"
        f"Generated: {generated}\n"
        f"Target: {target_path}\n"
        f"Files found: {len(files)}\n"
        f"Python syntax checks: {passed} passed, {failed} failed\n\n"
        "Files and check results:\n"
        f"{entry_text}\n"
    )
    REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_name = f"report_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.txt"
    report_file = REPORTS_DIRECTORY / report_name
    report_file.write_text(report, encoding="utf-8")
    return (
        f"Report saved to reports/{report_name} "
        f"({len(report)} characters)."
    )


if __name__ == "__main__":
    # stdio transport: the MCP client starts this server as a subprocess.
    mcp.run(transport="stdio")
