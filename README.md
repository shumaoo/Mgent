# Mgent

Mgent is a command-line coding agent prototype powered by Claude.

The current version supports an interactive terminal chat loop. The project is structured as a Python package so it can grow from a simple script into a real CLI tool.

## Project Structure

```text
Mgent/
├── main.py                  # Backward-compatible script entry point
├── pyproject.toml           # Package metadata and CLI command mapping
├── requirements.txt         # Dependency list for simple setup
├── setup.py                 # Minimal editable-install compatibility shim
└── mgent/
    ├── __init__.py          # Marks mgent as a Python package
    ├── __main__.py          # Enables python -m mgent
    ├── anthropic_client.py  # Loads environment and creates Anthropic client
    ├── chat.py              # Runs the interactive chat loop
    └── cli.py               # CLI entry point that wires components together
```

## Environment Setup

Create a `.env` file with your Anthropic API key:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run From Source

You can still run the original script entry point:

```bash
python main.py
```

You can also run Mgent as a Python package:

```bash
python -m mgent
```

Both commands start the same chat loop.

## Install As a CLI

To install Mgent as an editable local package:

```bash
python -m pip install -e .
```

Then run:

```bash
mgent
```

Editable mode means changes to files inside `mgent/` are picked up without reinstalling.

## If Editable Install Fails

If you see an error like:

```text
No module named pip
```

then the active Python environment needs `pip` repaired. Try:

```bash
python -m ensurepip --upgrade
python -m pip install -e .
```

If that still fails, create a clean virtual environment and install again.

## Stop Chatting

Inside the chat loop, type:

```text
exit
```

or:

```text
quit
```

## Architecture Notes

Mgent separates responsibilities across small modules:

- `cli.py` starts the app and delegates work.
- `chat.py` owns the multi-turn conversation loop.
- `anthropic_client.py` owns Claude API client setup.
- `main.py` preserves backward compatibility for `python main.py`.

This design makes the project easier to test, extend, and explain in interviews.
