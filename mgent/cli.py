import argparse

from mgent.anthropic_client import create_client
from mgent.chat import run_chat_loop
from mgent.permissions import PermissionMode


def main() -> int:
    """CLI entry point for Mgent."""
    args = _parse_args()

    client = create_client()
    if client is None:
        return 1

    return run_chat_loop(client, mode=args.mode)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mgent",
        description="Mgent — a local coding assistant powered by Claude.",
    )
    parser.add_argument(
        "--mode",
        type=PermissionMode,
        choices=list(PermissionMode),
        default=PermissionMode.DEFAULT,
        metavar="{default,auto,yolo}",
        help=(
            "Permission mode. "
            "default: ask before file edits. "
            "auto: allow reads, still ask for edits. "
            "yolo: allow everything without prompts (use with care)."
        ),
    )
    return parser.parse_args()
