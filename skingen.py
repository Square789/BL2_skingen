#!/usr/bin/env python3
# Borderlands 2 Skin generator, (c) 2019 - 2020 Square789
if __name__ != "__main__":
	raise RuntimeError("Please run this script directly.")
# pylint: disable=import-error, no-name-in-module

import sys
import os
import time
import re
from pathlib import Path
import logging
from pprint import pprint
import argparse
import datetime
from math import log2

import numpy # gotta get that sweet C array
from PIL import Image, ImageFilter, ImageDraw

from bl2_skingen.unreal_notation import Parser as UParser
from bl2_skingen.unreal_notation import UnrealNotationParseError
from bl2_skingen.log_formatter import SkingenLogFormatter
from bl2_skingen.argparser import get_argparser
from bl2_skingen.decalspec import parse_decalspec, validate_decalspec
from bl2_skingen.flags import FLAGS
from bl2_skingen.imaging.apply_decal import apply_decal
from bl2_skingen.imaging.multiply_sqrt import multiply
from bl2_skingen.imaging.blend_inplace import blend_inplace
from bl2_skingen.imaging.ue_color_diff import ue_color_diff

__author__ = "Square789"
__version__ = "1.2.0"

BAD_PATH_CHARS = (os.path.sep, "\\", "/", "..", ":", "*", ">", "<", "|")

# Flex tape the PIL.Image module's logger
logging.getLogger("PIL.Image").setLevel(60)

