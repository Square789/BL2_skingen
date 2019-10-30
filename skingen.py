if __name__ != "__main__":
	raise RuntimeError("Please run this script directly.")

import sys
import os
import time
import re
from pathlib import Path
import logging
from pprint import pprint
import argparse
from math import log2

import numpy # gotta get that sweet C array
from PIL import Image, ImageFilter, ImageDraw

from bl2_skingen.unreal_notation import Parser as UParser
from bl2_skingen.unreal_notation import UnrealNotationParseError
from bl2_skingen.imaging.overlay import overlay_3D # pylint: disable=import-error, no-name-in-module
from bl2_skingen.imaging.darken import darken # pylint: disable=import-error, no-name-in-module
from bl2_skingen.imaging.multiply_sqrt import multiply # pylint: disable=import-error, no-name-in-module
from bl2_skingen.imaging.ue_color_diff import ue_color_diff # pylint: disable=import-error, no-name-in-module

# Flex tape the PIL.Image module's logger
logging.getLogger("PIL.Image").setLevel(60)

__author__ = "Square789"
__version__ = "1.0.0"

SKINGEN_LOGGER = logging.getLogger(__name__)

CLASSES = ("Assassin", "Mechro", "Mercenary", "Soldier", "Siren", "Psycho")

PROPSFILE = "MaterialInstanceConstant\\Mati_{}_{}.props.txt"

TEXTURE_FILE = "Texture2D\\{}.tga"
UE_TEX_SEP = "."
RE_TEXTURE_UE_INTERNAL_PATH = re.compile(r"Texture2D'(.*)'") # NOTE: MAYBE \' IS A VALID ESC SEQUENCE
RE_DEFINES_CHNL_COL = re.compile(r"p_([ABC])Color(.*)$")
MAP_TEX_PARAM_NAME_TO_PART_ATTR = {"p_Normal": "nrm", "p_Diffuse": "dif", "p_Masks": "msk"}

MAP_COLOR_TO_IDX = {"A":0, "B":1, "C":2}
MAP_NAME_TO_IDX = {"shadow":0, "midtone":1, "hilight":2}
MAP_CHNL_TO_IDX = {"R":0, "G":1, "B":2, "A":3}

logging.getLogger().setLevel(0) # this magically works, whoop-de-doo

class Bodypart():
	"""Small namespace for different files of Head/Body.
	Name will be retrievable by the properties cap, lwr and upr.
	"""
	props = None
	props_dict = None
	dif = None
	msk = None
	nrm = None

	def __init__(self, name):
		self.name = name
	def __format__(self, idk):
		return self.lwr
	@property
	def cap(self):
		return self.name.capitalize()
	@property
	def lwr(self):
		return self.name.lower()
	@property
	def upr(self):
		return self.name.upper()

