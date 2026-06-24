import sys
from pathlib import Path

import anthropic

from mgent.permissions import Decision, PermissionMode, decide
from mgent.tools import TOOLS, execute_tool


MODEL = "claude-opus-4-8"
SYSTEM_PROMPT = """You are Mgent, a helpful local coding assistant.

You can use local file tools to inspect and edit files inside the current workspace.
Use tools when you need accurate information about local files.
Do not claim to have read or edited files unless a tool call succeeded.
For edits, prefer small exact replacements and explain what changed afterward.

Some actions require user approval before they run. When you call a tool that
changes files, include a short "reason" describing why, so the user can make an
informed decision. If an action is denied, explain the limitation and continue.
"""
MAX_TOOL_ITERATIONS = 5


def run_chat_loop(
    client: anthropic.Anthropic,
    mode: PermissionMode = PermissionMode.DEFAULT,
) -> int:
    """Run Mgent's interactive terminal chat loop."""
    messages: list[anthropic.types.MessageParam] = []
    workspace_root = Path.cwd()

    print("Mgent is ready. Type 'exit' or 'quit' to stop.")
    print(f"Workspace: {workspace_root}")
    print(f"Permission mode: {mode.value}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return 0

        turn_start = len(messages)
        messages.append({"role": "user", "content": user_input})

        try:
            _run_agent_turn(client, messages, workspace_root, mode)
        except anthropic.AuthenticationError:
            print("Authentication failed. Check ANTHROPIC_API_KEY in your .env file.", file=sys.stderr)
            del messages[turn_start:]
            continue
        except anthropic.APIError as error:
            print(f"Anthropic API error: {error}", file=sys.stderr)
            del messages[turn_start:]
            continue


def _run_agent_turn(
    client: anthropic.Anthropic,
    messages: list[anthropic.types.MessageParam],
    workspace_root: Path,
    mode: PermissionMode,
) -> None:
    """Run one user turn, including any tool calls Claude requests."""
    for iteration in range(MAX_TOOL_ITERATIONS):
        with client.messages.stream(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOLS,
        ) as stream:
            print("Mgent: ", end="", flush=True)
            for text in stream.text_stream:
                print(text, end="", flush=True)

            response = stream.get_final_message()
            print("\n")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_results.append(_handle_tool_call(block, workspace_root, mode))

        if not tool_results:
            return

        messages.append({"role": "user", "content": tool_results})

    messages.append(
        {
            "role": "user",
            "content": "Tool iteration limit reached. Please give the best answer you can with the information already gathered.",
        }
    )
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOLS,
    ) as stream:
        print("Mgent: ", end="", flush=True)
        for text in stream.text_stream:
            print(text, end="", flush=True)
        print("\n")


def _handle_tool_call(block, workspace_root: Path, mode: PermissionMode) -> dict:
    """Apply the permission policy, then execute or refuse a single tool call."""
    decision = decide(block.name, mode)

    if decision is Decision.DENY:
        return _tool_error(block.id, f"Tool '{block.name}' is not permitted.")

    if decision is Decision.ASK and not _approve(block.name, block.input):
        return _tool_error(block.id, f"User denied permission to run '{block.name}'.")

    result = execute_tool(block.name, block.input, workspace_root)
    return {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": result.content,
        "is_error": result.is_error,
    }


def _tool_error(tool_use_id: str, message: str) -> dict:
    """Build a tool_result that reports a refusal back to Claude."""
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": message,
        "is_error": True,
    }


def _approve(tool_name: str, tool_input: dict) -> bool:
    """Ask the user to approve a sensitive tool call."""
    print(f"\nMgent wants to run: {tool_name}")

    reason = tool_input.get("reason")
    if reason:
        print(f"Reason: {reason}")

    path = tool_input.get("path")
    if path:
        print(f"Path: {path}")

    if tool_name == "edit_file":
        print("\nReplace:")
        print(_preview(str(tool_input.get("old_text", ""))))
        print("\nWith:")
        print(_preview(str(tool_input.get("new_text", ""))))

    answer = input("\nAllow this action? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def _preview(text: str, limit: int = 1000) -> str:
    """Return a bounded preview for terminal confirmation prompts."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... preview truncated ..."
