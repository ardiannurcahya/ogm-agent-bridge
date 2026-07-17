# Configuration

Bridge loads `.env` without overriding process environment. One process serves one project.

| Variable | Required | Default | Rule |
|---|---:|---|---|
| `OGM_BASE_URL` | yes | none | Core API URL; trailing `/` removed. |
| `OGM_API_KEY` | yes | none | Project API key. |
| `OGM_PROJECT_ID` | yes | none | UUID sent as `X-Project-Id`. |
| `OGM_TIMEOUT_SECONDS` | no | `30.0` | Positive number. |
| `OGM_MAX_RETRIES` | no | `2` | Non-negative integer for transient requests. |
| `OGM_PERMISSION_PROFILE` | no | `personal-safe` | `read-only` or `personal-safe`. |
| `OGM_UPLOAD_ROOTS` | no | process working directory | OS-path-separator list of resolved roots. |

`read-only` permits health, datasets, and all graph read tools. `personal-safe` adds document upload. No full profile exists.

```env
OGM_BASE_URL=http://localhost:8000
OGM_API_KEY=<project-api-key>
OGM_PROJECT_ID=<project-uuid>
OGM_PERMISSION_PROFILE=read-only
# OGM_UPLOAD_ROOTS=/srv/approved:/home/me/project/docs
```

For multiple projects, use separate bridge processes and environment files. No local bridge state needs backup or migration.
