# Mgent

Mgent is a command-line local coding assistant prototype powered by Claude.

The current version supports an interactive terminal chat loop with local file tools. Mgent can list directories, read text files, and propose exact-replacement edits with user confirmation.

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
    ├── chat.py              # Runs the agent loop and tool orchestration
    ├── cli.py               # CLI entry point that wires components together
    ├── path_safety.py       # Validates safe workspace-relative paths
    └── tools.py             # Defines and executes local file tools
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

Both commands start the same agent loop.

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

This local machine also has a global wrapper command:

```bash
Mgent
```

The wrapper points to the project virtual environment so Mgent can be launched from any directory.

## Local File Tools

Mgent currently exposes three local tools to Claude:

- `list_directory` — lists files and folders inside the current workspace.
- `read_file` — reads UTF-8 text files inside the current workspace.
- `edit_file` — edits an existing text file by exact string replacement.

## Permission Modes

A deterministic policy decides whether each tool call may run automatically,
must ask the user, or is denied. The model proposes and explains actions, but it
cannot approve its own — that decision is made in code, and the user selects the
mode from the command line:

```bash
Mgent              # default: ask before file edits
Mgent --mode auto  # allow reads, still ask for edits
Mgent --mode yolo  # allow everything without prompts (use with care)
```

When an action needs approval, Mgent prompts:

```text
Allow this action? [y/N]:
```

If denied, the action does not run and Claude receives a tool error so it can
adjust.

## Safety Rules

Mgent validates tool paths before touching the filesystem.

It blocks:

- absolute paths
- paths outside the current workspace
- `.env`
- `.git/`
- `.venv/`
- `.ssh/`
- `*.pem`
- `*.key`
- large files over 100 KB
- non-UTF-8 files

This keeps the security boundary in deterministic application code instead of relying on the model.

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
- `chat.py` owns the multi-turn agent loop and tool orchestration.
- `tools.py` defines typed local capabilities.
- `path_safety.py` enforces filesystem boundaries.
- `anthropic_client.py` owns Claude API client setup.
- `main.py` preserves backward compatibility for `python main.py`.

This design makes the project easier to test, extend, and explain in interviews.
