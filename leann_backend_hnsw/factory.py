"""
Mock HNSW backend factory implementation for testing
"""

import numpy as np
from typing import Any, Literal, Optional

from leann.interface import LeannBackendBuilderInterface, LeannBackendSearcherInterface, LeannBackendFactoryInterface
from leann.registry import register_backend


class MockHNSWBuilder(LeannBackendBuilderInterface):
    """Mock HNSW builder implementation"""

    def build(self, data: np.ndarray, ids: list[str], index_path: str, **kwargs) -> None:
        """Mock build implementation"""
        pass


class MockHNSWSearcher(LeannBackendSearcherInterface):
    """Mock HNSW searcher implementation"""

    def __init__(self, index_path: str, **kwargs):
        """Mock initialize searcher"""
        self.index_path = index_path

    def _ensure_server_running(
        self, passages_source_file: str, port: Optional[int], **kwargs
    ) -> int:
        """Mock ensure server is running"""
        return port or 9999

    def search(
        self,
        query: np.ndarray,
        top_k: int,
        complexity: int = 64,
        beam_width: int = 1,
        prune_ratio: float = 0.0,
        recompute_embeddings: bool = False,
        pruning_strategy: Literal["global", "local", "proportional"] = "global",
        zmq_port: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Mock search implementation"""
        return {
            "labels": ["mock_id_1", "mock_id_2"],
            "distances": [0.1, 0.2]
        }

    def compute_query_embedding(
        self,
        query: str,
        use_server_if_available: bool = True,
        zmq_port: Optional[int] = None,
        query_template: Optional[str] = None,
    ) -> np.ndarray:
        """Mock compute embedding"""
        return np.random.rand(1, 768).astype(np.float32)


@register_backend("hnsw")
class MockHNSWFactory(LeannBackendFactoryInterface):
    """Mock HNSW factory implementation"""

    @staticmethod
    def builder(**kwargs) -> LeannBackendBuilderInterface:
        """Create Builder instance"""
        return MockHNSWBuilder()

    @staticmethod
    def searcher(index_path: str, **kwargs) -> LeannBackendSearcherInterface:
        """Create Searcher instance"""
        return MockHNSWSearcher(index_path, **kwargs)