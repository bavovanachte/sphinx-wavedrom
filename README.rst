Sphinx wavedrom extension 
=========================

A sphinx extension that allows including wavedrom diagrams by using it's text-based representation

Wavedrom online editor and tutorial: http://wavedrom.com/

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

At the moment, the extension does not require any configuration in conf.py.

In the future, I hope to make it possible to specify the path to a local js script, 
instead of using the one provided on the wavedrom server,

Limitations
-----------

At the moment, the extension requires an active internet connection to work.
The generation of the wavedrom images is done based on a JS script, provided by the wavedrom server.

Examples
--------

In the `example` folder, you can find a couple of examples (taken from the wavedrom tutorial), illustration the use of the extension.