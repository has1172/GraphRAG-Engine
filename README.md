# 🧠 GraphRAG Engine — Local Knowledge Graph + RAG Pipeline

> **A fully local, privacy-preserving Retrieval-Augmented Generation (RAG) system powered by LlamaIndex, Ollama, Neo4j, and `nomic-embed-text`. No cloud APIs. No data leaves your machine.**

---

## 📖 Table of Contents

1. [What is GraphRAG?](#what-is-graphrag)
2. [System Architecture](#system-architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Setup & Installation](#setup--installation)
   - [1. Start Neo4j via Docker](#1-start-neo4j-via-docker)
   - [2. Pull Ollama Models](#2-pull-ollama-models)
   - [3. Set Up Python Environment](#3-set-up-python-environment)
   - [4. Install Dependencies](#4-install-dependencies)
7. [Configuration](#configuration)
   - [LLM and Embedding Model](#llm-and-embedding-model)
   - [Extraction Schema](#extraction-schema)
8. [Running the Pipeline](#running-the-pipeline)
9. [Visualizing the Graph in Neo4j](#visualizing-the-graph-in-neo4j)
   - [Neo4j Browser Screenshots](#neo4j-browser-screenshots)
   - [Useful Cypher Queries](#useful-cypher-queries)
10. [Example Document & Output](#example-document--output)
11. [Available Ollama Models](#available-ollama-models)
12. [Troubleshooting & Errors Fixed](#troubleshooting--errors-fixed)
13. [Extending the Project](#extending-the-project)
14. [Contributing](#contributing)

---

## What is GraphRAG?

Traditional RAG retrieves **chunks of text** that are semantically similar to a query. This works well for simple lookups but fails when the answer requires **connecting multiple facts** across a document — e.g., "If Component A fails, what happens to Subsystem B?"

**GraphRAG** solves this by:

1. Parsing documents with an LLM to extract **entities** (nodes) and **relationships** (edges).
2. Storing the resulting **knowledge graph** in a graph database (Neo4j).
3. At query time, traversing the graph to find **chains of reasoning** across entities, then passing the relevant subgraph + raw text to the LLM to formulate an answer.

This makes it especially powerful for **technical documentation**, **engineering manuals**, **security reports**, and any domain where relationships between concepts matter.

```
Document
   │
   ▼
LLM Entity Extractor (phi3:mini via Ollama)
   │
   ├──► Nodes:  APM-NX Core, Gyroscope, MAVLink v2, GPS Spoofing Attack...
   └──► Edges:  CONTROLS, FEEDS_DATA_TO, VULNERABLE_TO, MITIGATES...
                              │
                              ▼
                         Neo4j Graph DB
                              │
                              ▼
               Query → Graph Traversal + Text Retrieval
                              │
                              ▼
                    LLM synthesizes final answer
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GraphRAG Engine                              │
│                                                                     │
│  ┌──────────────┐   ┌────────────────────┐   ┌──────────────────┐   │
│  │ system_manuals│──▶│  LlamaIndex Core   │──▶│  Neo4j (Docker)│   │
│  │  (.txt files) │   │  PropertyGraphIndex│   │  bolt://7687    │   │
│  └──────────────┘   └────────────────────┘   └──────────────────┘   │
│                              │                        ▲             │
│                              ▼                        │             │
│                    ┌─────────────────┐                │             │
│                    │  Ollama (local) │────────────────┘             │
│                    │  ┌───────────┐  │  SchemaLLMPathExtractor      │
│                    │  │ phi3:mini │  │  (Entity + Relation Extraction│
│                    │  └───────────┘  │                              │
│                    │  ┌────────────┐ │                              │
│                    │  │nomic-embed │ │  OllamaEmbedding             │
│                    │  └────────────┘ │  (Vector Embeddings)         │
│                    └─────────────────┘                              │
│                              │                                      │
│                     Query Engine                                    │
│            (LLM Synonym Retriever + Vector Retriever)               │
│                              │                                      │
│                              ▼                                      │
│                    ┌──────────────────┐                             │
│                    │   Final Answer   │                             │
│                    └──────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component            | Technology                                  | Purpose                                       |
| -------------------- | ------------------------------------------- | --------------------------------------------- |
| **Graph Database**   | [Neo4j](https://neo4j.com/) (Docker)        | Stores extracted knowledge graph              |
| **RAG Framework**    | [LlamaIndex](https://www.llamaindex.ai/)    | Orchestrates ingestion, extraction & querying |
| **Local LLM**        | [Ollama](https://ollama.com/) + `phi3:mini` | Entity extraction & answer generation         |
| **Embeddings**       | Ollama + `nomic-embed-text`                 | Semantic vector search                        |
| **Language**         | Python 3.11+                                | Core runtime                                  |
| **Containerization** | Docker Compose                              | Neo4j lifecycle management                    |

---

## Project Structure

```
GraphRAG Engine/
│
├── graph_rag.py                  # 🚀 Main pipeline script
├── docker-compose.yml            # 🐳 Neo4j container configuration
├── .env.txt                      # 🔑 Environment variables (credentials)
├── README.md                     # 📖 This file
│
├── system_manuals/               # 📄 Your source documents go here
│   └── tactical_aircraft_architecture.txt
│       └── uav_specs.txt         # Add more .txt files to enrich the graph
│
├── neo4j/                        # 🗄️ Neo4j persistent storage (auto-created by Docker)
│   ├── data/                     # Database files
│   ├── logs/                     # Database logs
│   ├── import/                   # CSV import directory
│   └── plugins/                  # APOC and other plugin JARs
│
└── .venv/                        # 🐍 Python virtual environment
```

---

## Prerequisites

Make sure the following are installed on your machine **before** proceeding:

| Tool               | Version                  | Download                                                      |
| ------------------ | ------------------------ | ------------------------------------------------------------- |
| **Python**         | 3.11 or 3.12 recommended | [python.org](https://www.python.org/downloads/)               |
| **Docker Desktop** | Latest                   | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Ollama**         | Latest                   | [ollama.com](https://ollama.com/)                             |
| **Git**            | Any                      | [git-scm.com](https://git-scm.com/)                           |

> ⚠️ **Python 3.13 users:** A known asyncio regression requires adding `nest_asyncio.apply()` — this is already handled in `graph_rag.py`.

---

## Setup & Installation

### 1. Start Neo4j via Docker

From the project root, start the Neo4j container:

```bash
docker compose up -d
```

This will:

- Pull the latest `neo4j` image (first run only)
- Expose the browser at **http://localhost:7474**
- Expose the Bolt protocol at **bolt://localhost:7687**
- Enable the APOC plugin automatically
- Persist all data under `./neo4j/data/`

Verify the container is running:

```bash
docker ps
```

You should see `neo4j_db` in the list with status `Up`.

---

### 2. Pull Ollama Models

You need two models: one for language understanding (entity extraction + QA) and one for embeddings.

```bash
# Language model — used for entity extraction and answering questions
ollama pull phi3:mini

# Embedding model — used for semantic vector search
ollama pull nomic-embed-text
```

**Optional alternative models (already downloaded):**

```bash
ollama pull gemma:2b       # 1.7 GB — lighter alternative to phi3:mini
ollama pull tinyllama      # 637 MB — fastest, lowest quality
ollama pull qwen3.5:4b     # 3.4 GB — best quality, needs context_window=4096
```

Verify all models are available:

```bash
ollama list
```

---

### 3. Set Up Python Environment

```bash
# Create a virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Activate it (macOS/Linux)
source .venv/bin/activate
```

---

### 4. Install Dependencies

```bash
pip install llama-index
pip install llama-index-llms-ollama
pip install llama-index-embeddings-ollama
pip install llama-index-graph-stores-neo4j
pip install nest-asyncio
```

Or install all at once:

```bash
pip install llama-index llama-index-llms-ollama llama-index-embeddings-ollama llama-index-graph-stores-neo4j nest-asyncio
```

---

## Configuration

### LLM and Embedding Model

In `graph_rag.py`, the LLM and embedding model are configured at the top:

```python
# Language model for extraction and QA
llm = Ollama(
    model="phi3:mini",
    request_timeout=300.0,   # Allow up to 5 min for slow responses
    context_window=4096      # CRITICAL: Prevents Ollama from pre-allocating >40 GB RAM
)

# Embedding model for vector similarity search
embed_model = OllamaEmbedding(model_name="nomic-embed-text")
```

> ⚠️ **`context_window=4096` is critical.** Without it, Ollama defaults to a 128K context window and tries to pre-allocate ~48 GB of KV cache RAM — causing an out-of-memory error even on machines with 32+ GB RAM.

To switch models, change the `model=` parameter. For `qwen3.5:4b`, keep `context_window=4096`.

---

### Extraction Schema

The schema tells the extractor **what types of entities and relationships to look for** in your documents. Modify this section in `graph_rag.py` to match your domain:

```python
# Entity types (nodes in the graph)
entities = Literal[
    "Subsystem",
    "Sensor",
    "Actuator",
    "PowerUnit",
    "TelemetryProtocol",
    "SecurityThreat",
    "MitigationStrategy",
    "FlightController"
]

# Relationship types (edges in the graph)
relations = Literal[
    "POWERED_BY",
    "FEEDS_DATA_TO",
    "CONTROLS",
    "COMMUNICATES_VIA",
    "VULNERABLE_TO",
    "DETECTS",
    "MITIGATES",
    "TRIGGERS"
]

# Validation schema: which entity types can have which relations
validation_schema = {
    "Sensor":            ["FEEDS_DATA_TO", "DETECTS"],
    "Actuator":          ["POWERED_BY", "TRIGGERS"],
    "FlightController":  ["CONTROLS", "COMMUNICATES_VIA"],
    "TelemetryProtocol": ["VULNERABLE_TO"],
    "SecurityThreat":    ["TRIGGERS"],
    "MitigationStrategy":["MITIGATES"],
    "Subsystem":         ["POWERED_BY", "COMMUNICATES_VIA"],
    "PowerUnit":         ["POWERED_BY"],
}
```

The extractor is configured with `strict=False` — meaning it accepts approximate matches from smaller models that may not follow the schema format perfectly. If you use a larger model (e.g., `qwen3.5:4b`), you can experiment with `strict=True` for higher precision.

---

## Running the Pipeline

Make sure:

- Docker container (`neo4j_db`) is running
- Ollama is running in the background
- Your virtual environment is activated

Then run:

```bash
.venv\Scripts\python.exe graph_rag.py
```

**Expected output:**

```
Reading documents...
Extracting entities and building graph locally (this may take a minute)...
Applying transformations: 100%|██████████| 1/1 [00:05<00:00,  5.58s/it]
Generating embeddings:    100%|██████████| 1/1 [00:02<00:00,  2.32s/it]

Extracted 18 entity-relation triplets from documents.

Graph built successfully! Querying the engine...

--- Answer ---
The Dynamic Frequency Hopping Algorithm detects RF Signal Jamming and mitigates
it by rapidly shifting communication bands across the spectrum...
```

> ℹ️ The first run will always rebuild the graph from scratch. Subsequent runs will re-ingest into the same Neo4j database (triplets accumulate). To start fresh, run `MATCH (n) DETACH DELETE n` in Neo4j Browser before re-running.

---

## Visualizing the Graph in Neo4j

Open your browser and navigate to: **http://localhost:7474**

Login with:

- **Username:** `neo4j`
- **Password:** `your_secure_password`

### Neo4j Browser Screenshots

> 📸 **Add your screenshots below** after running the pipeline. Replace the placeholder text with actual image embeds using the format:
> `![Caption](./screenshots/your_image.png)`
>
> **Tip:** Create a `screenshots/` folder in the project root to store your captures.

---

#### Full Graph View — All Nodes and Relationships

```cypher
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
```

> 📸 **[ INSERT SCREENSHOT HERE ]**
>
> _Suggested filename: `screenshots/full_graph_overview.png`_
>
> _What to capture: The full interactive graph canvas showing all entity nodes (color-coded by type) connected by labeled relationship edges._

---

#### FlightController Subgraph — What the APM-NX Core Controls

```cypher
MATCH (fc:FlightController)-[r]->(m) RETURN fc, r, m
```

> 📸 **[ INSERT SCREENSHOT HERE ]**
>
> _Suggested filename: `screenshots/flightcontroller_subgraph.png`_
>
> _What to capture: The APM-NX Core node with outgoing CONTROLS and COMMUNICATES_VIA edges._

---

#### Security Threat Graph — Vulnerabilities and Mitigations

```cypher
MATCH (n)-[r:VULNERABLE_TO|DETECTS|MITIGATES]->(m) RETURN n, r, m
```

> 📸 **[ INSERT SCREENSHOT HERE ]**
>
> _Suggested filename: `screenshots/security_threat_graph.png`_
>
> _What to capture: TelemetryProtocol nodes linked to SecurityThreats via VULNERABLE_TO, and MitigationStrategy nodes linked via DETECTS/MITIGATES._

---

#### Power Dependency Graph — What is POWERED_BY What

```cypher
MATCH (n)-[r:POWERED_BY]->(m) RETURN n, r, m
```

> 📸 **[ INSERT SCREENSHOT HERE ]**
>
> _Suggested filename: `screenshots/power_dependency_graph.png`_
>
> _What to capture: All components linked to their respective PowerUnit battery nodes._

---

#### Node Detail View — Clicking a Specific Node

> 📸 **[ INSERT SCREENSHOT HERE ]**
>
> _Suggested filename: `screenshots/node_detail_panel.png`_
>
> _What to capture: The right-side properties panel in Neo4j Browser after clicking on a specific node (e.g., "APM-NX Core"), showing its `id`, `label`, `name`, and any other stored properties._

---

### Useful Cypher Queries

Copy and paste these into the Neo4j Browser query bar and press **▶ Run**:

| Purpose                           | Cypher                                                                                         |
| --------------------------------- | ---------------------------------------------------------------------------------------------- |
| View entire graph                 | `MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100`                                                  |
| Count all nodes                   | `MATCH (n) RETURN count(n)`                                                                    |
| Count all relationships           | `MATCH ()-[r]->() RETURN type(r), count(*) ORDER BY count(*) DESC`                             |
| Find a specific entity            | `MATCH (n) WHERE n.name CONTAINS 'APM-NX' RETURN n`                                            |
| All neighbors of a node           | `MATCH (n {name: 'APM-NX Core'})-[r]-(m) RETURN n, r, m`                                       |
| Shortest path between two nodes   | `MATCH p=shortestPath((a {name:'GPS Spoofing Attack'})-[*]-(b {name:'APM-NX Core'})) RETURN p` |
| Export all triplets as table      | `MATCH (n)-[r]->(m) RETURN n.name, type(r), m.name`                                            |
| **Delete all data (fresh start)** | `MATCH (n) DETACH DELETE n`                                                                    |

---

## Example Document & Output

**Input document** (`system_manuals/tactical_aircraft_architecture.txt`):

```
DOCUMENT ID: TA-884-AEROSPACE
SUBJECT: Advanced System Architecture and Telemetry Security Protocols
         for Morphing Tactical Aircraft (Project PARTH)

1. HARDWARE ARCHITECTURE AND CORE SYSTEMS
The aircraft's primary FlightController is the APM-NX Core...
The APM-NX Core directly CONTROLS the Servo-Actuated Folding Arms (Actuator)...
These morphing Actuators are explicitly POWERED_BY the Secondary Li-Ion Payload Battery (PowerUnit).

3. TELEMETRY, COMMUNICATIONS, AND VULNERABILITIES
The FlightController COMMUNICATES_VIA the standard MAVLink v2 Protocol (TelemetryProtocol)...
The MAVLink v2 Protocol is VULNERABLE_TO a GPS Spoofing Attack (SecurityThreat).
The AES-256 Encrypted Datalink is VULNERABLE_TO RF Signal Jamming (SecurityThreat).

4. CYBER-PHYSICAL SECURITY AND AI MITIGATION
The Physics-Informed Neural Network Filter (MitigationStrategy) DETECTS the GPS Spoofing Attack.
The Physics-Informed Neural Network Filter MITIGATES the GPS Spoofing Attack...
```

**Extracted Knowledge Graph (as triplets):**

| Subject                                | Relationship     | Object                           |
| -------------------------------------- | ---------------- | -------------------------------- |
| APM-NX Core                            | CONTROLS         | Servo-Actuated Folding Arms      |
| Servo-Actuated Folding Arms            | POWERED_BY       | Secondary Li-Ion Payload Battery |
| High-Fidelity Gyroscope                | FEEDS_DATA_TO    | APM-NX Core                      |
| Pitot Static Tube                      | FEEDS_DATA_TO    | APM-NX Core                      |
| LiDAR Terrain Mapper                   | FEEDS_DATA_TO    | APM-NX Core                      |
| APM-NX Core                            | COMMUNICATES_VIA | MAVLink v2 Protocol              |
| APM-NX Core                            | COMMUNICATES_VIA | AES-256 Encrypted Datalink       |
| MAVLink v2 Protocol                    | VULNERABLE_TO    | GPS Spoofing Attack              |
| AES-256 Encrypted Datalink             | VULNERABLE_TO    | RF Signal Jamming                |
| Physics-Informed Neural Network Filter | DETECTS          | GPS Spoofing Attack              |
| Physics-Informed Neural Network Filter | MITIGATES        | GPS Spoofing Attack              |
| Dynamic Frequency Hopping Algorithm    | DETECTS          | RF Signal Jamming                |
| Dynamic Frequency Hopping Algorithm    | MITIGATES        | RF Signal Jamming                |
| Auto-Rotational Descent Subsystem      | POWERED_BY       | Primary Solid-State Battery      |
| Active Thermal Management Subsystem    | POWERED_BY       | Primary Solid-State Battery      |
| Auto-Rotational Descent Subsystem      | TRIGGERS         | Ballistic Recovery Parachute     |

**Sample Query and Answer:**

```
Question: "What happens if the telemetry is jammed?"

Answer:
The Dynamic Frequency Hopping Algorithm detects any targeted RF Signal Jamming.
Upon detection, it mitigates the jamming by rapidly shifting communication bands
across the spectrum, maintaining the link between the FlightController and the
Ground Control Station despite electronic warfare interference.
```

---

## Available Ollama Models

The following models are downloaded and ready to use on this machine:

| Model              | Size   | Recommended For                                          |
| ------------------ | ------ | -------------------------------------------------------- |
| `nomic-embed-text` | 274 MB | ✅ Embeddings (keep this always)                         |
| `tinyllama`        | 637 MB | Speed tests, minimal RAM usage                           |
| `gemma:2b`         | 1.7 GB | Lighter LLM alternative                                  |
| `phi3:mini`        | 2.2 GB | **✅ Default — best balance of speed & quality**         |
| `qwen3.5:4b`       | 3.4 GB | Best extraction quality (use with `context_window=4096`) |

To switch models, update line 16 of `graph_rag.py`:

```python
# Change this to any model from the table above
llm = Ollama(model="phi3:mini", request_timeout=300.0, context_window=4096)
```

---

## Troubleshooting & Errors Fixed

Below is a log of every error encountered during development and the exact fix applied:

### ❌ Error 1 — `model 'qwen' not found (404)`

**Cause:** Incorrect model name. Ollama requires the full tag including version.  
**Fix:** Use the exact name: `model="qwen3.5:4b"` or `model="phi3:mini"`.

---

### ❌ Error 2 — `ModuleNotFoundError: No module named 'llama_index.llms.ollama'`

**Cause:** The Ollama integration is a separate package not bundled with base `llama-index`.  
**Fix:**

```bash
pip install llama-index-llms-ollama llama-index-embeddings-ollama
```

---

### ❌ Error 3 — `model requires 48.4 GiB than is available (4.6 GiB)`

**Cause:** Ollama defaults to a **128K token context window** and pre-allocates the full KV cache upfront. Even a 2.2 GB model can demand 48 GB of RAM with this setting.  
**Fix:** Add `context_window=4096` to the `Ollama()` constructor.

```python
llm = Ollama(model="phi3:mini", request_timeout=300.0, context_window=4096)
```

---

### ❌ Error 4 — `RuntimeError: Detected nested async. Please use nest_asyncio.apply()`

**Cause:** Python 3.13 disallows calling `asyncio.run()` inside an already-running event loop. LlamaIndex does this internally during graph building and querying.  
**Fix:** Add at the very top of `graph_rag.py`:

```python
import nest_asyncio
nest_asyncio.apply()
```

---

### ❌ Error 5 — Script runs but returns `Empty Response`

**Cause:** `strict=True` discards any entity or relation that doesn't **exactly** match the schema string. Small models like `phi3:mini` rarely produce perfect format compliance, so all extracted data gets thrown away, leaving an empty graph.  
**Fix:**

```python
kg_extractor = SchemaLLMPathExtractor(
    ...
    strict=False,    # Accept approximate matches from small models
    num_workers=1    # Sequential processing avoids async overload on local Ollama
)
```

---

## Extending the Project

### Add More Documents

Drop any `.txt` file into `system_manuals/` and re-run `graph_rag.py`. The new entities and relationships will be merged into the existing graph in Neo4j.

### Expand the Schema

Add new entity types and relation types in `graph_rag.py` lines 31–43 to capture different domains (e.g., add `"Person"`, `"Organization"`, `"Event"` for news documents).

### Add a Query Loop (Interactive Mode)

Replace the hardcoded `question` at the bottom of `graph_rag.py` with:

```python
while True:
    question = input("\nAsk a question (or 'quit' to exit): ")
    if question.lower() == "quit":
        break
    response = query_engine.query(question)
    print("\n--- Answer ---")
    print(response.response)
```

### Export the Graph

To export all triplets to CSV from Neo4j Browser:

```cypher
MATCH (n)-[r]->(m)
RETURN n.name AS subject, type(r) AS relation, m.name AS object
```

Then click **Export CSV** in the Neo4j Browser result panel.

### Use a Better Model

For higher extraction quality at the cost of more RAM:

```python
llm = Ollama(model="qwen3.5:4b", request_timeout=300.0, context_window=4096)
```

---

## Contributing

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add your documents to `system_manuals/` or extend the schema
4. Commit your changes: `git commit -m "Add: new schema for cybersecurity domain"`
5. Push and open a Pull Request

---

## License

MIT License — free to use, modify, and distribute with attribution.

---

_Built with ❤️ using [LlamaIndex](https://www.llamaindex.ai/), [Ollama](https://ollama.com/), and [Neo4j](https://neo4j.com/)._
