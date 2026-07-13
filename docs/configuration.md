# Configuration

Bridge loads `.env` without overriding already-set environment variables. One process uses one `OGM_PROJECT_ID`; run separate processes for separate projects.

## Variables

| Variable | Required | Default | Rule |
|---|---:|---|---|
| `OGM_BASE_URL` | yes | none | Non-empty URL. Trailing `/` removed. Core default commonly `http://localhost:8000`. |
| `OGM_API_KEY` | yes | none | Non-empty project API key. Never commit. |
| `OGM_PROJECT_ID` | yes | none | UUID only. Sent as `X-Project-Id`. |
| `OGM_TIMEOUT_SECONDS` | no | `30.0` | Number greater than `0`. |
| `OGM_MAX_RETRIES` | no | `2` | Integer `>= 0`. Client retries eligible transient reads; write paths disable retry. |
| `OGM_STATE_DB` | no | `~/.local/state/ogm-agent-bridge/state.db` | Expanded with `~`. SQLite mapping and identity state. |
| `OGM_PERMISSION_PROFILE` | no | `personal-safe` | Exact value `read-only` or `personal-safe`. No `full` profile. |
| `OGM_UPLOAD_ROOTS` | no | resolved current working directory | OS-path-separator list. Every entry must be non-empty; each expands and resolves. Linux/macOS separator `:`; Windows separator `;`. |

Project API calls send `X-API-Key` and `X-Project-Id`. `ogm_health` calls unauthenticated `/health`.

## Permission profiles

| Tool class | `read-only` | `personal-safe` |
|---|---:|---:|
| `ogm_health`, `ogm_list_datasets`, `ogm_query`, `ogm_search_memory` | allow | allow |
| `ogm_create_session`, `ogm_remember`, `ogm_upload_document` | deny | allow |
| Delete, update, admin, project creation | no tool | no tool |

Profile is bridge-side guard, not replacement for core project authorization.

## Upload roots

`ogm_upload_document` takes local `path`, never document content. Bridge resolves path, requires regular file, then requires file to be inside one configured resolved root. Symlinks resolve before root test. Default root is bridge process current directory.

```bash
export OGM_UPLOAD_ROOTS="$HOME/approved:/srv/team-docs"
```

Use narrow roots. Upload crosses trust boundary: selected file bytes leave local machine for configured core endpoint. See [security](security.md).

## Single project `.env`

```env
OGM_BASE_URL=http://localhost:8000
OGM_API_KEY=<project-api-key>
OGM_PROJECT_ID=<project-uuid>
OGM_TIMEOUT_SECONDS=30
OGM_MAX_RETRIES=2
OGM_STATE_DB=~/.local/state/ogm-agent-bridge/state.db
OGM_PERMISSION_PROFILE=personal-safe
# OGM_UPLOAD_ROOTS=/srv/approved:/home/me/project/docs
```

## Multiple named project configs

Do not put multiple projects in one bridge process. Keep isolated env files and state databases. Start harness-specific bridge commands with matching `env` entries.

```text
~/.config/ogm-agent-bridge/work.env
~/.config/ogm-agent-bridge/personal.env
~/.local/state/ogm-agent-bridge/work.db
~/.local/state/ogm-agent-bridge/personal.db
```

`work.env`:

```env
OGM_BASE_URL=https://ogm.work.example
OGM_API_KEY=<work-key>
OGM_PROJECT_ID=<work-project-uuid>
OGM_STATE_DB=~/.local/state/ogm-agent-bridge/work.db
OGM_PERMISSION_PROFILE=read-only
OGM_UPLOAD_ROOTS=/home/me/work/docs
```

Harness config must inject these values directly or launch wrapper command that exports them. Do not rely on bridge loading arbitrary named env files: bridge only loads default `.env` when environment is not already supplied. See [Claude Code](claude-code.md), [OpenCode](opencode.md), [Hermes](hermes.md).

## Check config

```bash
uv run ogm-agent-bridge --version
```

Missing values or invalid rules stop startup with config error. Test connection through `ogm_health`, then project auth through `ogm_list_datasets`.
