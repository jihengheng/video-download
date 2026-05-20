# Video Research Studio

Monorepo for a public-facing video research and download MVP.

## Structure

- `frontend/` - Vue 3 + Element Plus client
- `backend/` - FastAPI API and worker services
- `infra/` - deployment examples and local compose file
- `docs/` - project notes

## Product Scope

The product focuses on public video analysis workflows:

1. Inspect a public video URL
2. Select a downloadable format
3. Queue a processing task
4. Download media, extract audio, transcribe, and summarize
5. Review history and export outputs

## Local Development

See `backend/README.md` and `frontend/README.md` after installing dependencies.
