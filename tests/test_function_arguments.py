import pytest
from functools import partial
from syd import make_viewer
from syd.interactive_viewer import InteractiveViewer
from syd.parameters import ParameterUpdateError


def correct_arguments_positional(viewer, state):
    return "correct"


def correct_arguments_kwargs(viewer=None, state=None):
    return "correct"


def correct_arguments_kwargs_extra(viewer=None, state=None, **kwargs):
    return "correct"


def correct_arguments_extra(viewer=None, state=None, extra=None):
    return "correct"


def no_arguments():
    return "external function with no arguments is not allowed"


def one_argument(arg1):
    return "external function with one argument is not allowed"


def three_arguments(arg1, arg2, arg3):
    return "external function with three arguments is not allowed"


def one_kwarg(arg1, *, arg2):
    return "external function with one kwarg is not allowed"


def two_kwargs(*, arg1, arg2):
    return "external function with multiple kwargs is not allowed"


def one_positional_and_one_kwarg(arg1, *, arg2):
    return "external function with one positional and one kwarg is not allowed"


not_callable = "not callable"

valid_lambda_function = lambda viewer, state: "correct"
invalid_lambda_function = lambda: "incorrect"


class MockViewer(InteractiveViewer):
    def correct_arguments_positional(self, state):
        return "correct"

    def correct_arguments_kwargs(self, state=None):
        return "correct"

    def correct_arguments_kwargs_extra(self, state=None, **kwargs):
        return "correct"

    def correct_arguments_extra(self, state=None, extra=None):
        return "correct"

    def one_argument(self):
        return "external function with one argument is not allowed"

    def three_arguments(self, arg2, arg3):
        return "external function with three arguments is not allowed"

    def one_positional_and_one_kwarg(self, *, arg2):
        return "external function with one positional and one kwarg is not allowed"

    @staticmethod
    def correct_arguments_positional_static(self, state):
        return "correct"

    @staticmethod
    def correct_arguments_kwargs_static(self, state=None):
        return "correct"

    @staticmethod
    def correct_arguments_extra_static(self, state=None, extra=None):
        return "correct"

    @staticmethod
    def one_argument_static(self):
        return "external function with one argument is not allowed"

    @staticmethod
    def three_arguments_static(self, arg2, arg3):
        return "external function with three arguments is not allowed"

    @staticmethod
    def one_positional_and_one_kwarg_static(self, *, arg2):
        return "external function with one positional and one kwarg is not allowed"

    @classmethod
    def two_arguments_class(cls, viewer, state):
        return "this is okay"

    @classmethod
    def one_argument_class(cls, viewer):
        return "not two additional arguments"


instance = MockViewer()

# fmt: off
correct_kind_callable_pairs = {
    # Correct external functions
    "correct_positional": ("external", correct_arguments_positional),
    "correct_kwargs": ("external", correct_arguments_kwargs),
    "correct_kwargs_extra": ("external", correct_arguments_kwargs_extra),
    "correct_extra": ("external", correct_arguments_extra),
    "correct_partial_three_args": ("external", partial(three_arguments, arg3="make_arg3_a_kwarg")),
    "correct_partial_extra": ("external", partial(correct_arguments_extra, extra="wrap extra in a partial")),
    "correct_lambda": ("external", valid_lambda_function),
    
    # Correct bound methods
    "correct_bound_positional": ("bound", instance.correct_arguments_positional),
    "correct_bound_kwargs": ("bound", instance.correct_arguments_kwargs),
    "correct_bound_kwargs_extra": ("bound", instance.correct_arguments_kwargs_extra),
    "correct_bound_extra": ("bound", instance.correct_arguments_extra),
    "correct_bound_partial_three": ("bound", partial(instance.three_arguments, arg3="make_arg3_a_kwarg")),
    "correct_bound_partial_extra": ("bound", partial(instance.correct_arguments_extra, extra="wrap extra in a partial")),
    "correct_bound_static_positional": ("bound", instance.correct_arguments_positional_static),
    "correct_bound_static_kwargs": ("bound", instance.correct_arguments_kwargs_static),
    "correct_bound_static_extra": ("bound", instance.correct_arguments_extra_static),
    "correct_bound_static_partial_three": ("bound", partial(instance.three_arguments_static, arg3="make_arg3_a_kwarg")),
    "correct_bound_static_partial_extra": ("bound", partial(instance.correct_arguments_extra_static, extra="wrap extra in a partial")),

    "correct_bound_class": ("bound", instance.two_arguments_class),

    # Use the external kind for these so we just use them directly from a distinct instance
    "correct_bound_other": ("external", instance.three_arguments),
}

