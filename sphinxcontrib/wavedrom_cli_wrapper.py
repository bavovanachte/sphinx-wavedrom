import os
import subprocess
import shlex

from sphinx.util.osutil import (
    ensuredir,
    ENOENT,
)


def _ntunquote(s):
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s

def _split_cmdargs(args):
    if isinstance(args, (tuple, list)):
        return list(args)
    if os.name == 'nt':
        return list(map(_ntunquote, shlex.split(args, posix=False)))
    else:
        return shlex.split(args, posix=True)

def generate_wavedrom_args(self, input_filename, output_filename):
    # npx wavedrom-cli -i mywave.json5 -s mywave.svg
    args = _split_cmdargs(self.builder.config.wavedrom_cli)
    args.extend(['-i', input_filename])
    args.extend(['-s', output_filename])
    return args

def render_wavedrom_cli(self, node, outpath, bname, format):
    ensuredir(outpath)
    input_json = os.path.join(outpath, "{}.{}".format(bname, 'json5'))
    output_svg = os.path.join(outpath, "{}.{}".format(bname, 'svg'))
    with open(input_json, 'w') as f:
        f.write(node['code'])
    try:
        p = subprocess.run(generate_wavedrom_args(self, input_json, output_svg), capture_output=True)
    except OSError as err:
        if err.errno != ENOENT:
            raise
        raise PlantUmlError('wavedrom command %r cannot be run' % self.builder.config.wavedrom_cli)
    if p.returncode != 0:
        raise Exception('error while running wavedrom\n\n%s' % p.stderr)

        # SVG can be directly written and is supported on all versions
    if format == 'image/svg+xml':
        fname = "{}.{}".format(bname, "svg")
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
        cairosvg.svg2pdf(url=output_svg, write_to=fpath)
        return fname

    if format == 'image/png':
        fname = "{}.{}".format(bname, "png")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2png(url=output_svg, write_to=fpath)
        return fname