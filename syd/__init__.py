from typing import Callable, Optional
from .viewer import Viewer

__version__ = "1.0.1"


def make_viewer(plot_func: Optional[Callable] = None):
    viewer = Viewer()
    if plot_func is not None:
        viewer.set_plot(plot_func)
    return viewer
