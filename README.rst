Sphinx wavedrom extension 
=========================

A sphinx extension that allows including wavedrom diagrams by using it's text-based representation

Wavedrom online editor and tutorial: http://wavedrom.com/

.. image:: https://travis-ci.org/bavovanachte/sphinx-wavedrom.svg?branch=master
    :target: https://travis-ci.org/bavovanachte/sphinx-wavedrom

Installation
------------

The wavedrom extension can be installed using pip:

::
	
	pip install sphinxcontrib-wavedrom

and by adding **'sphinxcontrib.wavedrom'** to the extensions list in your conf.py file.

Directives
----------

The extension is useable in the form of an extra wavedrom directive, as shown below.

::

	.. wavedrom::

		{ signal: [
		  	{ name: "clk",  wave: "P......" },
		  	{ name: "bus",  wave: "x.==.=x", data: ["head", "body", "tail", "data"] },
		  	{ name: "wire", wave: "0.1..0." }
		]}

The extension will not generate an image out of the diagram description itself,
but it will surround it with some html and js tags in the final html document
that allow the images to be rendered by the browser.

Configuration
-------------

The extension can work in 2 modes:

- Online mode: 	the extension links to the javascript file(s) provided by the wavedrom server
- Offline mode: the extension uses the javascript file(s) that are saved locally on your drive.

The online mode is the default one. This requires no configuration in conf.py

If offline mode is desired, the following parameters need to be provided:

- **offline_skin_js_path** : the path to the skin javascript file (the url to the online version is "http://wavedrom.com/skins/default.js")
- **offline_wavedrom_js_path** : the path to the wavedrom javascript file (the url to the online version is "http://wavedrom.com/WaveDrom.js")

The paths given for these configurations need to be relative to the configuration directory (the directory that contains conf.py)

Examples
--------

In the `example` folder, you can find a couple of examples (taken from the wavedrom tutorial), illustration the use of the extension.
