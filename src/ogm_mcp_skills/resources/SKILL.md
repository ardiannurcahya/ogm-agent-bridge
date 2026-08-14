---
name: ogm
description: >-
  OpenGraphMemory (OGM) Knowledge Graph, Codebase AST Search, and Persistent Agent Operational Memory.
  Use to recall past bug fixes, search codebase symbols/call-graphs, sync AST code files, and inspect document knowledge graphs.
---

# OpenGraphMemory (OGM) Skill

This skill provides comprehensive, unambiguous operational instructions for AI Agents interacting with OpenGraphMemory (OGM).

---

## 🎯 Codebase Ingestion Decision Tree (When User Requests Code Extraction)

When the user says:
* *"Tolong extract codebase ini ke dalam knowledge graph menggunakan ogm"*
* *"Index repo ini ke dalam OGM"*
* *"Buat knowledge graph dari project X"*

The Agent **MUST** follow this exact 5-step protocol:

```
[User: "Index/Extract Codebase X"]
         │
         ▼
 1. Check & Create Dedicated Dataset (`ds_<reponame>`) ──► NEVER mix repos into one dataset!
         │
         ▼
 2. Batch Scan & Extract AST (TS/TSX/JS/JSX/Python/Go/Rust)
    - Extract Class, Function, Interface, Method, Import, JSX Component Tags.
         │
         ▼
 3. Resolve Cross-File Symbol Calls (Global Symbol Resolution Table)
    - Link function calls and React component renders across files.
         │
         ▼
 4. Trigger & Commit Louvain Graph Analytics (Hierarchical Levels 0, 1, 2)
         │
         ▼
 5. Report Statistics to User with Direct UI Links:
    - Total Files, LOC, AST Entities, Graph Edges, Louvain Clusters.
    - URL: http://localhost:5000/graph?dataset=ds_<reponame>
```

---

## 🚨 Critical Agent Rules & Best Practices

### Rule 1: Dataset Isolation (Zero Contamination)
* **Always identify the target dataset first** using `ogm_list_datasets`.
* Each repository **MUST** have its own dedicated `dataset_id`:
  * `ds_ogm_core`: OpenGraphMemory Core Codebase (Python Backend, API, Worker).
  * `ds_ogm_mcp_skills`: OGM MCP Skills Codebase (Python MCP Server).
  * `ds_photobox_app`: Photobox App Codebase (Electron, React, TypeScript).
  * Custom Repos: Create or use `ds_<reponame>` specifically for that repository.
* **NEVER** upload or sync files from Repository A into the dataset of Repository B.

---

### Rule 2: Incremental Edit Sync vs Batch Ingestion
* **FOR FULL REPO INITIAL ONBOARDING (ONESHOT)**:
  * Call `ogm_index_codebase` with `dataset_id` and `path`. It parses the entire codebase (AST, symbols, relations, Louvain clusters) in 1 single tool call (< 5 seconds):
  ```json
  {
    "dataset_id": "ds_ogm_lightweight",
    "path": "C:/work/project/ogm-lightweight"
  }
  ```
  *Tool: `ogm_index_codebase`*

* **`ogm_sync_code_file` IS FOR INCREMENTAL SINGLE-FILE EDITS ONLY**:
  * Use `ogm_sync_code_file` ONLY when you edit/modify 1 file during pair programming.
  * **DO NOT** call `ogm_sync_code_file` in a loop across dozens or hundreds of files to onboard a new codebase.

---

## 🛠️ MCP Tool Workflows & Examples

### 1. Codebase Navigation & Call Graph
* **Oneshot Index Full Codebase Repository**:
  ```json
  {
    "dataset_id": "ds_ogm_lightweight",
    "path": "C:/work/project/ogm-lightweight"
  }
  ```
  *Tool: `ogm_index_codebase`*

* **Search Symbols**:
  ```json
  {
    "dataset_id": "ds_ogm_core",
    "query": "CodeExtractor",
    "kind": "class",
    "limit": 10
  }
  ```
  *Tool: `ogm_search_code_symbols`*

* **Trace Call Hierarchy & Call Graph**:
  ```json
  {
    "dataset_id": "ds_ogm_core",
    "symbol_id": "code_python_CodeExtractor_...",
    "direction": "both",
    "max_depth": 2
  }
  ```
  *Tool: `ogm_get_code_call_graph`*

* **Fetch AST Structural Chunks & Degree Centrality**:
  *Tool: `ogm_get_code_chunks`* (retrieves structural nodes sorted by **degree centrality**, containing `degree`, `weighted_degree`, `importance`, `community_id`, and `canonical_name`).

* **Query Degree Ranking (Most Connected Hub Symbols)**:
  When asked to rank or list nodes by degree centrality, use `ogm_get_code_chunks`:
  ```json
  {
    "dataset_id": "ds_photobox_app",
    "limit": 50
  }
  ```

---
## 🛠️ Complete 21-Tool MCP Cheat Sheet & Zero-Loop Rules

