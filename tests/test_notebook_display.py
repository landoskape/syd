from types import SimpleNamespace
from unittest.mock import Mock, patch

from syd.notebook_deployment.deployer import NotebookDeployer


def _figure_with_png(marker, width):
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + width.to_bytes(4, byteorder="big")
        + (600).to_bytes(4, byteorder="big")
        + marker
    )
    figure = Mock()
    figure.dpi = 100
    figure.savefig.side_effect = lambda buffer, **_: buffer.write(png_bytes)
    return figure, png_bytes


def test_inline_display_replaces_image_value_without_publishing_output():
    deployer = NotebookDeployer.__new__(NotebookDeployer)
    deployer.backend_type = "inline"
    deployer._last_figure = None
    deployer.plot_image = SimpleNamespace(
        value=b"",
        layout=SimpleNamespace(width=None),
    )
    deployer.plot_output = Mock()
    first_figure, first_png = _figure_with_png(b"first png", width=1300)
    second_figure, second_png = _figure_with_png(b"second png", width=800)

    with patch("syd.notebook_deployment.deployer.display") as display_mock:
        with patch("syd.notebook_deployment.deployer.plt.close") as close_mock:
            deployer._display_figure(first_figure)
            assert deployer.plot_image.value == first_png
            assert deployer.plot_image.layout.width == "650px"

            deployer._display_figure(second_figure)
            assert deployer.plot_image.value == second_png
            assert deployer.plot_image.layout.width == "400px"

    display_mock.assert_not_called()
    assert deployer.plot_output.mock_calls == []
    first_figure.savefig.assert_called_once_with(
        first_figure.savefig.call_args.args[0],
        format="png",
        bbox_inches="tight",
        dpi=200,
    )
    close_mock.assert_any_call(first_figure)
    close_mock.assert_any_call(second_figure)
    assert deployer._last_figure is second_figure
