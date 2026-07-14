"""
Central place for settings that the rest of the app will need later:
paths to your FAISS index, Ollama model name, chunk size for RAG, etc.

Empty for now — this file exists so that when step 2 (RAG ingestion)
and later steps need shared settings, there's already an obvious,
single place to put them instead of scattering constants everywhere.
"""

OLLAMA_MODEL = "qwen2.5:7b-instruct"  # placeholder, update when you pick your model
FAISS_INDEX_PATH = "data/faiss_index"