### Rule 3: Zero-Loop Policy & Direct Tool Execution
* **NEVER** run `curl` to `/v1/...` API endpoints manually.
* **NEVER** inspect OpenAPI schemas (`openapi.json`) or run custom regex/Node.js fallback scripts.
* **ALWAYS** call the matching `ogm_*` MCP tool directly in 1 single tool call (*oneshot*).

| Category | MCP Tool Name | Primary Parameters & Aliases | Purpose |
| :--- | :--- | :--- | :--- |
| **Codebase Ingestion** | `ogm_index_codebase` | `dataset_id`, `path` (or `directory_path`) | **Oneshot** index full codebase repository into OGM |
| **Codebase Sync** | `ogm_sync_code_file` | `dataset_id`, `file_path`, `code`, `language` | Live incremental AST sync for single edited file |
| **Symbol Search** | `ogm_search_code_symbols` | `dataset_id`, `q` (or `query`), `kind`, `limit` | Search codebase functions, classes, structs |
| **Call Graph** | `ogm_get_code_call_graph` | `entity_id` (or `symbol_id`), `limit` | Trace callers, calls, inheritance tree |
| **Degree & AST Chunks** | `ogm_get_code_chunks` | `dataset_id`, `file_path`, `limit` | Fetch top-degree hub nodes & AST chunk bounds |
| **Memory Recall** | `ogm_recall_code_memory` | `q` (or `query` / `file_path` / `function_name`) | Recall prior bugfixes & refactoring lessons |
| **Memory Record** | `ogm_record_code_fix` | `file_path`, `title`, `goal`, `root_cause`, `solution` | Record verified solution for future agent sessions |
| **Document Upload** | `ogm_upload_document` | `dataset_id`, `path` (or `file_path`), `filename` | Upload PDF/MD/CSV document into Knowledge Graph |
| **List Datasets** | `ogm_list_datasets` | *(None)* | List all isolated repository datasets |
| **Search Entities** | `ogm_search_entities` | `dataset_id`, `q` (or `query`), `entity_type` | Search canonical entities in Knowledge Graph |
| **Get Entity** | `ogm_get_entity` | `entity_id` | Read entity details by ID |
| **Get Neighbors** | `ogm_get_neighbors` | `entity_id` (or `symbol_id`), `limit` | Read 1-hop graph connections |
| **Find Path** | `ogm_find_path` | `dataset_id`, `source_entity_id`, `target_entity_id` | Calculate shortest path between two entities |
| **Get Subgraph** | `ogm_get_subgraph` | `dataset_id`, `entity_id` (or `root_entity_id`), `depth` | Extract clustered entity subgraphs |
| **Get Graph** | `ogm_get_graph` | `dataset_id`, `limit`, `depth` | Read dataset graph overview |
| **Evidence & Quotes** | `ogm_get_evidence` | `evidence_id` | Inspect exact quote backing graph relation |
| **Relation Evidence** | `ogm_get_relation_evidence` | `dataset_id`, `relation_id` | Retrieve relation-specific quote evidence |
| **Agent Memory Search** | `ogm_memory_search` | `q`, `problem_signature`, `repository` | Search verified agent operational memories |
| **Create Episode** | `ogm_memory_create_episode` | `goal`, `problem_signature`, `repository` | Start operational problem-solving episode |
| **Append Attempt** | `ogm_memory_append_attempt` | `episode_id`, `hypothesis`, `action` | Log episode attempt & hypothesis |
| **Record Outcome** | `ogm_memory_record_outcome` | `episode_id`, `status`, `lesson` | Finalize episode outcome with verifiers |

### 2. Operational Agent Memory (Bug Fixes & Lessons)
* **Recall Prior Fixes Before Solving a Bug**:
  * Always run `ogm_recall_code_memory` before attempting complex refactors or debugging tricky errors:
  ```json
  {
    "query": "socket.gaierror redis localhost connection error",
    "limit": 5
  }
  ```
* **Record Solution Pattern After Successful Fix**:
  * When a bug is fixed and verified, record it so future agent sessions remember the solution:
  ```json
  {
    "task_description": "Fix Redis host connection on Windows native host",
    "problem_signature": "socket.gaierror Errno 11001 resolving redis hostname",
    "root_cause": "Docker service name 'redis' was used instead of 127.0.0.1 on Windows host",
    "code_diff": "- REDIS_HOST=redis\n+ REDIS_HOST=127.0.0.1",
    "outcome": "useful",
    "dataset_id": "ds_ogm_core"
  }
  ```
  *Tool: `ogm_record_code_fix`*

---

### 3. Knowledge Graph Entities & Evidence
* `ogm_search_entities`: Search canonical entities across datasets.
* `ogm_get_neighbors`: Retrieve immediate 1-hop semantic connections.
* `ogm_find_path`: Find shortest relational paths between two symbols or entities.
* `ogm_get_subgraph`: Extract clustered entity subgraphs for GraphRAG context injection.