incorrect_kind_callable_pairs = {
    # Incorrect external functions
    "incorrect_no_args": ("external", no_arguments),
    "incorrect_one_arg": ("external", one_argument),
    "incorrect_three_args": ("external", three_arguments),
    "incorrect_one_kwarg": ("external", one_kwarg),
    "incorrect_two_kwargs": ("external", two_kwargs),
    "incorrect_pos_and_kwarg": ("external", one_positional_and_one_kwarg),
    "incorrect_partial_state": ("external", partial(correct_arguments_positional, state="wrap state in a partial")),
    "incorrect_partial_viewer": ("external", partial(correct_arguments_positional, viewer="wrap viewer in a partial")),
    "incorrect_partial_extra": ("external", partial(correct_arguments_kwargs, extra="wrap extra in a partial")),
    "incorrect_partial_arg1": ("external", partial(three_arguments, arg1="wrap arg1 in a partial... making all others kwarg-only")),
    "incorrect_not_callable": ("external", not_callable),
    "incorrect_lambda": ("external", invalid_lambda_function),
    
    # Incorrect bound methods
    "incorrect_bound_one": ("bound", instance.one_argument),
    "incorrect_bound_pos_kwarg": ("bound", instance.one_positional_and_one_kwarg),
    "incorrect_bound_static_one": ("bound", instance.one_argument_static),
    "incorrect_bound_static_three": ("bound", instance.three_arguments_static),
    "incorrect_bound_static_pos_kwarg": ("bound", instance.one_positional_and_one_kwarg_static),
    "incorrect_bound_partial_state": ("bound", partial(instance.correct_arguments_positional, state="wrap state in a partial")),
    "incorrect_bound_partial_viewer": ("bound", partial(instance.correct_arguments_positional, viewer="wrap viewer in a partial")),
    "incorrect_bound_partial_extra": ("bound", partial(instance.correct_arguments_kwargs, extra="wrap extra in a partial")),
    "incorrect_bound_partial_arg1": ("bound", partial(instance.three_arguments, arg1="wrap arg1 in a partial... making all others kwarg-only")),
    "incorrect_bound_static_partial_state": ("bound", partial(instance.correct_arguments_positional_static, state="wrap state in a partial")),
    "incorrect_bound_static_partial_viewer": ("bound", partial(instance.correct_arguments_positional_static, viewer="wrap viewer in a partial")),
    "incorrect_bound_static_partial_extra": ("bound", partial(instance.correct_arguments_kwargs_static, extra="wrap extra in a partial")),
    "incorrect_bound_static_partial_arg1": ("bound", partial(instance.three_arguments_static, arg1="wrap arg1 in a partial... making all others kwarg-only")),
    "incorrect_bound_class": ("bound", instance.one_argument_class),

    # Use the external kind for these so we just use them directly from a distinct instance
    "incorrect_bound_other_static": ("external", instance.three_arguments_static),
}
# fmt: on


@pytest.mark.parametrize(
    "name,kind,func",
    [(name, kind, func) for name, (kind, func) in correct_kind_callable_pairs.items()],
)
def test_make_viewer_with_valid_callable(name, kind, func):
    # Test adding an external function in the make_viewer call
    if kind == "external":
        try:
            viewer = make_viewer(func)
        except Exception as e:
            msg = f"make_viewer should accept a function with two positional arguments: {e}"
            assert False, msg

        msg = "viewer.plot should be called with just one positional argument and self implied"
        assert viewer.plot(viewer.get_state()), msg


@pytest.mark.parametrize(
    "name,kind,func",
    [(name, kind, func) for name, (kind, func) in correct_kind_callable_pairs.items()],
)
def test_set_plot_with_valid_callable(name, kind, func):
    # Test adding an external function with set_plot
    try:
        if kind == "external":
            viewer = make_viewer()
        else:
            viewer = instance
        viewer.set_plot(func)
    except Exception as e:
        msg = f"set_plot should accept a function with two positional arguments: {e}"
        assert False, msg

    msg = "viewer.plot should be called with just one positional argument and self implied"
    assert viewer.plot(viewer.get_state()), msg


@pytest.mark.parametrize(
    "name,kind,func",
    [
        (name, kind, func)
        for name, (kind, func) in incorrect_kind_callable_pairs.items()
    ],
)
def test_make_viewer_with_invalid_callable(name, kind, func):
    # Test invalid configurations
    if kind == "external":
        try:
            viewer = make_viewer(func)
        except Exception as e:
            pass  # Exception expected
        else:
            msg = f"make_viewer should not accept a function with two positional arguments: {e}"
            assert False, msg

        try:
            print(viewer)
        except NameError:
            pass  # NameError expected
        else:
            msg = "viewer should not be created if the plot function is invalid"
            assert False, msg


