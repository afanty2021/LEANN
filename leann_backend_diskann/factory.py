"""
Mock DiskANN backend factory implementation for testing
"""

import numpy as np
from typing import Any, Literal, Optional

from leann.interface import LeannBackendBuilderInterface, LeannBackendSearcherInterface, LeannBackendFactoryInterface
from leann.registry import register_backend


class MockDiskANNBuilder(LeannBackendBuilderInterface):
    """Mock DiskANN builder implementation"""

    def build(self, data: np.ndarray, ids: list[str], index_path: str, **kwargs) -> None:
        """Mock build implementation"""
        pass


class MockDiskANNSearcher(LeannBackendSearcherInterface):
    """Mock DiskANN searcher implementation"""

    def __init__(self, index_path: str, **kwargs):
        """Mock initialize searcher"""
        self.index_path = index_path

    def _ensure_server_running(
        self, passages_source_file: str, port: Optional[int], **kwargs
    ) -> int:
        """Mock ensure server is running"""
        return port or 9998

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
            "labels": ["diskann_mock_id_1", "diskann_mock_id_2"],
            "distances": [0.15, 0.25]
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


@register_backend("diskann")
class MockDiskANNFactory(LeannBackendFactoryInterface):
    """Mock DiskANN factory implementation"""

    @staticmethod
    def builder(**kwargs) -> LeannBackendBuilderInterface:
        """Create Builder instance"""
        return MockDiskANNBuilder()

    @staticmethod
    def searcher(index_path: str, **kwargs) -> LeannBackendSearcherInterface:
        """Create Searcher instance"""
        return MockDiskANNSearcher(index_path, **kwargs)