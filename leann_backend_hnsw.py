"""
Mock module for leann_backend_hnsw to allow testing without compilation
"""

def prune_hnsw_embeddings_inplace(*args, **kwargs):
    """Mock implementation of prune_hnsw_embeddings_inplace"""
    pass

# Add any other functions/classes that might be needed
__all__ = ['prune_hnsw_embeddings_inplace']