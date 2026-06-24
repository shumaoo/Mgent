from pathlib import Path


MAX_FILE_BYTES = 100_000
SENSITIVE_NAMES = {".env", ".git", ".venv", ".ssh", "__pycache__"}
SENSITIVE_SUFFIXES = {".key", ".pem"}


class PathSafetyError(ValueError):
    """Raised when a requested path is outside Mgent's safety policy."""


def resolve_workspace_path(workspace_root: Path, requested_path: str) -> Path:
    """Resolve a workspace-relative path and reject unsafe locations."""
    if not requested_path or not requested_path.strip():
        raise PathSafetyError("Path cannot be empty.")

    raw_path = Path(requested_path).expanduser()
    if raw_path.is_absolute():
        raise PathSafetyError("Absolute paths are not allowed. Use a workspace-relative path.")

    root = workspace_root.resolve()
    candidate = (root / raw_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PathSafetyError("Path is outside the allowed workspace.") from exc

    _reject_sensitive_path(root, candidate)
    return candidate


def ensure_text_file(path: Path) -> None:
    """Validate that a path points to a small readable text file."""
    if not path.exists():
        raise PathSafetyError(f"File does not exist: {path.name}")

    if not path.is_file():
        raise PathSafetyError("Path is not a file.")

    if path.stat().st_size > MAX_FILE_BYTES:
        raise PathSafetyError(f"File is too large. Limit is {MAX_FILE_BYTES} bytes.")

    try:
        with path.open("r", encoding="utf-8") as file:
            file.read(2048)
    except UnicodeDecodeError as exc:
        raise PathSafetyError("Only UTF-8 text files are supported right now.") from exc


def _reject_sensitive_path(root: Path, candidate: Path) -> None:
    relative_parts = candidate.relative_to(root).parts

    for part in relative_parts:
        if part in SENSITIVE_NAMES:
            raise PathSafetyError(f"Access to sensitive path '{part}' is not allowed.")

    if candidate.suffix in SENSITIVE_SUFFIXES:
        raise PathSafetyError(f"Access to '{candidate.suffix}' files is not allowed.")