# Set up own logger
SKINGEN_LOGGER = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler(sys.stdout)
fmtr = SkingenLogFormatter("{levelname:9}| {funcName:20}: {message}", None, "{")
log_hdlr.setFormatter(fmtr)
SKINGEN_LOGGER.addHandler(log_hdlr)

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

	def __init__(self, logger, in_dir, out_dir, out_fmt, silence, flag, decalspec = None):
		"""logger: Logger to be used by the skingenerator.
		in_dir: Input directory to be read from.
		out_dir: Directory result files should be written to.
		out_fmt: Format string to name the output files after.
		silence: Integer to change the logger's sensitivity.
		flag: Flagnumber.
		decalspec: None or an acceptable decalspec String.
		"""
		self.in_dir = Path(in_dir)
		self.out_dir = Path(out_dir)
		self.in_dir = self.in_dir.absolute()
		self.out_dir = self.out_dir.absolute()
		self.flag = flag
		self.out_fmt = out_fmt
		self.decalspec = decalspec

		self.logger = logger
		if silence > 3: silence = 3
		self.logger.setLevel(21 + (silence * 3))

		for i in CLASSES:
			if i in self.in_dir.stem:
				self.class_ = i
				break
		else:
			self.logger.log(50, f"Unable to find class in path name: {self.in_dir.stem}")
			sys.exit()
		try:
			tmp = self.in_dir.stem.split("_")
			self.skin_name = tmp[3]
			self.skin_type = tmp[2]
		except IndexError:
			self.logger.log(50, "Path not conforming to expected format.")
			sys.exit()

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
		if not (self.flag & FLAGS.EXCLUDE_BODY):
			self.logger.log(25, f"===Generating body file===")
			self._generate_image(self.body)
		if not (self.flag & FLAGS.EXCLUDE_HEAD):
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

	def dump_color_palette(self, col_arr) -> Image.Image:
		"""
		! Debug method !
		Generates a palette img from a colorarray and returns it.
		"""
		color_names = ("A", "B", "C")
		shm_names = ("shadow", "midtone", "hilight")
		palette_img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
		y_offset = 0
		x_offset = 0
		cname_i = 0
		sname_i = 0
		draw_agent = ImageDraw.ImageDraw(palette_img)
		for color in col_arr:
			for shm in color:
				draw_agent.rectangle(
					(x_offset * 64 + 16 * (x_offset + 1), y_offset * 64 + 16 * (y_offset + 1),
					((x_offset + 1) * 64) + 16 * x_offset, (y_offset + 1) * 64 + 16* y_offset),
					fill = tuple([int(round(i)) for i in (shm[0], shm[1], shm[2], shm[3])])
				)
				draw_agent.text(
					(x_offset * 64 + 16 * (x_offset + 1), y_offset * 64 + 16 * (y_offset + 1) + 64),
					f"{color_names[cname_i]} {shm_names[sname_i]}",
					fill = (0, 0, 0, 255)
				)
				x_offset += 1
				sname_i += 1
			x_offset = 0
			sname_i = 0
			y_offset += 1
			cname_i += 1
		return palette_img

	def _locate_props_files(self):
		"""Seeks and confirms existence of the props files."""
		for part in (self.body, self.head):
			tmp_pat = Path(self.in_dir, PROPSFILE.format(self.skin_name, part.cap))
			if not tmp_pat.exists():
				self.logger.log(50, f"COULD NOT FIND {tmp_pat}!")
				sys.exit()
			setattr(part, "props", tmp_pat)

			self.logger.log(20, f"\tFound {tmp_pat.name}")

	def _parse_props_files(self):
		"""Assumes both self.body and self.head contain links to the
		props files, parses those and stores information as a dict in
		the part's props_dict attribute.
		"""
		for part in (self.body, self.head):
			with open(part.props, "r") as h:
				u_prsr = UParser(h.read())
			try:
				res = u_prsr.parse()
			except UnrealNotationParseError:
				self.logger.log(50, f"Error parsing Unreal Notation file")
				sys.exit()
			part.props_dict = res

	def _get_textures(self):
		"""Reads textures from self.body.props_dict and
		self.head.props_dics, then checks whether they exist (as tga).
		If they do, stores them in the respective objects.
		"""
		for part in (self.body, self.head):
			for param_dict in part.props_dict["TextureParameterValues"]:
				if param_dict["ParameterName"] not in MAP_TEX_PARAM_NAME_TO_PART_ATTR:
					continue
				attr = MAP_TEX_PARAM_NAME_TO_PART_ATTR[param_dict["ParameterName"]]

				ue_tex_name = RE_TEXTURE_UE_INTERNAL_PATH.search(param_dict["ParameterValue"])
				if not ue_tex_name:
					self.logger.log(50, "Could not apply regex to get texture file.")
					sys.exit()
				ue_tex_name = ue_tex_name[1]
				ue_tex_name = ue_tex_name.split(UE_TEX_SEP)[-1]
				tmp_pat = Path(self.in_dir, TEXTURE_FILE.format(ue_tex_name))
				if not tmp_pat.exists():
					self.logger.log(50, f"Unable to find texture file {tmp_pat}!")
				setattr(part, attr, tmp_pat)
				self.logger.log(20, f"\t{attr} {part.cap}: {tmp_pat.name}")

	def _fetch_colors(self, part):
		"""Reads the part's props_dict and return a three-dimensional
		numpy array, where:
		[0]: A, [1]: B, [2]: C
		[x][0]: "shadow", [x][1]: "mid", [x][2]: "hilight"
		[x][y][0]: R, [x][y][1]: G, [x][y][2]: B, [x][y][3]: A
		"""
		colors = numpy.ndarray((3, 3, 4), dtype = numpy.uint8)
		colors[:] = 255 # Sometimes colors are not specified, set them to full then

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
				if not (self.flag & FLAGS.KEEP_WHITE):
					if nrm_colors[0] > 235 and nrm_colors[1] > 235 and nrm_colors[2] > 235:
						nrm_colors[3] = 0 # Wonky; so far all white has been overlayed with
						# skin, turning it brighter than it should be. This may cause problems
						# with skins such as Zer0's "Whiteout" however.
				colors[MAP_COLOR_TO_IDX[color_name_match[1]]] \
					[MAP_NAME_TO_IDX[color_name_match[2].lower()]] = \
					nrm_colors
		return colors

	def _get_decal(self, part):
		"""
		Searches through a part's props_dict and looks for a element called
		p_Decal. If it is encountered, reads the value of that element, resolves
		it to a path based on in_dir and the UEViewer image extraction scheme,
		checks whether the path exists and finally returns it as a Path object.
		If the decal or the image do not exist, None is returned.
		"""
		decalimg = None
		for i, j in enumerate(part.props_dict["TextureParameterValues"]):
			curtexparam = part.props_dict["TextureParameterValues"][i]
			if curtexparam["ParameterName"] == "p_Decal":
				tmp = RE_TEXTURE_UE_INTERNAL_PATH.search(curtexparam["ParameterValue"])
				if tmp is None:
					self.logger.log(30, "Error while locating decal. Key found, but could not"
						" determine image path.")
					break
				decalimg = Path(self.in_dir, TEXTURE_FILE.format(tmp[1].split(UE_TEX_SEP)[-1]))
				if not decalimg.exists():
					self.logger.log(30, "Decal image does not exist.")
					return None
				break
		return decalimg

	def _stamp_decal(self, overlay_arr, hard_mask_arr, decalpath, decalspec):
		"""
		Applies decal to `overlay_arr`

		overlay_arr : numpy.ndarray[np.uint8, ndin = 3] | Numpy array
			containing the overlay image generated so far.
		hard_mask_arr : numpy.ndarray[np.uint8, ndim = 3] | Numpy array
			containing the hard mask used to format decal.
		decalpath : str;pathlib.Path | Full path to the decal image.
		decalspec : bl2_skingen.decalspec.Decalspec | Decalspec
			containing absolute values.
		"""
		decal_image = Image.open(decalpath)
		processed_decal_arr = \
			apply_decal(
				decal_image,
				hard_mask_arr,
				decalspec.posx, decalspec.posy)
		blend_inplace(processed_decal_arr, overlay_arr)
		Image.fromarray(overlay_arr).show()
		#raise NotImplementedError()

	def _generate_image(self, part):
		self.logger.log(20, f"Opening {part.dif}")
		dif_img = Image.open(part.dif)
		difx, dify = dif_img.size

		self.logger.log(20, f"Opening {part.msk} and expanding")
		msk_img = Image.open(part.msk)
		if not self.is_perfect_square(msk_img):
			self.logger.log(50, "Image has bad constraints.")
			sys.exit()

		m_x, m_y = msk_img.size
		if m_x != difx or m_y != dify:
			self.logger.log(50, "Well this shouldn't happen but the dif and mask images are of"
				" different sizes.")
			sys.exit()

		soft_mask = msk_img.resize((difx, dify), box = (0.0, 0.0, difx/2, float(dify)))
		hard_mask = msk_img.resize((difx, dify), box = (difx/2, 0.0, float(difx), float(dify)))

		self.logger.log(20, f"Reading and converting color information...")
		colors = self._fetch_colors(part)

		######DEBUG BLOCK
		self.logger.log(19, f"Color infs:\n{colors}")
		if self.flag & FLAGS.DUMP_PALETTE:
			p = self.dump_color_palette(colors)
			self._save_image(p, Bodypart("palette"))
		######

		self.logger.log(25, f"Generating overlay image...")
		hard_mask_arr = numpy.array(hard_mask)
		soft_mask_arr = numpy.array(soft_mask)
		overlay_arr = ue_color_diff(hard_mask_arr, soft_mask_arr, colors)

		self.logger.log(25, f"Seeking decal...")
		decalpath = self._get_decal(part)
		if decalpath is not None:
			self.logger.log(20, f"Decal found: {decalpath}")
			if self.decalspec is None:
				self.logger.log(25, "Decal found, but no decalspec supplied; skipping.")
			else:
				self.logger.log(25, "Applying decal...")
				self._stamp_decal(
					overlay_arr,
					hard_mask_arr,
					decalpath,
					parse_decalspec(self.decalspec, difx, dify),)
	
		else:
			self.logger.log(25, f"No decal found.")

		self.logger.log(25, f"Merging overlay and base image...")
		dif_img_arr = numpy.array(dif_img)
		final_arr = multiply(overlay_arr, dif_img_arr)
		self._save_image(Image.fromarray(final_arr), part)

	def _save_image(self, img, part):
		"""
		Choose a target path based on class variables, the current bodypart,
		which has to be supplied and save the image.
		Asks user whether they want to overwrite an existing file or create
		non-existing directories.
		"""
		f_stub = self.out_fmt.format(class_ = self.class_, skin = self.skin_name,
				part = part.lwr, date = datetime.datetime.now().strftime("%d%m%Y-%H%M%S"))
		targetpath = Path(self.out_dir, (f_stub + ".png"))
		if not self.out_dir.exists():
			if not (self.flag & FLAGS.NO_ASK):
				while True:
					self.logger.log(30, "Target directory does not seem to exist.")
					userchoice = input("Create it? (Y/N) > ").lower()
					if userchoice != "n" and userchoice != "y":
						continue
					if userchoice == "n":
						return
					if userchoice == "y":
						break
			os.makedirs(self.out_dir)
		self.logger.log(25, f"Saving generated texture to {targetpath}")
		if targetpath.exists() and (not (self.flag & FLAGS.NO_ASK)):
			self.logger.log(30, f"File {targetpath} already exists!")
			while True:
				userchoice = input("Overwrite it? (Y/N) > ").lower()
				if userchoice != "n" and userchoice != "y":
					continue
				if userchoice == "n":
					return
				elif userchoice == "y":
					break
				else:
					self.logger.log(50, "What"); sys.exit()
		img.save(targetpath, format = "PNG")

