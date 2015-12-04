#!/usr/bin/env python
"""
Spine Exporter for Inkscape

Export each layer in the current document to individual PNG files and generate
a Spine JSON file to import.
https://esotericsoftware.com/spine-json-format
"""
import os
import inkex
import json
import subprocess


INKSCAPE_LABEL = "{%s}label" % (inkex.NSS["inkscape"])


class SpineExporter(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option(
			"--outdir",
			action="store",
			type="string",
			dest="outdir",
			default="~",
			help="Path to the export directory"
		)
		self.OptionParser.add_option(
			"--dpi",
			action="store",
			type="float",
			dest="dpi",
			default=90.0,
			help="Resolution to export at"
		)
		self.OptionParser.add_option(
			"--json",
			type="inkbool",
			dest="json",
			help="Create a Spine JSON file",
		)
		self.OptionParser.add_option(
			"--pretty-print",
			type="inkbool",
			dest="pretty",
			help="Pretty-print the JSON file",
		)

	@property
	def svg(self):
		return self.document.getroot()

	@property
	def friendly_name(self):
		docname = self.svg.xpath("//@sodipodi:docname", namespaces=inkex.NSS)
		if docname:
			return docname[0].replace(".svg", "")
		return self.svg.attrib["id"]

	@property
	def layers(self):
		xpath = "./svg:g[@inkscape:groupmode='layer']"

		def get_layers(e):
			ret = []
			sublayers = e.xpath(xpath, namespaces=inkex.NSS)
			if sublayers:
				for sublayer in sublayers:
					ret += get_layers(sublayer)
			else:
				ret.append(e)
			return ret

		return get_layers(self.svg)

	def autocrop_in_place(self, path):
		from PIL import Image
		im = Image.open(path)
		bbox = im.getbbox()
		cropped = im.crop(bbox)
		cropped.save(path)
		global_width, global_height = im.size
		left, top, right, bottom = bbox
		width = right - left
		height = bottom - top
		x = 0.5 * width - (global_width * 0.5) + left
		y = (global_height / 2) - ((top + bottom) / 2)
		return x, y, width, height

	def effect(self):
		outdir = os.path.expanduser(self.options.outdir)
		imagedir = os.path.join(outdir, "images")
		if not os.path.exists(imagedir):
			os.makedirs(imagedir)

		spine_struct = {
			"skeleton": {"images": imagedir},
			"bones": [{"name": "root"}],
			"slots": [],
			"skins": {"default": {}},
			"animations": {"animation": {}}
		}

		for layer in self.layers:
			id = layer.attrib["id"]
			label = layer.attrib.get(INKSCAPE_LABEL, id)
			outfile = os.path.join(imagedir, "%s.png" % (label))

			command = (
				"inkscape",
				"--export-png", outfile,
				"--export-id-only",
				"--export-area-drawing",
				"--export-id", id,
				"--export-dpi", str(self.options.dpi),
				"--file", self.args[-1],
			)

			process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			process.wait()

			# Inkscape and SVG don't make it easy to get the layer positions
			# So instead of immediately generating cropped images, we pass
			# --export-area-drawing which gives us images of the same size.
			# We then get their bounding box and crop them with Pillow.
			x, y, width, height = self.autocrop_in_place(outfile)

			spine_struct["slots"].append({"name": label, "bone": "root", "attachment": label})
			spine_struct["skins"]["default"][label] = {
				label: {"x": x, "y": y, "width": width, "height": height},
			}

		if self.options.json:
			path = os.path.join(outdir, "%s.json" % (self.friendly_name))
			if self.options.pretty:
				args = {"separators": (",", ": "), "indent": 4}
			else:
				args = {"separators": (",", ":")}

			with open(path, "w") as f:
				json.dump(spine_struct, f, **args)


inkex.localize()
effect = SpineExporter()
effect.affect()
