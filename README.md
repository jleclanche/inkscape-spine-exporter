# Inkscape Spine Exporter

Exports an SVG file from Inkscape to [Spine](https://esotericsoftware.com).
Can generate a [Spine JSON file](https://esotericsoftware.com/spine-json-format).


## Installation

* Copy `spine_exporter.inx` and `spine_exporter.py`
* Restart Inkscape

## Usage

If the installation worked, you should see an "Export to Spine" submenu in the
Extensions menu. Click it and modify the Output Directory at will.

In that directory will be generated one image for each leaf layer. By default,
a JSON file will be generated in the output directory and images will be output
to the `./images` directory within it.
