# Backend

FastAPI service for authentication, video inspection, task orchestration, and result retrieval.

## Main responsibilities

- public URL inspection with `yt-dlp`
- quota enforcement and audit logging
- asynchronous task execution
- transcript and summary persistence
- subtitle and auto-caption extraction via `yt-dlp`
- live summarization via DeepSeek chat API

## Local commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## Required runtime tools

- `yt-dlp` is installed from `requirements.txt`

## Required environment variables for DeepSeek-only processing

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

Recommended values:

```env
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
```

In this DeepSeek-only mode, summary generation requires the source video to expose subtitles or auto-captions. If no usable subtitles exist, task execution fails with a clear error instead of silently inventing a transcript.
