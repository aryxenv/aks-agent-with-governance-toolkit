# WeatherAgent Server

## Pre-requisites

- uv
- python

## Get started

### Locally

1. venv

```pwsh
uv venv
```

2. install deps

```pwsh
uv sync
```

3. start server (no hot-reload)

```pwsh
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```
