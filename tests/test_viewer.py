import pytest
from syd.parameters import ParameterType, TextParameter
from syd.viewer import Viewer, validate_parameter_operation

with pytest.raises(ValueError):

    class TestViewer(Viewer):
        def __init__(self):
            pass

        @validate_parameter_operation("not_add_or_update", ParameterType.text)
        def add_alternate_parameter(self, name, value):
            self.parameters[name] = TextParameter(name, value)


with pytest.raises(ValueError):

    class TestViewer(Viewer):
        def __init__(self):
            pass

        @validate_parameter_operation("add", ParameterType.text)
        def update_alternate_parameter(self, name, value):
            self.parameters[name] = TextParameter(name, value)


with pytest.raises(ValueError):

    class TestViewer(Viewer):
        def __init__(self):
            pass

        @validate_parameter_operation("update", ParameterType.text)
        def add_alternate_parameter(self, name, value):
            self.parameters[name] = TextParameter(name, value)
