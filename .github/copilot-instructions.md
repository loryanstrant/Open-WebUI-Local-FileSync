# Copilot instructions — Open-WebUI-Local-FileSync

> Canonical standards live in the `dev-standards` repo on SOUNDWAVE/Gitea.
> Read by Copilot chat **and** inline suggestions.

## What this repo is

A standalone **Dockerised Python service** that syncs local files into Open-WebUI,
with a web interface. Core logic in `sync.py` + `web.py`. Not a Home Assistant
component.

## Repo shape

- `sync.py` — the sync engine (large; the heart of the project).
- `web.py` — web interface.
- `config.py` — configuration handling.
- `Dockerfile`, `docker-compose.yml`, `docker-compose-ssh-example.yml`,
  `entrypoint.sh`.
- Extensive docs: `CONFIGURATION.md`, `DEPLOYMENT.md`, `EXAMPLES.md`,
  `QUICKSTART.md`, `STATE_FORMAT.md`, `TROUBLESHOOTING.md`, `WEB_INTERFACE.md`,
  `FLOW_DIAGRAM.md`.

## Conventions

- Python service, not an HA integration: no `manifest.json`/`hassfest`/HACS.
- Keep the docs set in step with behaviour — this project documents heavily;
  update the relevant `.md` when changing config keys or the state format.
- Config via `config.py` + env / compose; never commit real credentials, API
  keys, or SSH keys (there's an SSH compose example — keep secrets out of it).
- Ship changes as a rebuilt Docker image (`.github/workflows/docker-build.yml`).

## Never

- Don't commit credentials, tokens, or SSH keys.
