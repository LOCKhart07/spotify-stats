# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small FastAPI service (Python 3.11) that acts as an authenticated, Redis-cached
proxy in front of the Spotify Web API's "top tracks / artists / genres" endpoints.
It exists so a portfolio frontend can fetch the owner's listening stats without
exposing Spotify credentials or hitting Spotify's rate limits. There is no
database, no test suite, and no linter configured — the entire app is the three
files under `app/`.

## Commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/): `pyproject.toml`
declares them (pinned with `==`) and `uv.lock` pins the full resolved tree. There
is no `requirements.txt`. Add/remove deps with `uv add` / `uv remove` (which
update both files); regenerate the lock with `uv lock`.

Run locally (needs a reachable Redis and a populated `.env`, see below):

```bash
uv sync                                                          # install from uv.lock into .venv
uv run uvicorn app.main:app --host 0.0.0.0 --port 9000           # or: uv run python -m app.main
```

Run via Docker (the supported path; image is `ghcr.io/lockhart07/spotify-stats`):

```bash
docker compose up -d          # expects an external Docker network named "backend"
```

Health check: `GET /ping` → `{"message": "pong"}` (unauthenticated, used by the
compose healthcheck).

Required environment variables (`.env` for local, compose env / GitHub secrets in
CI): `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`,
`BEARER_TOKEN`, `REDIS_HOST`, `REDIS_PORT`, `CACHE_TTL`.

## Architecture

**Request pipeline.** Each API route in `app/main.py` is wrapped by three stacked
decorators whose order is load-bearing:

```
@router.get(...)        # FastAPI route + response_model validation
@verify_authorization   # rejects unless Authorization == "Bearer {BEARER_TOKEN}"
@redis_cache            # cache lookup, then call, then cache store
def top_tracks(...): ...
```

Auth runs before the cache, and the route handler delegates to a
`fetch_spotify_*` function in `app/service.py`. `service.py` owns all Spotify I/O:
it exchanges the refresh token for an access token (cached in Redis under
`spotify_access_token` with a hardcoded 3500s TTL), then calls
`https://api.spotify.com/v1/me/top/{tracks,artists}` and reshapes the JSON into
the Pydantic models in `app/models.py`. `top-genres` has no dedicated Spotify
endpoint — it derives genres by counting artist genres from the top-50 artists
call and sorting by frequency.

**Caching design.** `redis_cache` stores results as `str(result)` (Python repr of
a list of dicts) and reads them back with `eval()`. This means the cached
functions must return only `eval`-safe primitives, and the cache holds raw dicts,
not Pydantic models (FastAPI re-validates them against `response_model` on the way
out). Only non-`None`, non-empty results are cached.

**Routing.** All data endpoints live under the `/spotify-stats/api` prefix (an
`APIRouter`); `/ping` is registered directly on the app at the root. The service
is deployed behind a reverse proxy, so uvicorn runs with `--proxy-headers`. CORS
is locked to specific portfolio origins in `main.py`.

**Config duplication.** `main.py` and `service.py` each independently call
`load_dotenv()` and construct their own `redis.Redis` client. They also disagree
on the `CACHE_TTL` default (86400 in `main.py`, 3600 in `service.py`); the
effective TTL is whatever `main.py` uses for endpoint responses.

## Caching gotcha

`redis_cache` builds its key from `kwargs`, which FastAPI populates using the
handler's *parameter names* (`limit`, `page`, `time_range`). The lookup keys in
the decorator must match those names exactly — a prior regression used
`kwargs.get("period", ...)` instead of `"time_range"`, which silently fell back
to the `short_term` default and made all time ranges collide on one cache entry.
If you change a handler's parameter names or add cached params, update the key
construction in `redis_cache` to match.

## Deployment

Pushing to `main` (or `workflow_dispatch`) triggers
`.github/workflows/backend-build-push-deploy.yaml`: it builds a `linux/arm64/v8`
image (the `Dockerfile` copies the `uv` binary from `ghcr.io/astral-sh/uv` and
installs deps with `uv sync --frozen --no-dev` into `/code/.venv`), pushes it to
GHCR tagged `latest` and `sha-…`, then SSHes into an Oracle
host, pulls the latest `docker-compose.yaml` from `main`, and runs
`docker compose up -d` with secrets injected as environment variables.
