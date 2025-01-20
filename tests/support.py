from contextlib import contextmanager
from syd.interactive_viewer import InteractiveViewer
from syd.parameters import get_parameter_attributes


class MockViewer(InteractiveViewer):
    """Simple concrete implementation for testing"""

    def plot(self, **kwargs):
        return None


@contextmanager
def check_no_change(viewer: MockViewer, param_name: str):
    param = viewer.parameters[param_name]
    param_attrs = get_parameter_attributes(type(param))
    attr_values = {attr: getattr(param, attr) for attr in param_attrs}
    try:
        yield
    finally:
        changed = set()
        for attr in param_attrs:
            if getattr(viewer.parameters[param_name], attr) != attr_values[attr]:
                changed.add(attr)
        if changed:
            raise AttributeError(f"Update changed the following parameters: {changed}")
