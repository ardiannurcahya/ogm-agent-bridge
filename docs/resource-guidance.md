# Resource guidance

Bridge process is light: Python stdio MCP, SQLite state, and HTTP requests. Core does retrieval, ingestion, databases, vector/graph work, and document processing.

## 2 vCPU / 2 GB

2 vCPU and 2 GB can suit bridge plus harness for low-concurrency local use when core runs elsewhere. This is bridge guidance only. It does **not** validate OpenGraphMemory core on 2 vCPU/2 GB, and does not include core dependencies.

Keep core separate. Size core from its own deployment requirements, dataset size, ingestion load, graph/vector services, model providers, and concurrent query traffic.

## Bridge sizing signals

Watch:

- concurrent harness sessions and MCP calls;
- request latency and timeout rate;
- upload file size and local disk throughput;
- SQLite state disk capacity and backup retention;
- stderr log volume;
- core `502`, `503`, transport, and timeout failures.

## Practical limits

- Keep one bridge process per project/config.
- Use narrow upload roots; upload streams through bridge process.
- Keep state on persistent local disk, not ephemeral temp directory.
- Set timeout from observed core latency; default 30 seconds.
- `OGM_MAX_RETRIES=2` limits eligible transient retries. Writes are not retried.

For reliability, isolate core resources from agent/harness resources. See [configuration](configuration.md), [security](security.md), [architecture](architecture.md), and [API audit](api-audit.md).