class SkinGenerator():
	"""Main Program class that takes control of the command line."""
	body = Bodypart("Body")
	head = Bodypart("Head")
	skin_name = None
	skin_type = None

	def __init__(self, in_dir, out_dir, no_ask, silence):
		self.in_dir = Path(in_dir)
		self.out_dir = Path(out_dir)
		self.in_dir = self.in_dir.absolute()
		self.out_dir = self.out_dir.absolute()

		self.logger = SKINGEN_LOGGER
		log_hdlr = logging.StreamHandler(sys.stdout)
		fmtr = logging.Formatter("{message}", None, "{")
		log_hdlr.setFormatter(fmtr)
		self.logger.addHandler(log_hdlr)
		if silence > 3: silence = 3
		self.logger.setLevel(21 + (silence * 3))

		self._determine_params()

	def _determine_params(self):
		for i in CLASSES:
			if i[0] in self.in_dir.stem:
				self.class_ = i[1]
				break
		else:
			raise ValueError("Unable to find class in path name: " + self.in_dir.stem)
		try:
			tmp = self.in_dir.stem.split("_")
			self.skin_name = tmp[3]
			self.skin_type = tmp[2]
		except IndexError:
			raise ValueError("Path not conforming to expected format.")

	def run(self):
		"""Do the thing."""
		self.logger.log(22, f"Input directory: {self.in_dir}")
		self.logger.log(22, f"Output directory: {self.out_dir}")
		self.logger.log(22, f"Seeking for props files...")
		self._locate_props_files()
		self.logger.log(22, f"Parsing props files and getting textures...")
		self._parse_props_files()
		self.logger.log(22, f"Fetching and validating textures...")
		self._get_textures()
		self.logger.log(25, f"===Generating body file===")
		self._generate_image(self.body)
		self.logger.log(25, f"===Generating head file===")
		self._generate_image(self.head)

	@staticmethod
	def is_perfect_square(img: Image.Image):
		"""Returns True if the input image's dimensions are
		4x4, 8x8, 16x16, ..., 1024x1024, 2048x2048 etc.
		"""
		img_sz = img.size
		if img_sz[0] != img_sz[1]:
			return False
		if not log2(img_sz[0]).is_integer():
			return False
		return True

	def dump_color_palette(self, colordict):
		"""
		! Debug method !
		Dumps a palette img called palette.png into the working directory.
		"""
		color_names = ("A", "B", "C")
		shm_names = ("shadow", "midtone", "hilight")
		palette_img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
		y_offset = 0
		x_offset = 0
		cname_i = 0
		sname_i = 0
		draw_agent = ImageDraw.ImageDraw(palette_img)
		for color in colordict:
			for shm in color:
				draw_agent.rectangle(
					(x_offset * 64 + 16 * (x_offset + 1), y_offset * 64 + 16 * (y_offset + 1),
					((x_offset + 1) * 64) + 16 * x_offset, (y_offset + 1) * 64 + 16* y_offset),
					fill = tuple([int(round(i)) for i in (shm[0], shm[1], shm[2], shm[3])]), )
				draw_agent.text( (x_offset * 64 + 16 * (x_offset + 1), y_offset * 64 + 16 * (y_offset + 1) + 64), f"{color_names[cname_i]} {shm_names[sname_i]}", fill = (0, 0, 0, 255) )
				x_offset += 1
				sname_i += 1
			x_offset = 0
			sname_i = 0
			y_offset += 1
			cname_i += 1
		palette_img.save(Path(self.out_dir, "palette.png"))

	def _locate_props_files(self):
		"""Seeks and confirms existence of the props files."""
		for part in (self.body, self.head):
			tmp_pat = Path(self.in_dir, PROPSFILE.format(self.skin_name, part.cap))
			if not tmp_pat.exists():
				self.logger.log(50, f"COULD NOT FIND {tmp_pat}.")
				raise FileNotFoundError(tmp_pat.__str__())
			setattr(part, "props", tmp_pat)

			self.logger.log(20, f"\tFound {tmp_pat.name}")

	def _parse_props_files(self):
		"""Assumes both self.body and self.head contain links to the
		props files, parses those and stores colouring information in
		the part's props_dict attribute.
		"""
		for part in (self.body, self.head):
			with open(part.props, "r") as h:
				u_prsr = UParser(h.read())
			try:
				res = u_prsr.parse()
			except UnrealNotationParseError:
				self.logger.log(50, f"Error parsing Unreal Notation file")
				raise
			part.props_dict = res

	def _get_textures(self):
		"""Reads textures from self.body.props_dict and
		self.head.props_dics, then checks whether they exist (as tga).
		If they do, stores them in the respective objects.
		"""
		#I need: dif, nrm, msk
		for part in (self.body, self.head):
			for param_dict in part.props_dict["TextureParameterValues"]:
				if param_dict["ParameterName"] not in MAP_TEX_PARAM_NAME_TO_PART_ATTR:
					continue
				attr = MAP_TEX_PARAM_NAME_TO_PART_ATTR[param_dict["ParameterName"]]

				ue_tex_name = RE_TEXTURE_UE_INTERNAL_PATH.search(param_dict["ParameterValue"])
				if not ue_tex_name:
					self.logger.log(50, "Could not apply regex to get texture file.")
					raise ValueError()
				ue_tex_name = ue_tex_name[1]
				ue_tex_name = ue_tex_name.split(UE_TEX_SEP)[-1]
				tmp_pat = Path(self.in_dir, TEXTURE_FILE.format(ue_tex_name))

				setattr(part, attr, tmp_pat)
				self.logger.log(20, f"\t{attr} {part.cap}: {tmp_pat.name}")

	def _generate_image(self, part):
		self.logger.log(20, f"Opening {part.dif}")
		dif_img = Image.open(part.dif)
		x, y = dif_img.size

		self.logger.log(20, f"Opening {part.msk} and expanding")
		msk_img = Image.open(part.msk)
		if not self.is_perfect_square(msk_img):
			raise ValueError("Image has bad constraints.")

		m_x, m_y = msk_img.size

		if m_x != x or m_y != y:
			raise ValueError("Well this shouldn't happen but the dif and mask images are of different sizes.")

		soft_mask = msk_img.resize((x, y), box = (0.0, 0.0, x/2, float(y)))
		hard_mask = msk_img.resize((x, y), box = (x/2, 0.0, float(x), float(y)), resample = Image.NEAREST)
		#hmmod0 = hard_mask.filter(ImageFilter.SMOOTH)
		#hmmod1 = hard_mask.filter(ImageFilter.SMOOTH_MORE)
		#hmmod0.show()
		#hmmod1.show()

		#raise NotImplementedError()

		self.logger.log(20, f"Reading and converting color information...")

		colors = numpy.ndarray((3, 3, 4), dtype = numpy.uint8)
		colors[:] = 255 # Sometimes, colors are not specified, set them to full then
		# [0]: A, [1]: B, [2]: C
		# [x][0]: "shadow", [x][1]: "mid", [x][2]: "hilight"
		# [x][y][0]: R, [x][y][1]: G, [x][y][2]: B, [x][y][3]: A

		for i in part.props_dict["VectorParameterValues"]:
			color_name_match = RE_DEFINES_CHNL_COL.match(i["ParameterName"])
			if color_name_match:
				nrm_colors = [0, 0, 0, 0]
				mul = 1
				for val in i["ParameterValue"].values():
					val = float(val.strip())
					if val > 1:
						mul = 1/val

				for chnl, val in i["ParameterValue"].items():
					nrm_colors[MAP_CHNL_TO_IDX[chnl]] = \
						round(((float(val.strip())) * 255) * mul)

				colors[MAP_COLOR_TO_IDX[color_name_match[1]]] \
					[MAP_NAME_TO_IDX[color_name_match[2].lower()]] = \
					nrm_colors

		######DEBUG BLOCK
		self.logger.log(19, f"Color infs:\n{colors}")
		#self.dump_color_palette(colors)

		self.logger.log(25, f"Generating overlay image...")
		hard_mask_arr = numpy.array(hard_mask)
		soft_mask_arr = numpy.array(soft_mask)
		overlay_arr = ue_color_diff(hard_mask_arr, soft_mask_arr, colors)

		self.logger.log(25, f"Merging overlay and base image...")
		dif_img_arr = numpy.array(dif_img)
		final_arr = multiply(overlay_arr, dif_img_arr)
		self.logger.log(25, f"Saving generated texture...")
		targetpath = Path(self.out_dir, f"final_{part.lwr}.png")
		Image.fromarray(final_arr).save(targetpath)


if __name__ == "__main__":
	argparser = argparse.ArgumentParser()

	argparser.add_argument("-in", default = os.getcwd(), dest = "in_", help = """
		Input directory from the extracted Unreal Package. It should follow a
		format like CD_<Class>_Skin_<Skin_name>_SF .
	""")
	argparser.add_argument("-out", "-o", default = os.getcwd(), help = """
		Directory to save generated files to.
	""")
	# argparser.add_argument("-noask", default = False, help = """
	# 	On certain uncertanties (overwriting files etc.) do not prompt the user to
	# 	confirm/cancel an operation, always pick the one that resumes execution.
	# """)
	argparser.add_argument("-s", default = 0, action = "count", dest = "silence", help = """
		Shut the script up to varying degrees (-s, -ss, -sss)
	""")
	argparser.add_argument("-debug", default = 0, action = "count", dest = "debug", help = """
		Decreases the logging threshold by 6. Basically counteracts two "-s".
	""")

	if len(sys.argv) == 1:
		argparser.print_help()
		exit()

	args = argparser.parse_args()

	sg = SkinGenerator(in_dir = args.in_, out_dir = args.out, no_ask = None,
			silence = (args.silence - (args.debug * 2)))
	sg.run()
