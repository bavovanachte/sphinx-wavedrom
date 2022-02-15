'''Sphinx plugin for generating waveform diagrams based on the wavedrom tool'''
# We need this for older python versions, otherwise it will not use the wavedrom module
from __future__ import absolute_import

from os import path

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image
from sphinx.ext.graphviz import figure_wrapper
from sphinx.util.fileutil import copy_asset_file
from sphinx.locale import __
from sphinx.util.docutils import SphinxDirective
from sphinx.util.i18n import search_image_for_language
from .wavedrom_render_image import render_wavedrom_image

ONLINE_SKIN_JS = "{url}/skins/default.js"
ONLINE_WAVEDROM_JS = "{url}/wavedrom.min.js"

WAVEDROM_HTML = """
<div style="overflow-x:auto">
<script type="WaveDrom">
{content}
</script>
</div>
"""

class WavedromNode(nodes.General, nodes.Inline, nodes.Element):
    """
    Special node for wavedrom figures. It is not used for inline javascript.
    """
    # pass


class WavedromDirective(Image, SphinxDirective):
    """
    Directive to insert a wavedrom image.

    It derives from image, but is plain html when inline javascript is used.
    """
    has_content = True

    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False

    option_spec = Image.option_spec.copy()
    option_spec['caption'] = directives.unchanged
    has_content = True

    def run(self):
        if self.arguments:
            # Read code from file
            document = self.state.document
            if self.content:
                return [document.reporter.warning(
                    __('wavedrom directive cannot have both content and '
                       'a filename argument'), line=self.lineno)]
            argument = search_image_for_language(self.arguments[0], self.env)
            rel_filename, filename = self.env.relfn2path(argument)
            self.env.note_dependency(rel_filename)
            try:
                with open(filename, 'r') as file_pointer:  # type: ignore
                    code = file_pointer.read()
            except (IOError, OSError):
                return [document.reporter.warning(
                    __('External wavedrom json file %r not found or reading '
                       'it failed') % filename, line=self.lineno)]
        else:
            # Read code from given content
            code = "\n".join(self.content)
            if not code.strip():
                return [self.state_machine.reporter.warning(
                    __('Ignoring "wavedrom" directive without content.'),
                    line=self.lineno)]

        # For html output with inline JS enabled, just return plain HTML
        if (self.env.app.builder.name in ('html', 'dirhtml', 'singlehtml') and self.config.wavedrom_html_jsinline):
            text = WAVEDROM_HTML.format(content=code)
            content = nodes.raw(text=text, format='html')
            return [content]

        # Store code in a special docutils node and pick up at rendering
        node = WavedromNode()

        node['code'] = code
        wd_node = node # point to the actual wavedrom node

        # A caption option turns this image into a Figure
        caption = self.options.get('caption')
        if caption:
            node = figure_wrapper(self, wd_node, caption)
            self.add_name(node)

        # Run image directive processing for the options, supply dummy argument, otherwise will fail.
        # We don't actually replace this node by the image_node and will also not make it a child,
        # because intermediate steps, like converters, depend on the file being in sources. We don't
        # want to generate any files in the user sources. Store the image_node private to this node
        # and not in the docutils tree and use it later. Revisit this when the situation changes.
        self.arguments = ["dummy"]
        (wd_node['image_node'],) = Image.run(self)

        return [node]

def builder_inited(app):
    """
    Sets wavedrom_html_jsinline to False for all non-html builders for
    convenience (use ifconf etc.)

    We instruct sphinx to include some javascript files in the output html.
    Depending on the settings provided in the configuration, we take either
    the online files from the wavedrom server, or the locally provided wavedrom
    javascript files
    """
    if (app.config.wavedrom_html_jsinline and app.builder.name not in ('html', 'dirhtml', 'singlehtml')):
        app.config.wavedrom_html_jsinline = False

    # Skip for non-html or if javascript is not inlined
    if not app.env.config.wavedrom_html_jsinline:
        return

    if app.config.offline_skin_js_path is not None:
        app.add_js_file(path.basename(app.config.offline_skin_js_path))
    else:
        app.add_js_file(ONLINE_SKIN_JS.format(url=app.config.online_wavedrom_js_url))
    if app.config.offline_wavedrom_js_path is not None:
        app.add_js_file(path.basename(app.config.offline_wavedrom_js_path))
    else:
        app.add_js_file(ONLINE_WAVEDROM_JS.format(url=app.config.online_wavedrom_js_url))


def build_finished(app, _exception):
    """
    When the build is finished, we copy the javascript files (if specified)
    to the build directory (the static folder)
    """
    # Skip for non-html or if javascript is not inlined
    if not app.env.config.wavedrom_html_jsinline:
        return

    if app.config.offline_skin_js_path is not None:
        copy_asset_file(
            path.join(app.builder.srcdir, app.config.offline_skin_js_path),
            path.join(app.builder.outdir, '_static'),
            app.builder)
    if app.config.offline_wavedrom_js_path is not None:
        copy_asset_file(
            path.join(app.builder.srcdir, app.config.offline_wavedrom_js_path),
            path.join(app.builder.outdir, '_static'),
            app.builder)


def doctree_resolved(app, doctree, _fromdocname):
    """
    When the document, and all the links are fully resolved, we inject one
    raw html element for running the command for processing the wavedrom
    diagrams at the onload event.
    """
    # Skip for non-html or if javascript is not inlined
    if not app.env.config.wavedrom_html_jsinline:
        return

    text = """
    <script type="text/javascript">
        function init() {
            WaveDrom.ProcessAll();
        }
        window.onload = init;
    </script>"""
    doctree.append(nodes.raw(text=text, format='html'))

def visit_wavedrom(sphinx, node):
    '''WavedromNode visit function. This function will generate an image that is included in the document

    Args:
        sphinx (sphinx): Sphinx instance
        node (WavedromNode): WavedromNode that is being processed

    Raises:
        SkipDeparture: Highlights to sphinx that a departure callback is not needed
    '''
    render_wavedrom_image(sphinx, node)
    raise nodes.SkipDeparture

def setup(app):
    """
    Setup the extension
    """
    app.add_config_value('offline_skin_js_path', None, 'html')
    app.add_config_value('offline_wavedrom_js_path', None, 'html')
    app.add_config_value('online_wavedrom_js_url', "https://wavedrom.com", 'html')
    app.add_config_value('wavedrom_html_jsinline', True, 'html')
    app.add_config_value('wavedrom_cli', "npx wavedrom-cli", 'html')
    app.add_config_value('render_using_wavedrompy', False, 'html')
    app.add_directive('wavedrom', WavedromDirective)
    app.connect('build-finished', build_finished)
    app.connect('builder-inited', builder_inited)
    app.connect('doctree-resolved', doctree_resolved)

    app.add_node(WavedromNode,
                 html=(visit_wavedrom, None),
                 latex=(visit_wavedrom, None),
                 )

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True
    }
