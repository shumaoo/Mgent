"""Deterministic permission policy for Mgent tool calls.

This module is the *authority* layer. It answers one question for every tool
call: allow, ask, or deny. The language model never calls into this module and
cannot change its answer. Keeping the decision here — in plain Python the user
can read and audit — is what makes Mgent's safety boundary trustworthy: a
confused or prompt-injected model can request anything, but it cannot approve
its own actions.
"""

from enum import Enum
from typing import Dict


class Decision(str, Enum):
    """The outcome of a permission check for a single tool call."""

    ALLOW = "allow"  # run without asking
    ASK = "ask"      # run only after the user approves
    DENY = "deny"    # never run; report the refusal back to the model


class PermissionMode(str, Enum):
    """A user-selected global posture that can override per-tool defaults."""

    DEFAULT = "default"  # use the per-tool rules as written
    AUTO = "auto"        # reads allowed; mutating actions still ask
    YOLO = "yolo"        # allow everything; skip all prompts (explicit opt-in)


# Per-tool base policy. Read-only tools are safe to run automatically; any tool
# that changes the machine defaults to ASK. A tool absent from this map is
# treated as ASK — unknown capability is never silently trusted.
DEFAULT_TOOL_RULES: Dict[str, Decision] = {
    "list_directory": Decision.ALLOW,
    "read_file": Decision.ALLOW,
    "edit_file": Decision.ASK,
}

# Tools known to be read-only (no machine mutation). AUTO mode auto-allows ONLY
# these. The check is an allowlist, not "is it mutating?" — so an unknown tool
# (which is in neither set) still asks in AUTO mode, preserving fail-closed.
READ_ONLY_TOOLS = {"list_directory", "read_file"}


def decide(tool_name: str, mode: PermissionMode) -> Decision:
    """Decide whether a tool call may run, must ask, or must be denied.

    The model has no input here — only the tool name and the user-selected mode.
    """
    base = DEFAULT_TOOL_RULES.get(
        tool_name,
        # Fail closed: an unrecognized tool is treated as needing approval.
        Decision.ASK,
    )

    # A per-tool DENY is absolute and cannot be loosened by any mode.
    if base is Decision.DENY:
        return Decision.DENY

    if mode is PermissionMode.YOLO:
        return Decision.ALLOW

    if mode is PermissionMode.AUTO:
        # Allowlist: only provably read-only tools run automatically.
        # Everything else — including unknown tools — still asks.
        if tool_name in READ_ONLY_TOOLS:
            return Decision.ALLOW
        return Decision.ASK

    # DEFAULT mode: honor the per-tool rule exactly.
    return base
