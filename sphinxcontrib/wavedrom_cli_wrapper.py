'''Supporting file dedicated to the generation of wavedrom images using the official wavedrom-cli executable '''
import os
import subprocess
import shlex
import cairosvg

from sphinx.util.osutil import (
    ensuredir,
    ENOENT,
)

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
        Exception: OSError during execution of the wavedrom command
        Exception: Non-zero return code
        Exception: Invalid image format input string

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
            capture_output=True,
            check=False)
    except OSError as err:
        if err.errno != ENOENT:
            raise
        raise Exception('wavedrom command %r cannot be run' % sphinx.builder.config.wavedrom_cli)
    if process.returncode != 0:
        raise Exception('error while running wavedrom\n\n%s' % process.stderr)

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
        raise Exception('Invalid choice of image format: \n\n%s' % image_format)
    return fname
