---
name: ogm
description: >-
  OpenGraphMemory (OGM) Knowledge Graph, Codebase AST Search, Document Extraction, and Persistent Agent Operational Memory.
  Use to upload documents/specs, recall past bug fixes, search codebase symbols/call-graphs, sync AST code files, and manage persistent agent operational memories.
license: MIT
compatibility: Requires an OpenGraphMemory server and ogm-mcp-skills MCP server.
---

# OpenGraphMemory (OGM) Skill

This skill provides a comprehensive, unambiguous, production-grade operational guide for AI Agents interacting with OpenGraphMemory (OGM). It covers all three core capabilities: **Document Knowledge Graphs**, **Codebase AST Call-Graphs**, and **Persistent Agent Operational Memory**.

---

## 🎯 Task Intent Routing (English & Indonesian Triggers)

Default to using OGM whenever a task involves reading documents, navigating codebases, or executing non-trivial engineering/operational work.

### 📄 Category 1: Document Upload & Knowledge Extraction
**English Triggers:**
* *"Upload/index document spec.pdf or design.md into OGM"*
* *"Extract knowledge graph from document X"*
* *"Show evidence quotes for relation Y"*

**Indonesian Triggers:**
* *"Upload/index dokumen spec.pdf ke OGM"*
* *"Extract knowledge graph dari dokumen design.md"*
* *"Tampilkan bukti kutipan relasi Y"*

**Action Protocol:**
1. Identify dataset (`ogm_list_datasets`).
2. Upload document using `ogm_upload_document`.
3. Inspect relation evidence quotes using `ogm_get_evidence` or `ogm_get_relation_evidence`.

---

### 💻 Category 2: Codebase AST Call-Graphs & Centrality
**English Triggers:**
* *"Extract/index this codebase into OpenGraphMemory / OGM"*
* *"Build AST call-graph for project Y"*
* *"Which symbols are most connected / have top degree in repo Z?"*

**Indonesian Triggers:**
* *"Tolong extract codebase ini ke dalam knowledge graph menggunakan ogm"*
* *"Index repo ini ke dalam OGM"*
* *"Simbol apa yang paling banyak keterhubungannya / urutkan degree terbanyak"*

**Action Protocol:**
1. **Full Repo Onboarding (Oneshot)**: Call `ogm_index_codebase` with `dataset_id` and `path`.
2. **Incremental Single-File Edit**: Call `ogm_sync_code_file` when editing 1 file during pair programming.
3. **Symbol Search & Call Graphs**: Use `ogm_search_code_symbols` and `ogm_get_code_call_graph`.
4. **Degree Centrality Ranking**: Use `ogm_get_code_chunks` to fetch hub nodes sorted by degree.

---

### 🧠 Category 3: Persistent Agent Operational Memory Workflow

Use for bug fixes, errors, failed tests/builds, deployments, migrations, MCP/opencode config, GitHub PR/merge/push work, documentation changes, repository operations, incidents, research, trading, or any non-trivial engineering task: **search Agent Memory first**, **reorient when evidence changes**, then **record verified outcomes**. Skip only greetings, simple facts, and trivial one-line edits.

Use the registered `ogm` MCP Agent Memory tools:
- `ogm_memory_search` / `ogm_recall_code_memory`
- `ogm_memory_list_episodes`
- `ogm_memory_get_episode`
- `ogm_memory_create_episode`
- `ogm_memory_append_attempt`
- `ogm_memory_record_outcome` / `ogm_record_code_fix`
- `ogm_memory_feedback_episode`
- `ogm_memory_supersede_episode`
- `ogm_memory_feedback_pattern`
- `ogm_memory_supersede_pattern`

---

## 🧠 Agent Memory Detailed Protocol

### 1. Recall Before Work
Before planning, editing, deploying, merging, pushing, or diagnosing, search Agent Memory when the request is any of the following:
- A bug, regression, error message, flaky test, failed build, migration, deployment, incident, performance issue, or configuration problem.
- A task involving MCP, opencode configuration, skills, agents, plugins, GitHub, PR review, branch merge, push, release, CI, Docker, object storage, database migrations, or remote VPS operations.
- A task involving an unfamiliar subsystem, provider, dependency, repository, environment, operational runbook, or production-like runtime.
- A non-trivial implementation, documentation update, design decision, or repository cleanup where previous verified solutions could shape the plan.

Skip recall only for greetings, casual conversation, simple factual answers, obvious one-line edits, and tasks with no reusable technical context.

**Recall Protocol:**
1. Derive a concise diagnostic query from the user request, error text, failing component, or affected behavior.
2. Derive a stable lowercase hyphenated `problem_signature` when the problem is concrete. Do not invent a signature for a vague request.
3. Call `ogm_memory_search` or `ogm_recall_code_memory` with the diagnostic query, exact signature when known, repository/environment scope when known, and a limit of 3 to 5.
4. Use returned memory as a hypothesis accelerator only. Verify recommendations against current code before acting. Never copy commands blindly.

### 2. Reorient During Investigation
Do not search on every failed command. Search again only when the initial hypothesis is disproven, a new root-cause candidate or subsystem becomes central, or a failed fix reveals a different failure mode.

### 3. Persist After Work
Record memory only when all of the following are true:
- The task changed code, configuration, infrastructure, documentation, an operational decision, or produced a non-obvious investigation result.
- There is a reusable diagnosis, decision, or workflow to retain.
- At least one verifier exists: passing test, lint/typecheck/build, runtime health check, API response, or source evidence actually read.
- The task reached `success`, `partial`, `failed`, or `cancelled`.

