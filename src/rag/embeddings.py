"""
Gemini Embeddings Module

This module provides a custom embedding function for ChromaDB
using Google Gemini's text-embedding-004 model.

The embedding function is used by ChromaDB to convert text into
vector representations for semantic search.
"""

from typing import List
import google.generativeai as genai
from chromadb.api.types import EmbeddingFunction, Documents

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function for ChromaDB using Gemini.
    
    This class implements the ChromaDB EmbeddingFunction interface
    to generate embeddings using Google's Gemini API.
    
    Features:
    - Uses text-embedding-004 model
    - Batch processing support
    - Error handling and fallbacks
    """
    
    def __init__(self):
        """
        Initialize the Gemini embedding function.
        
        This configures the Gemini API with the API key from config.
        """
        # Configure Gemini API
        genai.configure(api_key=config.gemini.api_key)
        
        self.model_name = config.gemini.embedding_model
        logger.info(f"Initialized Gemini embeddings: {self.model_name}")
    
    def __call__(self, input: Documents) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        This method is called by ChromaDB to generate embeddings.
        
        Args:
            input: List of text documents to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if not input:
            return []
        
        try:
            # Generate embeddings using Gemini
            embeddings = []
            
            for text in input:
                # Generate embedding for this document
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"  # Optimized for RAG
                )
                
                embeddings.append(result['embedding'])
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            # Return zero vectors as fallback
            # Gemini text-embedding-004 produces 768-dimensional vectors
            return [[0.0] * 768 for _ in input]


async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate an embedding for a search query.
    
    This uses a different task type optimized for queries rather than documents.
    
    Args:
        query: Search query text
        
    Returns:
        List[float]: Embedding vector
    """
    try:
        result = genai.embed_content(
            model=config.gemini.embedding_model,
            content=query,
            task_type="retrieval_query"  # Optimized for search queries
        )
        
        return result['embedding']
        
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}", exc_info=True)
        return [0.0] * 768  # Fallback zero vector


if __name__ == "__main__":
    # Test embedding function
    embedding_fn = GeminiEmbeddingFunction()
    
    # Test documents
    docs = [
        "Hello, how are you?",
        "The weather is nice today",
        "I love programming in Python"
    ]
    
    # Generate embeddings
    embeddings = embedding_fn(docs)
    
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"First embedding (first 10 values): {embeddings[0][:10]}")
