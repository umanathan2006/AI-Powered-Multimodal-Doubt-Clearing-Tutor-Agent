from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


EMBEDDINGS_MODEL_NAME = "all-MiniLM-L6-v2"
_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL_NAME)
    return _embeddings


def build_index(chunks: list[str], save_path: str, metadatas: list[dict] = None) -> None:
    """Build and save a FAISS index for text chunks and their metadata."""
    embeddings = get_embeddings()
    store = FAISS.from_texts(texts=chunks, embedding=embeddings, metadatas=metadatas)
    Path(save_path).mkdir(parents=True, exist_ok=True)
    store.save_local(save_path)


def load_index(save_path: str) -> FAISS:
    """Load a FAISS index from disk."""
    return FAISS.load_local(save_path, embeddings=get_embeddings(), allow_dangerous_deserialization=True)


def query_index(store: FAISS, question: str, k: int = 3) -> list[dict]:
    """Query the vector store and return results with text and metadata."""
    results = store.similarity_search(question, k=k)
    output = []
    for doc in results:
        output.append({
            "text": doc.page_content,
            "metadata": doc.metadata,
        })
    return output
