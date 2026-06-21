from mgent.anthropic_client import create_client
from mgent.chat import run_chat_loop


def main() -> int:
    """CLI entry point for Mgent."""
    client = create_client()
    if client is None:
        return 1

    return run_chat_loop(client)
