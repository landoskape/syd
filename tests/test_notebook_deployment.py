# import pytest
# from unittest.mock import Mock, patch
# import ipywidgets as widgets
# from matplotlib.figure import Figure
# from syd.viewer import Viewer
# from syd.notebook_deployment.widgets import (
#     create_widget,
#     TextWidget,
#     SelectionWidget,
#     BooleanWidget,
# )
# from syd.notebook_deployment.deployer import NotebookDeployer, LayoutConfig


# @pytest.fixture
# def basic_parameters():
#     class TestViewer(Viewer):
#         def plot(self, state) -> Figure:
#             # Return a mock figure
#             return Mock(spec=Figure)

#     mock_viewer = TestViewer()
#     # Add test parameters using keyword arguments
#     mock_viewer.add_text("text_param", value="test")
#     mock_viewer.add_boolean("bool_param", value=True)
#     mock_viewer.add_selection("select_param", value="A", options=["A", "B", "C"])
#     mock_viewer.add_integer("int_param", value=5, min=0, max=10)
#     return mock_viewer


# # Widget Creation Tests
# class TestWidgetCreation:
#     def test_text_widget_creation(self, basic_parameters):
#         param = basic_parameters.parameters["text_param"]
#         widget = create_widget(param)

#         assert isinstance(widget, TextWidget)
#         assert isinstance(widget.widget, widgets.Text)
#         assert widget.value == "test"
#         assert widget.widget.description == "text_param"

#     def test_selection_widget_creation(self, basic_parameters):
#         param = basic_parameters.parameters["select_param"]
#         widget = create_widget(param)

#         assert isinstance(widget, SelectionWidget)
#         assert isinstance(widget.widget, widgets.Dropdown)
#         assert widget.value == "A"
#         assert list(widget.widget.options) == ["A", "B", "C"]

#     def test_boolean_widget_creation(self, basic_parameters):
#         param = basic_parameters.parameters["bool_param"]
#         widget = create_widget(param)

#         assert isinstance(widget, BooleanWidget)
#         assert isinstance(widget.widget, widgets.Checkbox)
#         assert widget.value is True

#     def test_widget_creation_validation(self, basic_parameters):
#         # Test creation with invalid parameter
#         with pytest.raises(ValueError):
#             create_widget(Mock())


# # Widget Update Tests
# class TestWidgetUpdates:
#     def test_widget_value_update(self, basic_parameters):
#         param = basic_parameters.parameters["text_param"]
#         widget = create_widget(param)

#         widget.value = "new value"
#         assert widget.value == "new value"

#         # Test update from parameter
#         param.value = "param update"
#         widget.update_from_parameter(param)
#         assert widget.value == "param update"

#     def test_selection_widget_options_update(self, basic_parameters):
#         param = basic_parameters.parameters["select_param"]
#         widget = create_widget(param)

#         # Update options through parameter
#         new_options = ["X", "Y", "Z"]
#         param.update({"options": new_options, "value": "X"})
#         widget.update_from_parameter(param)

#         assert list(widget.widget.options) == new_options
#         assert widget.value == "X"

#     def test_parameter_validation_during_update(self, basic_parameters):
#         param = basic_parameters.parameters["int_param"]
#         widget = create_widget(param)

#         # Test value clamping
#         widget.value = 15  # Above max
#         assert widget.value == 10  # Should be clamped to max

#         widget.value = -5  # Below min
#         assert widget.value == 0  # Should be clamped to min


# # Callback Tests
# class TestWidgetCallbacks:
#     def test_widget_callback_registration(self, basic_parameters):
#         param = basic_parameters.parameters["int_param"]
#         widget = create_widget(param)

#         callback = Mock()
#         widget.observe(callback)

#         widget.value = 7
#         callback.assert_called_once()

#         # Verify callback is not called when value doesn't change
#         callback.reset_mock()
#         widget.value = 7
#         callback.assert_not_called()

#     def test_callback_disable_reenable(self, basic_parameters):
#         param = basic_parameters.parameters["int_param"]
#         widget = create_widget(param)

#         callback = Mock()
#         widget.observe(callback)

#         widget.disable_callbacks()
#         widget.value = 7
#         callback.assert_not_called()

#         widget.reenable_callbacks()
#         widget.value = 8
#         callback.assert_called_once()

#     def test_multiple_callbacks(self, basic_parameters):
#         param = basic_parameters.parameters["int_param"]
#         widget = create_widget(param)

#         callback1 = Mock()
#         callback2 = Mock()
#         widget.observe(callback1)
#         widget.observe(callback2)

#         widget.value = 7
#         callback1.assert_called_once()
#         callback2.assert_called_once()


# # Deployment Tests
# class TestNotebookDeployer:
#     def test_deployment_initialization(self, basic_parameters):
#         config = LayoutConfig(controls_position="left")
#         deployment = NotebookDeployer(basic_parameters, config)
#         deployment._create_parameter_widgets()

#         assert len(deployment.parameter_widgets) == 4
#         assert deployment.config.controls_position == "left"
#         assert deployment.config.is_horizontal is True

#     def test_parameter_change_handling(self, basic_parameters):
#         deployment = NotebookDeployer(basic_parameters)
#         deployment._create_parameter_widgets()

#         with patch.object(deployment, "_update_plot") as mock_update_plot:
#             with patch.object(deployment, "_sync_widgets_with_state"):
#                 deployment._handle_widget_engagement("text_param")
#                 mock_update_plot.assert_called_once()
