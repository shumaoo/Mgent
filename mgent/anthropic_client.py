import os
import sys
from typing import Optional

import anthropic
from dotenv import load_dotenv


def create_client() -> Optional[anthropic.Anthropic]:
    """Create an Anthropic client from environment configuration."""
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Missing ANTHROPIC_API_KEY. Add it to your .env file.", file=sys.stderr)
        return None

    return anthropic.Anthropic()
