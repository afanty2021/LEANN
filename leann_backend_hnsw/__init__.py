"""
Mock package for leann_backend_hnsw to allow testing without compilation
"""

from .convert_to_csr import prune_hnsw_embeddings_inplace
from .factory import MockHNSWFactory

# Trigger auto-discovery by importing the factory module
__all__ = ['prune_hnsw_embeddings_inplace', 'MockHNSWFactory']