import os
import sys
from pathlib import Path


def ensure_project_venv() -> None:
    """Re-exec with the backend .venv on Windows when run.py is launched by a global Python."""
    if os.environ.get("MINDNEST_SKIP_VENV_REEXEC") == "1":
        return

    project_dir = Path(__file__).resolve().parent
    if os.name == "nt":
        venv_python = project_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = project_dir / ".venv" / "bin" / "python"

    if not venv_python.exists():
        return

    current = Path(sys.executable).resolve()
    target = venv_python.resolve()
    if current == target:
        return

    env = os.environ.copy()
    env["MINDNEST_SKIP_VENV_REEXEC"] = "1"
    os.execve(str(target), [str(target), str(Path(__file__).resolve()), *sys.argv[1:]], env)


if __name__ == "__main__":
    ensure_project_venv()

    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
