from types import SimpleNamespace
from unittest.mock import Mock, patch

from syd.notebook_deployment.deployer import NotebookDeployer


def _figure_with_png(png_bytes):
    figure = Mock()
    figure.savefig.side_effect = lambda buffer, **_: buffer.write(png_bytes)
    return figure


def test_inline_display_replaces_image_value_without_publishing_output():
    deployer = NotebookDeployer.__new__(NotebookDeployer)
    deployer.backend_type = "inline"
    deployer._last_figure = None
    deployer.plot_image = SimpleNamespace(value=b"")
    deployer.plot_output = Mock()
    first_figure = _figure_with_png(b"first png")
    second_figure = _figure_with_png(b"second png")

    with patch("syd.notebook_deployment.deployer.display") as display_mock:
        with patch("syd.notebook_deployment.deployer.plt.close") as close_mock:
            deployer._display_figure(first_figure)
            assert deployer.plot_image.value == b"first png"

            deployer._display_figure(second_figure)
            assert deployer.plot_image.value == b"second png"

    display_mock.assert_not_called()
    assert deployer.plot_output.mock_calls == []
    close_mock.assert_any_call(first_figure)
    close_mock.assert_any_call(second_figure)
    assert deployer._last_figure is second_figure
