import nest_asyncio
nest_asyncio.apply()

from typing import Literal
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.core import SimpleDirectoryReader, PropertyGraphIndex, Settings

# Import the local Ollama modules instead of OpenAI
# pyrefly: ignore [missing-import]
from llama_index.llms.ollama import Ollama
# pyrefly: ignore [missing-import]
from llama_index.embeddings.ollama import OllamaEmbedding

# 1. Set up the local LLM and Embedding Model
llm = Ollama(model="phi3:mini", request_timeout=300.0, context_window=4096)
embed_model = OllamaEmbedding(model_name="nomic-embed-text")

# Tell LlamaIndex to use these local models globally
Settings.llm = llm
Settings.embed_model = embed_model

# 2. Connect to local Neo4j Docker container
graph_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="your_secure_password",
    url="bolt://localhost:7687"
)

# 3. Define the Extraction Schema
entities = Literal["Subsystem", "Sensor", "Actuator", "PowerUnit", "TelemetryProtocol", "SecurityThreat", "MitigationStrategy", "FlightController"]
relations = Literal["POWERED_BY", "FEEDS_DATA_TO", "CONTROLS", "COMMUNICATES_VIA", "VULNERABLE_TO", "DETECTS", "MITIGATES", "TRIGGERS"]

validation_schema = {
    "Sensor": ["FEEDS_DATA_TO", "DETECTS"],
    "Actuator": ["POWERED_BY", "TRIGGERS"],
    "FlightController": ["CONTROLS", "COMMUNICATES_VIA"],
    "TelemetryProtocol": ["VULNERABLE_TO"],
    "SecurityThreat": ["TRIGGERS"],
    "MitigationStrategy": ["MITIGATES"],
    "Subsystem": ["POWERED_BY", "COMMUNICATES_VIA"],
    "PowerUnit": ["POWERED_BY"]
}

kg_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=entities,
    possible_relations=relations,
    kg_validation_schema=validation_schema,
    strict=False,       # Allow partial matches from small models
    num_workers=1       # Process one chunk at a time to avoid async issues
)

# 4. Ingest and Build the Graph
print("Reading documents...")
documents = SimpleDirectoryReader("./system_manuals").load_data()

print("Extracting entities and building graph locally (this may take a minute)...")
index = PropertyGraphIndex.from_documents(
    documents,
    kg_extractors=[kg_extractor],
    property_graph_store=graph_store,
    show_progress=True  # Show per-chunk progress
)

# Debug: show how many nodes/relations were extracted
nodes = list(index.property_graph_store.get_triplets())
print(f"\nExtracted {len(nodes)} entity-relation triplets from documents.")

# 5. Query the Engine
print("\nGraph built successfully! Querying the engine...")
query_engine = index.as_query_engine(
    include_text=True, 
    similarity_top_k=3
)

question = "Based on the manuals, what happens to the Navigation Subsystem if the PowerUnit fails?"
response = query_engine.query(question)

print("\n--- Answer ---")
print(response.response)