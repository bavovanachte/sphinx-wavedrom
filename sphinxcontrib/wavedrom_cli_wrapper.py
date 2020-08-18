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
        try:
            p = subprocess.run(generate_wavedrom_args(self, input_json, output_svg), capture_output=True)
        except OSError as err:
            if err.errno != ENOENT:
                raise
            raise PlantUmlError('wavedrom command %r cannot be run' % self.builder.config.wavedrom_cli)
        if p.returncode != 0:
            raise Exception('error while running wavedrom\n\n%s' % p.stderr)
        return output_svg
    finally:
        f.close()