if __name__ == "__main__":
	argparser = get_argparser()

	if len(sys.argv) == 1:
		argparser.print_help()
		sys.exit()

	args = argparser.parse_args()
	# Prevent directory traversal.
	for pathsep in BAD_PATH_CHARS:
		if pathsep in args.out_fmt:
			SKINGEN_LOGGER.log(50, "Illegal characters in output file format! "
				"Remove all occurrences of " + BAD_PATH_CHARS)
			sys.exit()
	try: # Test the outformat.
		args.out_fmt.format(class_ = "test", skin = "test", part = "test", date = "test")
	except (IndexError, KeyError, ValueError):
		SKINGEN_LOGGER.log(50, "Invalid format string for output!")
		sys.exit()

	# Calculate the flagnumber
	flag = 0
	if args.flag is not None:
		for i in args.flag:
			flag |= i

	# TODO decalscribbles: Take the square root of the decals colors
	if args.decalspec is not None:
		if not validate_decalspec(args.decalspec):
			SKINGEN_LOGGER.log(30, "Bad decalspec, will ignore decal for this run.")
			setattr(args, "decalspec", None)

	sg = SkinGenerator(in_dir = args.in_, out_dir = args.out, out_fmt = args.out_fmt,
			silence = (args.silence - (((flag & FLAGS.DEBUG) // FLAGS.DEBUG) * 2)), flag = flag,
			logger = SKINGEN_LOGGER, decalspec = args.decalspec)

	sg.run()
