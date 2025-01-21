from typing import Callable
from .interactive_viewer import InteractiveViewer

__version__ = "0.1.5"


class DefaultViewer(InteractiveViewer):
    def plot(self, state):
        pass


def make_viewer(plot_func: Callable):
    viewer = DefaultViewer()
    viewer.plot = plot_func
    return viewer
