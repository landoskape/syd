from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.docutils import SphinxDirective


class ViewModeNode(nodes.General, nodes.Element):
    pass


def visit_view_mode_node_html(self, node):
    mode = node["mode"]
    self.body.append(f'<div class="only-{mode}">')


def depart_view_mode_node_html(self, node):
    self.body.append("</div>")


class ViewModeDirective(SphinxDirective):
    required_arguments = 1  # 'notebook' or 'browser'
    has_content = True

    def run(self):
        mode = self.arguments[0].strip().lower()
        if mode not in ("notebook", "browser"):
            raise self.error("Argument must be 'notebook' or 'browser'.")

        node = ViewModeNode()
        node["mode"] = mode
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


def setup(app):
    app.add_node(
        ViewModeNode, html=(visit_view_mode_node_html, depart_view_mode_node_html)
    )

    app.add_directive("view-mode", ViewModeDirective)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
