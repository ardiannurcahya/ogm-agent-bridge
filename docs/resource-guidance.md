# Resource Guidance

Bridge is lightweight Python stdio plus HTTP. Core owns document ingestion, PostgreSQL, graph projection, and analytics workload.

Watch concurrent MCP calls, core latency, upload size, stderr volume, and core `502`/`503`/timeout rate. Keep one bridge process per project config. Set timeout from observed core latency; default is 30 seconds.
