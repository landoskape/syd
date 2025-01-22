from typing import Callable, Optional
from .interactive_viewer import InteractiveViewer

__version__ = "0.1.6"


def make_viewer(plot_func: Optional[Callable] = None):
    viewer = InteractiveViewer()
    if plot_func is not None:
        viewer.set_plot(plot_func)
    return viewer