@pytest.mark.parametrize(
    "name,kind,func",
    [
        (name, kind, func)
        for name, (kind, func) in incorrect_kind_callable_pairs.items()
    ],
)
def test_set_plot_with_invalid_callable(name, kind, func):
    def valid_plot(viewer, state):
        return "correct"

    if kind == "external":
        viewer = make_viewer()
    else:
        viewer = instance
    viewer.set_plot(valid_plot)
    try:
        viewer.set_plot(func)
    except Exception as e:
        pass  # Exception expected
    else:
        msg = f"make_viewer should not accept a function with two positional arguments: {e}"
        assert False, msg

    msg = "Setting plot with an invalid function should not overwrite existing plot"
    assert viewer.plot(viewer.get_state()) == "correct", msg

    viewer = make_viewer()
    with pytest.raises(ValueError):
        viewer.set_plot(func)
    try:
        viewer.plot(viewer.get_state())
    except NotImplementedError:
        pass  # NotImplementedError expected
    else:
        msg = "viewer.plot should raise NotImplementedError if no plot function is set"
        assert False, msg


@pytest.mark.parametrize(
    "name,kind,func",
    [(name, kind, func) for name, (kind, func) in correct_kind_callable_pairs.items()],
)
def test_add_button_with_valid_callback(name, kind, func):
    param_name = str(func) + "testing_add_button"
    try:
        if kind == "external":
            viewer = make_viewer()
        else:
            viewer = instance
        viewer.add_button(param_name, label="test", callback=func)
    except Exception as e:
        msg = f"add_button should accept a function with two positional arguments: {e}"
        assert False, msg

    msg = "Button callback should be called with just one positional argument and self implied"
    assert viewer.parameters[param_name].callback(viewer.get_state()), msg


@pytest.mark.parametrize(
    "name,kind,func",
    [
        (name, kind, func)
        for name, (kind, func) in incorrect_kind_callable_pairs.items()
    ],
)
def test_add_button_with_invalid_callback(name, kind, func):
    param_name = str(func) + "testing_add_button"
    if kind == "external":
        viewer = make_viewer()
    else:
        viewer = instance

    try:
        viewer.add_button(param_name, label="test", callback=func)
    except Exception as e:
        pass  # Exception expected
    else:
        msg = "add_button should not accept invalid callback functions"
        assert False, msg

    def good_callback(viewer, state):
        return "good_callback"

    # Test that update_button maintains existing valid callback when given invalid one
    viewer.add_button(param_name, label="test", callback=good_callback)
    with pytest.raises(ParameterUpdateError):
        viewer.update_button(param_name, callback=func)

    callback_return = viewer.parameters[param_name].callback(viewer.get_state())
    msg = "Failing to update the callback should not change the original callback"
    assert callback_return == "good_callback", msg


@pytest.mark.parametrize(
    "name,kind,func",
    [(name, kind, func) for name, (kind, func) in correct_kind_callable_pairs.items()],
)
def test_on_change_with_valid_callback(name, kind, func):
    param_name = str(func) + "testing_on_change"
    try:
        if kind == "external":
            viewer = make_viewer()
        else:
            viewer = instance
        viewer.add_text(param_name, value="test")
        viewer.on_change(param_name, func)
    except Exception as e:
        msg = f"on_change should accept a function with two positional arguments: {e}"
        assert False, msg

    try:
        viewer.perform_callbacks(param_name)
    except Exception as e:
        msg = "Callbacks should not fail when performed with valid functions!"
        assert False, msg


@pytest.mark.parametrize(
    "name,kind,func",
    [
        (name, kind, func)
        for name, (kind, func) in incorrect_kind_callable_pairs.items()
    ],
)
def test_on_change_with_invalid_callback(name, kind, func):
    param_name = str(func) + "testing_on_change"
    if kind == "external":
        viewer = make_viewer()
    else:
        viewer = instance

    try:
        viewer.add_text(param_name, value="test")
        viewer.on_change(param_name, func)
    except Exception as e:
        pass  # Exception expected
    else:
        msg = "on_change should not accept invalid callback functions"
        assert False, msg

    msg = "Callbacks should not be added when they are not valid"
    assert str(func) not in viewer.callbacks, msg