### 4. Domain Selection
Choose the `domain` for `ogm_memory_create_episode` from the task type:
- `engineering`: code changes, tests, builds, deployments, migrations, infrastructure, MCP config, GitHub PR/merge/push work, CI, Docker, databases, and production debugging.
- `research`: technical research, vendor/tool comparison, literature review, knowledge gathering, design exploration.
- `trading`: market analysis, trading strategy, trade review, risk decisions, backtest investigation, portfolio workflow.
- `operations`: incident response, runbooks, monitoring, backup/restore, maintenance windows, remote server administration, credential rotation.
- `custom`: substantive work that does not fit other domains.

### 5. Completion Protocol
1. Search with `ogm_memory_search` before creating a record.
2. Reuse a matching active episode when one exists; otherwise call `ogm_memory_create_episode`.
3. Call `ogm_memory_append_attempt` once for the meaningful hypothesis and decisive actions.
4. Call `ogm_memory_record_outcome` or `ogm_record_code_fix` when complete.
5. Include actual verifiers: `test`, `build`, `ci`, `runtime`, `self_report`.

---

## 🛠️ Complete 21-Tool MCP Cheat Sheet & Zero-Loop Rules

### Rule 3: Zero-Loop Policy & Direct Tool Execution
* **NEVER** run `curl` commands to `/v1/...` API endpoints manually.
* **NEVER** inspect OpenAPI schemas (`openapi.json`) or run custom regex/Node.js fallback scripts.
* **ALWAYS** call the matching `ogm_*` MCP tool directly in 1 single tool call (*oneshot*).

| Category | MCP Tool Name | Primary Parameters & Aliases | Purpose |
| :--- | :--- | :--- | :--- |
| **Document Upload** | `ogm_upload_document` | `dataset_id`, `path` (or `file_path`), `filename` | Upload PDF/MD/CSV document into Knowledge Graph |
| **Evidence & Quotes** | `ogm_get_evidence` | `evidence_id` | Inspect exact quote backing graph relation |
| **Relation Evidence** | `ogm_get_relation_evidence` | `dataset_id`, `relation_id` | Retrieve relation-specific quote evidence |
| **Codebase Ingestion** | `ogm_index_codebase` | `dataset_id`, `path` (or `directory_path`) | **Oneshot** index full codebase repository into OGM |
| **Codebase Sync** | `ogm_sync_code_file` | `dataset_id`, `file_path`, `code`, `language` | Live incremental AST sync for single edited file |
| **Symbol Search** | `ogm_search_code_symbols` | `dataset_id`, `q` (or `query`), `kind`, `limit` | Search codebase functions, classes, structs |
| **Call Graph** | `ogm_get_code_call_graph` | `entity_id` (or `symbol_id`), `limit` | Trace callers, calls, inheritance tree |
| **Degree & AST Chunks** | `ogm_get_code_chunks` | `dataset_id`, `file_path`, `limit` | Fetch top-degree hub nodes & AST chunk bounds |
| **Memory Search** | `ogm_memory_search` | `q` (or `query`), `problem_signature`, `repository` | Search verified agent operational memories |
| **Memory Recall** | `ogm_recall_code_memory` | `q` (or `query` / `file_path` / `function_name`) | Recall prior bugfixes & refactoring lessons |
| **Memory Create** | `ogm_memory_create_episode` | `goal`, `problem_signature`, `domain` | Start operational problem-solving episode |
| **Memory Attempt** | `ogm_memory_append_attempt` | `episode_id`, `hypothesis`, `action` | Log episode attempt & hypothesis |
| **Memory Outcome** | `ogm_memory_record_outcome` | `episode_id`, `status`, `lesson` | Finalize episode outcome with verifiers |
| **Record Code Fix** | `ogm_record_code_fix` | `file_path`, `title`, `goal`, `root_cause`, `solution` | Record verified solution for future agent sessions |
| **List Datasets** | `ogm_list_datasets` | *(None)* | List all isolated repository datasets |
| **Search Entities** | `ogm_search_entities` | `dataset_id`, `q` (or `query`), `entity_type` | Search canonical entities in Knowledge Graph |
| **Get Entity** | `ogm_get_entity` | `entity_id` | Read entity details by ID |
| **Get Neighbors** | `ogm_get_neighbors` | `entity_id` (or `symbol_id`), `limit` | Read 1-hop graph connections |
| **Find Path** | `ogm_find_path` | `dataset_id`, `source_entity_id`, `target_entity_id` | Calculate shortest path between two entities |
| **Get Subgraph** | `ogm_get_subgraph` | `dataset_id`, `entity_id` (or `root_entity_id`), `depth` | Extract clustered entity subgraphs |
| **Get Graph** | `ogm_get_graph` | `dataset_id`, `limit`, `depth` | Read dataset graph overview |

---

## 🛠️ MCP Tool Workflows & Examples

### 1. Document Upload Workflow
```json
{
  "dataset_id": "ds_ogm_core",
  "path": "C:/docs/architecture_spec.md"
}
```
*Tool: `ogm_upload_document`*

### 2. Codebase Oneshot Indexing
```json
{
  "dataset_id": "ds_ogm_lightweight",
  "path": "C:/work/project/ogm-lightweight"
}
```
*Tool: `ogm_index_codebase`*

### 3. Degree Ranking Query
```json
{
  "dataset_id": "ds_photobox_app",
  "limit": 50
}
```
*Tool: `ogm_get_code_chunks`*

### 4. Memory Recall Before Work
```json
{
  "query": "socket.gaierror redis localhost connection error",
  "limit": 5
}
```
*Tool: `ogm_memory_search` / `ogm_recall_code_memory`*
