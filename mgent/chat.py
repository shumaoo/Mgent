import sys

import anthropic


MODEL = "claude-opus-4-8"
SYSTEM_PROMPT = "You are Mgent, a helpful AI assistant."


def run_chat_loop(client: anthropic.Anthropic) -> int:
    """Run Mgent's interactive terminal chat loop."""
    messages: list[anthropic.types.MessageParam] = []

    print("Mgent is ready. Type 'exit' or 'quit' to stop.\n")

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

        messages.append({"role": "user", "content": user_input})

        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                print("Mgent: ", end="", flush=True)
                for text in stream.text_stream:
                    print(text, end="", flush=True)

                response = stream.get_final_message()
                print("\n")
        except anthropic.AuthenticationError:
            print("Authentication failed. Check ANTHROPIC_API_KEY in your .env file.", file=sys.stderr)
            messages.pop()
            continue
        except anthropic.APIError as error:
            print(f"Anthropic API error: {error}", file=sys.stderr)
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": response.content})
