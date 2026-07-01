"""
Gemini Embeddings Module

This module provides a custom embedding function for ChromaDB
using Google Gemini's text-embedding-004 model.

The embedding function is used by ChromaDB to convert text into
vector representations for semantic search.
"""

from typing import List
from chromadb.api.types import EmbeddingFunction, Documents

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function for ChromaDB supporting both Gemini and NVIDIA embeddings.
    """

    def __init__(self):
        """
        Initialize the embedding function dynamically based on config.
        """
        self.provider = config.active_llm_provider
        if self.provider == "nvidia":
            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

            self.embedder = NVIDIAEmbeddings(
                model=config.nvidia.embedding_model, api_key=config.nvidia.api_key
            )
            logger.info(
                f"Initialized NVIDIA embeddings: {config.nvidia.embedding_model}"
            )
        else:
            import google.generativeai as genai

            genai.configure(api_key=config.gemini.api_key)
            self.model_name = config.gemini.embedding_model
            logger.info(f"Initialized Gemini embeddings: {self.model_name}")

    def __call__(self, input: Documents) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        """
        if not input:
            return []

        try:
            if self.provider == "nvidia":
                return self.embedder.embed_documents(input)
            else:
                import google.generativeai as genai

                embeddings = []
                for text in input:
                    result = genai.embed_content(
                        model=self.model_name,
                        content=text,
                        task_type="retrieval_document",
                    )
                    embeddings.append(result["embedding"])
                return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            # Fallback zero vector
            dim = 1024 if self.provider == "nvidia" else 768
            return [[0.0] * dim for _ in input]


# Alias for backward compatibility
GeminiEmbeddingFunction = ChromaEmbeddingFunction


async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate an embedding for a search query.
    """
    try:
        provider = config.active_llm_provider
        if provider == "nvidia":
            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

            embedder = NVIDIAEmbeddings(
                model=config.nvidia.embedding_model, api_key=config.nvidia.api_key
            )
            return await embedder.aembed_query(query)
        else:
            import google.generativeai as genai

            result = genai.embed_content(
                model=config.gemini.embedding_model,
                content=query,
                task_type="retrieval_query",
            )
            return result["embedding"]
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}", exc_info=True)
        dim = 1024 if config.active_llm_provider == "nvidia" else 768
        return [0.0] * dim


if __name__ == "__main__":
    # Test embedding function
    embedding_fn = GeminiEmbeddingFunction()

    # Test documents
    docs = [
        "Hello, how are you?",
        "The weather is nice today",
        "I love programming in Python",
    ]

    # Generate embeddings
    embeddings = embedding_fn(docs)

    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"First embedding (first 10 values): {embeddings[0][:10]}")
