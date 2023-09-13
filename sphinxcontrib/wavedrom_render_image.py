'''Supporting file dedicated to the generation of wavedrom images using the official wavedrom-cli executable '''
import os
import subprocess
import shlex
from uuid import uuid4
import cairosvg
from wavedrom import render
from sphinx.errors import SphinxError
import errno

# This exception was not always available..
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from sphinx.util.osutil import ensuredir

ENOENT = getattr(errno, 'ENOENT', 0)

def determine_format(supported):
    """
    Determine the proper format to render
    :param supported: list of formats that the builder supports
    :return: Preferred format
    """
    order = ['image/svg+xml', 'application/pdf', 'image/png']
    for image_format in order:
        if image_format in supported:
            return image_format
    return None


def render_wavedrom_py(node, outpath, bname, image_format):
    """
    Render a wavedrom image
    """
    # Try to convert node, raise error with code on failure
    try:
        svgout = render(node["code"])
    except Exception:
        print(
            "Cannot render the following json code: \n{} \n\n".format(
                node['code']),
            file=sys.stderr)
        raise

    if not os.path.exists(outpath):
        os.makedirs(outpath)

    # SVG can be directly written and is supported on all versions
    if image_format == 'image/svg+xml':
        fname = "{}.{}".format(bname, "svg")
        fpath = os.path.join(outpath, fname)
        svgout.saveas(fpath)
        return fname

    if image_format == 'application/pdf':
        fname = "{}.{}".format(bname, "pdf")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2pdf(svgout.tostring(), write_to=fpath)
        return fname

    if image_format == 'image/png':
        fname = "{}.{}".format(bname, "png")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2png(svgout.tostring(), write_to=fpath)
        return fname

    raise SphinxError("No valid wavedrom conversion supplied")


def render_wavedrom_image(sphinx, node):
    """
    Visit the wavedrom node
    """
    image_format = determine_format(sphinx.builder.supported_image_types)
    if image_format is None:
        raise SphinxError("Cannot determine a suitable output format")

    # Create random filename
    bname = "wavedrom-{}".format(uuid4())
    outpath = os.path.join(sphinx.builder.outdir, sphinx.builder.imagedir)

    # Render the wavedrom image
    if sphinx.builder.config.render_using_wavedrompy:
        imgname = render_wavedrom_py(node, outpath, bname, image_format)
    else:
        imgname = render_wavedrom_cli(sphinx, node, outpath, bname, image_format)

    # Now we unpack the image node again. The file was created at the build destination,
    # and we can now use the standard visitor for the image node. We add the image node
    # as a child and then raise a SkipDepature, which will trigger the builder to visit
    # children.
    image_node = node['image_node']
    image_node['uri'] = os.path.join(sphinx.builder.imgpath, imgname)
    node.append(image_node)

def _ntunquote(string_to_unquote):
    '''Function used to unquote windows strings

    Due to some funky business with windows command splitting using shlex, we might still need to unquote
    the shlex.split result. That happens here.

    Args:
        string_to_unquote (str): String to unquote.

    Returns:
        str: The input string stripped of any remaining quote characters
    '''
    if string_to_unquote.startswith('"') and string_to_unquote.endswith('"'):
        return string_to_unquote[1:-1]
    return string_to_unquote

def _split_cmdargs(args):
    '''Function for splitting the wavedrom command for use by subprocess

    Args:
        args (str): The wavedrom command to split into chunks

    Returns:
        list: The split wavedrom command
    '''
    if isinstance(args, (tuple, list)):
        return list(args)
    if os.name == 'nt':
        return list(map(_ntunquote, shlex.split(args, posix=False)))
    return shlex.split(args, posix=True)

def generate_wavedrom_args(sphinx, input_filename, output_filename):
    ''' Function for constructing the wavedrom command line

    Args:
        sphinx (sphinx): Sphinx instance
        input_filename (str): The filename of the json5 input file
        output_filename (str): The filename of the svg output file

    Returns:
        list: The split command-line arguments for running wavedrom-cli
    '''
    # npx wavedrom-cli -i mywave.json5 -s mywave.svg
    args = _split_cmdargs(sphinx.builder.config.wavedrom_cli)
    args.extend(['-i', input_filename])
    args.extend(['-s', output_filename])
    return args

WAVEDROM_NOT_FOUND = '''
Wavedrom command %r cannot be run. Versions >3.0.0 use wavedrom-cli as the default rendering engine for the diagrams,
which may not be available or installable on your system.
A pure python wavedrom implementation (wavedrompy) is available as alternative and can be activated by configuring
"render_using_wavedrompy = True" in your conf.py. However, be aware that its results may differ from the official
wavedrom tool
'''

def render_wavedrom_cli(sphinx, node, outpath, bname, image_format):
    '''Function for generating the image using the wavedrom-cli executable

    Args:
        sphinx (sphinx): Sphinx instance
        node (wavedromnode): The wavedrom node containing the wavedrom json content
        outpath (str): The path where the (temporary) output should be written
        bname (str): The filename (without full path) to be used for the file generation
        image_format (str): The desired image format. Possible options are:

            - "image/svg+xml"
            - "application/pdf"
            - "image/png"

    Returns:
        str: The filename (without full path) of the generated image output

    Raises:
        OSError: File not found
        SphinxError: OSError during execution of the wavedrom command
        SphinxError: Non-zero return code
        SphinxError: Invalid image format input string

    '''
    fname = None
    ensuredir(outpath)
    input_json = os.path.join(outpath, "{}.{}".format(bname, 'json5'))
    output_svg = os.path.join(outpath, "{}.{}".format(bname, 'svg'))
    with open(input_json, 'w') as input_json_file:
        input_json_file.write(node['code'])
    try:
        process = subprocess.run(
            generate_wavedrom_args(sphinx, input_json, output_svg),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            check=False)
    except OSError as err:
        if err.errno != ENOENT:
            raise
        raise SphinxError(WAVEDROM_NOT_FOUND % sphinx.builder.config.wavedrom_cli)
    if process.returncode != 0:
        raise SphinxError('error while running wavedrom\n\n%s' % process.stderr)

        # SVG can be directly written and is supported on all versions
    if image_format == 'image/svg+xml':
        fname = "{}.{}".format(bname, "svg")
    elif image_format == 'application/pdf':
        fname = "{}.{}".format(bname, "pdf")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2pdf(url=output_svg, write_to=fpath)
    elif image_format == 'image/png':
        fname = "{}.{}".format(bname, "png")
        fpath = os.path.join(outpath, fname)
        cairosvg.svg2png(url=output_svg, write_to=fpath)
    else:
        raise SphinxError('Invalid choice of image format: \n\n%s' % image_format)
    return fname
