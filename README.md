# codex-fastapi-demo

Proyecto base con FastAPI (Python 3.11+), estructura `src/` y `tests/`, lint/format con Ruff y CI en GitHub Actions.

## Requisitos

- Python 3.11+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -e .[dev]
```

## Ejecutar en local

```bash
python -m uvicorn app.main:app --reload
```

## Tests

```bash
pytest -q
```

## Lint y formato

```bash
ruff check .
ruff format --check .
```
