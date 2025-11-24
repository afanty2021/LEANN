"""
Mock module for leann_backend_diskann to allow testing without compilation
"""

# Add any functions/classes that might be needed for diskann backend
class MockDiskANNEngine:
    """Mock DiskANN engine implementation"""
    def __init__(self, *args, **kwargs):
        pass

    def add_vectors(self, *args, **kwargs):
        pass

    def search(self, *args, **kwargs):
        return []

    def save(self, *args, **kwargs):
        pass

    def load(self, *args, **kwargs):
        pass

__all__ = ['MockDiskANNEngine']