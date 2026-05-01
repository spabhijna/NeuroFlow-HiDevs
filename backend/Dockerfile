FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./

RUN python - <<'PY'
import subprocess
import sys
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text())
deps = data.get("project", {}).get("dependencies", [])
if not deps:
    raise SystemExit("No dependencies found in pyproject.toml")

subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--no-cache-dir", *deps]
)
PY

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]