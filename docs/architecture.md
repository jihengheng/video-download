# Architecture Notes

## Runtime split

- `frontend/` serves the public product and authenticated workspace
- `backend/` exposes inspection, auth, task, result, and admin APIs
- `worker` processes queued media jobs
- `Redis` is reserved for queueing, rate limiting, and short-lived state
- `PostgreSQL` stores users, quota, tasks, summaries, and audit records

## Current implementation notes

- The inspection layer now uses `yt-dlp` metadata extraction directly.
- The task pipeline downloads the selected media format, extracts subtitles or automatic captions through `yt-dlp` metadata, and sends transcript text plus segment hints to DeepSeek's chat completion API for structured summarization.
- Tests mock the external networked media and AI calls so the backend suite remains deterministic.
- Task artifacts are stored in local object storage under `storage/object_store/`.
