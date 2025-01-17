from syd.interactive_viewer import InteractiveViewer


class MockViewer(InteractiveViewer):
    """Simple concrete implementation for testing"""

    def plot(self, **kwargs):
        return None
