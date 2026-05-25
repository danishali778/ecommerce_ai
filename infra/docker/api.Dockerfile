FROM python:3.12-slim

WORKDIR /app

COPY apps/api/pyproject.toml /tmp/pyproject.toml

RUN pip install --no-cache-dir uv
RUN python - <<'PY'
import tomllib
from pathlib import Path

with open('/tmp/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)

deps = data['project']['dependencies']
Path('/tmp/requirements.txt').write_text('\n'.join(deps) + '\n', encoding='utf-8')
PY
RUN uv pip install --system -r /tmp/requirements.txt

COPY apps/api /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
