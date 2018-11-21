# We need this for older python versions, otherwise it will not use the wavedrom module
from __future__ import absolute_import

import json
import os
from os import path
from uuid import uuid4

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.images import Image
from sphinx.errors import SphinxError
from sphinx.ext.graphviz import figure_wrapper
from sphinx.util import copy_static_entry
from sphinx.locale import __
from sphinx.util.docutils import SphinxDirective
from sphinx.util.i18n import search_image_for_language
from wavedrom import WaveDrom

# This exception was not always available..
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

ONLINE_SKIN_JS = "http://wavedrom.com/skins/default.js"
ONLINE_WAVEDROM_JS = "http://wavedrom.com/WaveDrom.js"

WAVEDROM_HTML = """
<div style="overflow-x:auto">
<script type="WaveDrom">
{content}
</script>
</div>
"""


class wavedromnode(nodes.General, nodes.Inline, nodes.Element):
    """
    Special node for wavedrom figures. It is not used for inline javascript.
    """
    pass


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
                with open(filename, 'r') as fp:  # type: ignore
                    code = fp.read()
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
        if (self.env.app.builder.name in ('html', 'dirhtml', 'singlehtml')
            and self.config.wavedrom_html_jsinline):
            text = WAVEDROM_HTML.format(content=code)
            content = nodes.raw(text=text, format='html')
            return [content]

        # Store code in a special docutils node and pick up at rendering
        node = wavedromnode()

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


def determine_format(supported):
    """
    Determine the proper format to render
    :param supported: list of formats that the builder supports
    :return: Preferred format
    """
    order = ['image/svg+xml', 'application/pdf', 'image/png']
    for format in order:
        if format in supported:
            return format
    return None


def render_wavedrom(self, node, outpath, bname, format):
    """
    Render a wavedrom image
    """

    # Try to convert node, raise error with code on failure
    try:
        svgout = WaveDrom().renderWaveForm(0, json.loads(node['code']))
    except JSONDecodeError as e:
        raise SphinxError("Cannot render the following json code: \n{} \n\nError: {}".format(node['code'], e))

    if not os.path.exists(outpath):
        os.makedirs(outpath)

    # SVG can be directly written and is supported on all versions
    if format == 'image/svg+xml':
        fname = "{}.{}".format(bname, "svg")
        fpath = os.path.join(outpath, fname)
        svgout.saveas(fpath)
        return fname

    # It gets a bit ugly, if the output does not support svg. We use cairosvg, because it is the easiest
    # to use (no dependency on installed programs). But it only works for Python 3.
    try:
        import cairosvg
    except:
        raise SphinxError(__("Cannot import 'cairosvg'. In Python 2 wavedrom figures other than svg are "
                             "not supported, in Python 3 ensure 'cairosvg' is installed."))

    if format == 'application/pdf':
        fname = "{}.{}".format(bname, "pdf")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2pdf(svgout.tostring(), write_to=fpath)
        return fname

    if format == 'image/png':
        fname = "{}.{}".format(bname, "png")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2png(svgout.tostring(), write_to=fpath)
        return fname

    raise SphinxError("No valid wavedrom conversion supplied")


def visit_wavedrom(self, node):
    """
    Visit the wavedrom node
    """
    format = determine_format(self.builder.supported_image_types)
    if format is None:
        raise SphinxError(__("Cannot determine a suitable output format"))

    # Create random filename
    bname = "wavedrom-{}".format(uuid4())
    outpath = path.join(self.builder.outdir, self.builder.imagedir)

    # Render the wavedrom image
    imgname = render_wavedrom(self, node, outpath, bname, format)

    # Now we unpack the image node again. The file was created at the build destination,
    # and we can now use the standard visitor for the image node. We add the image node
    # as a child and then raise a SkipDepature, which will trigger the builder to visit
    # children.
    image_node = node['image_node']
    image_node['uri'] = os.path.join(self.builder.imgpath, imgname)
    node.append(image_node)

    raise nodes.SkipDeparture


def builder_inited(app):
    """
    Sets wavedrom_html_jsinline to False for all non-html builders for
    convenience (use ifconf etc.)

    We instruct sphinx to include some javascript files in the output html.
    Depending on the settings provided in the configuration, we take either
    the online files from the wavedrom server, or the locally provided wavedrom
    javascript files
    """
    if (app.config.wavedrom_html_jsinline and
        app.builder.name not in ('html', 'dirhtml', 'singlehtml')):
        app.config.wavedrom_html_jsinline = False

    # Skip for non-html or if javascript is not inlined
    if not app.env.config.wavedrom_html_jsinline:
        return

    if app.config.offline_skin_js_path is not None:
        app.add_javascript(path.basename(app.config.offline_skin_js_path))
    else:
        app.add_javascript(ONLINE_SKIN_JS)
    if app.config.offline_wavedrom_js_path is not None:
        app.add_javascript(path.basename(app.config.offline_wavedrom_js_path))
    else:
        app.add_javascript(ONLINE_WAVEDROM_JS)


def build_finished(app, exception):
    """
    When the build is finished, we copy the javascript files (if specified)
    to the build directory (the static folder)
    """
    # Skip for non-html or if javascript is not inlined
    if not app.env.config.wavedrom_html_jsinline:
        return

    if app.config.offline_skin_js_path is not None:
        copy_static_entry(path.join(app.builder.srcdir, app.config.offline_skin_js_path), path.join(app.builder.outdir, '_static'), app.builder)
    if app.config.offline_wavedrom_js_path is not None:
        copy_static_entry(path.join(app.builder.srcdir, app.config.offline_wavedrom_js_path), path.join(app.builder.outdir, '_static'), app.builder)


def doctree_resolved(app, doctree, fromdocname):
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


def setup(app):
    """
    Setup the extension
    """
    app.add_config_value('offline_skin_js_path', None, 'html')
    app.add_config_value('offline_wavedrom_js_path', None, 'html')
    app.add_config_value('wavedrom_html_jsinline', True, 'html')
    app.add_directive('wavedrom', WavedromDirective)
    app.connect('build-finished', build_finished)
    app.connect('builder-inited', builder_inited)
    app.connect('doctree-resolved', doctree_resolved)

    app.add_node(wavedromnode,
                 html = (visit_wavedrom, None),
                 latex = (visit_wavedrom, None),
                 )

