from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from mgent.path_safety import PathSafetyError, ensure_text_file, resolve_workspace_path


TOOLS: List[Dict[str, Any]] = [
    {
        "name": "list_directory",
        "description": (
            "List files and folders inside the current workspace. "
            "Call this when you need to inspect project structure. "
            "This tool does not modify files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to the workspace root. Use '.' for the workspace root.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read a UTF-8 text file inside the current workspace. "
            "Call this when you need accurate contents of a local file. "
            "This tool does not modify files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to the workspace root.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Edit an existing UTF-8 text file by replacing exact text. "
            "Call this only when the user asks you to change a local file. "
            "Use small, precise replacements. This action may require user approval before it runs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to the workspace root.",
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact text currently in the file that should be replaced.",
                },
                "new_text": {
                    "type": "string",
                    "description": "Replacement text to write into the file.",
                },
                "reason": {
                    "type": "string",
                    "description": "Short explanation of why this edit is needed, shown to the user during approval.",
                },
            },
            "required": ["path", "old_text", "new_text"],
            "additionalProperties": False,
        },
    },
]


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


def execute_tool(
    name: str,
    tool_input: Dict[str, Any],
    workspace_root: Path,
) -> ToolResult:
    """Execute one local tool request.

    Permission to run has already been granted by the caller (the agent loop
    consults the policy in mgent.permissions). This function performs the work;
    it does not decide whether the work is allowed.
    """
    try:
        if name == "list_directory":
            return _list_directory(tool_input, workspace_root)
        if name == "read_file":
            return _read_file(tool_input, workspace_root)
        if name == "edit_file":
            return _edit_file(tool_input, workspace_root)
        return ToolResult(f"Unknown tool requested: {name}", is_error=True)
    except PathSafetyError as error:
        return ToolResult(f"Path safety error: {error}", is_error=True)
    except OSError as error:
        return ToolResult(f"Filesystem error: {error}", is_error=True)


def _list_directory(tool_input: Dict[str, Any], workspace_root: Path) -> ToolResult:
    path = resolve_workspace_path(workspace_root, str(tool_input.get("path", ".")))
    if not path.exists():
        return ToolResult(f"Directory does not exist: {tool_input.get('path')}", is_error=True)
    if not path.is_dir():
        return ToolResult("Path is not a directory.", is_error=True)

    entries = []
    for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        if child.name in {".git", ".venv", "__pycache__"}:
            continue
        suffix = "/" if child.is_dir() else ""
        entries.append(f"{child.name}{suffix}")
        if len(entries) >= 200:
            entries.append("... output truncated after 200 entries")
            break

    if not entries:
        return ToolResult("Directory is empty.")

    return ToolResult("\n".join(entries))


def _read_file(tool_input: Dict[str, Any], workspace_root: Path) -> ToolResult:
    path = resolve_workspace_path(workspace_root, str(tool_input.get("path", "")))
    ensure_text_file(path)
    return ToolResult(path.read_text(encoding="utf-8"))


def _edit_file(
    tool_input: Dict[str, Any],
    workspace_root: Path,
) -> ToolResult:
    path = resolve_workspace_path(workspace_root, str(tool_input.get("path", "")))
    ensure_text_file(path)

    old_text = str(tool_input.get("old_text", ""))
    new_text = str(tool_input.get("new_text", ""))

    if not old_text:
        return ToolResult("old_text cannot be empty.", is_error=True)

    content = path.read_text(encoding="utf-8")
    occurrences = content.count(old_text)
    if occurrences == 0:
        return ToolResult("old_text was not found in the file.", is_error=True)
    if occurrences > 1:
        return ToolResult(
            f"old_text appears {occurrences} times. Refusing ambiguous edit.",
            is_error=True,
        )

    path.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    return ToolResult(f"Edited file: {path.relative_to(workspace_root.resolve())}")
