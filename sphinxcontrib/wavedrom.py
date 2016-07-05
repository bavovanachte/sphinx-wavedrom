"""
This sphinx extension allows the user to include wavedrom waveform diagrams 
in its documentation, by just using the textual description, rather than 
generating and including static images.

At the moment, the extension doesn't generate static images itself, but
relies on the js scripts provided by wavedrom to generate them in the browser.

By default, the script will use the js hosted on the wavedrom servers. 
This is the easiest setup, but relies on an active internet connection and a 
stable hosting on wavedrom's side. In the near future, I aim to add the possibility
to use a local version of the js scripting, to allow for offline reading.
"""

from docutils import nodes
from sphinx.util.compat import Directive
from sphinx.util import copy_static_entry
from os import path

ONLINE_SKIN_JS = "http://wavedrom.com/skins/default.js"
ONLINE_WAVEDROM_JS = "http://wavedrom.com/WaveDrom.js"

WAVEDROM_SETUP = """
<script type="WaveDrom">
"""

WAVEDROM_TEARDOWN = """
 </script>
<script type="text/javascript">
(function() {
    try {
        WaveDrom.ProcessAll();
    } catch(e) {}
})();
</script>
"""

class WavedromDirective(Directive):
    """
    Directive to declare items and their traceability relationships.
    Syntax::

      .. wavedrom::

         [wavedrom_description]

    This directive will trigger the generation of a "raw" docutils node.
    The raw html content will be the same as the one passed on to the directive,
    but surrounded by some HTML tags that allow rendering of the image through javascript.

    """
    # Setting has_content to true marks that this directive has content (stored in self.content)
    has_content = True

    def run(self):
        env = self.state.document.settings.env
        text = "{wd_setup}{content}{wd_teardown}".format(wd_setup=WAVEDROM_SETUP, 
                                                         content="\n".join(self.content),
                                                         wd_teardown=WAVEDROM_TEARDOWN)
        content = nodes.raw(text=text, format='html')
        return [content]

def builder_inited(app):
    if app.config.offline_skin_js_path is not None:
        app.add_javascript(app.config.offline_skin_js_path)
    else:
        app.add_javascript(ONLINE_SKIN_JS)
    if app.config.offline_wavedrom_js_path is not None:
        app.add_javascript(app.config.offline_wavedrom_js_path)
    else:
        app.add_javascript(ONLINE_WAVEDROM_JS)

def build_finished(app, exception):
    if app.config.offline_skin_js_path is not None:
        copy_static_entry(path.join(app.builder.srcdir, app.config.offline_skin_js_path), path.join(app.builder.outdir, '_static'), app.builder)
    if app.config.offline_wavedrom_js_path is not None:
        copy_static_entry(path.join(app.builder.srcdir, app.config.offline_wavedrom_js_path), path.join(app.builder.outdir, '_static'), app.builder)

# -----------------------------------------------------------------------------
# Extension setup

def setup(app):
    app.add_config_value('offline_skin_js_path', None, 'html')
    app.add_config_value('offline_wavedrom_js_path', None, 'html')
    app.add_directive('wavedrom', WavedromDirective)
    app.connect('build-finished', build_finished)
    app.connect('builder-inited', builder_inited)