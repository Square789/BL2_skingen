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
from bl2_skingen.props import unify_props
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

DEF_DECAL_AREA = numpy.array([255, 255, 255], dtype = numpy.uint8)
DEF_DECAL_COL = numpy.array([0, 0, 0, 255], dtype = numpy.uint8)
DEF_DECALSPEC = {
	"Assassin":  {"head": "0 0 0 1", "body": "0 0 0 1"},
	"Mechro":    {"head": "0 0 0 1", "body": "0 0 0 1"},
	"Mercenary": {"head": "0 0 0 1", "body": "0 0 0 1"},
	"Soldier":   {"head": "0 0 0 1", "body": "0 0 0 1"},
	"Siren":     {"head": "0 0 0 1", "body": "0 0 0 1"},
	"Psycho":    {"head": "0 0 0 1", "body": "211 785 0 0.6953125"},
}

logging.getLogger().setLevel(0) # this magically works, whoop-de-doo

class Bodypart():
	"""
	Small namespace for different files of Head/Body.
	Name will be retrievable by t-he properties cap, lwr and upr.
	"""
	props = None
	unif_props = None
	colors = None
	decal_area = None
	decal_color = None
	decalspec = None
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
		"""
		Assumes both self.body and self.head contain links to the
		props files, parses those and stores information as a UnifiedProps
		instance in the part's unif_props attribute.
		"""
		for part in (self.body, self.head):
			with open(part.props, "r") as h:
				u_prsr = UParser(h.read())
			try:
				res = u_prsr.parse()
			except UnrealNotationParseError as exc:
				self.logger.log(50, f"Error parsing Unreal Notation file: {exc}")
				sys.exit()
			try:
				res = unify_props(res)
			except Exception as exc:
				self.logger.log(50, f"Unexpected error while parsing {part.props}")
				sys.exit()
			part.unif_props = res

	def _get_textures(self):
		"""Reads textures from self.body.unif_props and
		self.head.unif_props, then checks whether they exist (as tga).
		If they do, stores them in the respective objects.
		"""
		for part in (self.body, self.head):
			for param_node in part.unif_props.TexturePV:
				if param_node.name not in MAP_TEX_PARAM_NAME_TO_PART_ATTR:
					continue
				attr = MAP_TEX_PARAM_NAME_TO_PART_ATTR[param_node.name]

				ue_tex_name = RE_TEXTURE_UE_INTERNAL_PATH.search(param_node.value)
				if not ue_tex_name:
					self.logger.log(50, f"Could not apply regex to get texture file: "
						"{param_node.value}")
					sys.exit()
				ue_tex_name = ue_tex_name[1]
				ue_tex_name = ue_tex_name.split(UE_TEX_SEP)[-1]
				tmp_pat = Path(self.in_dir, TEXTURE_FILE.format(ue_tex_name))
				if not tmp_pat.exists():
					self.logger.log(50, f"Unable to find texture file {tmp_pat}!")
					sys.exit()
				setattr(part, attr, tmp_pat)
				self.logger.log(19, f"\t{attr} {part.cap}: {tmp_pat.name}")

	def _fill_part_attrs(self, part):
		"""
		Reads the part's unif_props and:
		- Place all findable colors into the part's `colors` attribute
		as a numpy array, where:
			[0]: A, [1]: B, [2]: C
			[x][0]: "shadow", [x][1]: "mid", [x][2]: "hilight"
			[x][y][0]: R, [x][y][1]: G, [x][y][2]: B, [x][y][3]: A
		- If decal colors can be found, set `decal_color` to a 4-value numpy array.
			If they can not be found, fallback decal color will be used.
		- If decal area specifications can be found, they will be placed into
			`decal_area` as a 3-value numpy array.
		If a global decalspec has been supplied, set the part's `decalspec`
			attribute to it. Else, fill it from the default decalspecs.
		"""
		colors = numpy.ndarray((3, 3, 4), dtype = numpy.uint8)
		colors[:] = 255 # Sometimes colors are not specified, set them to full then
		decal_color = DEF_DECAL_COL.copy()
		decal_area = DEF_DECAL_AREA.copy()

		for node in part.unif_props.VectorPV:
			if node.name == "p_DecalColor":
				decal_color = DEF_DECAL_COL.copy()
				mul = 1
				for v in node.value.values():
					v = float(v.strip()) * mul
					if v > 1:
						mul = 1 / val
				for j, k in node.value.items():
					decal_color[MAP_CHNL_TO_IDX[j]] = round(float(k.strip()) * 255 * mul)
			if node.name == "p_DecalChannelScale":
				for k, v in node.value.items():
					if not k in MAP_CHNL_TO_IDX:
						continue
					if k == "A": # Doesn't support alpha
						continue
					decal_area[MAP_CHNL_TO_IDX[k]] = round(float(v.strip()) * 255)
			color_name_match = RE_DEFINES_CHNL_COL.match(node.name)
			if color_name_match:
				nrm_colors = [0, 0, 0, 0]
				mul = 1
				for val in node.value.values():
					val = float(val.strip()) * mul
					if val > 1:
						mul = 1 / val
				for chnl, val in node.value.items():
					nrm_colors[MAP_CHNL_TO_IDX[chnl]] = \
						round(float(val.strip()) * 255 * mul)
				if not (self.flag & FLAGS.KEEP_WHITE):
					if nrm_colors[0] > 235 and nrm_colors[1] > 235 and nrm_colors[2] > 235:
						nrm_colors[3] = 0 # Wonky; so far all white has been overlayed with
						# skin, turning it brighter than it should be. This may cause problems
						# with skins such as Zer0's "Whiteout" however.
				colors[MAP_COLOR_TO_IDX[color_name_match[1]]] \
					[MAP_NAME_TO_IDX[color_name_match[2].lower()]] = \
					nrm_colors
		if self.decalspec is not None:
			setattr(part, "decalspec", self.decalspec)
		else:
			setattr(part, "decalspec", DEF_DECALSPEC[self.class_][part.lwr])
		setattr(part, "decal_color", decal_color)
		setattr(part, "decal_area", decal_area)
		setattr(part, "colors", colors)

	def _get_decal(self, part):
		"""
		Searches through a part's unif_props and looks for a element called
		p_Decal. If it is encountered, reads the value of that element, resolves
		it to a path based on in_dir and the UEViewer image extraction scheme,
		checks whether the path exists and finally returns it as a Path object.
		If the decal or the image do not exist, None is returned.
		"""
		decalimg = None
		for i, node in enumerate(part.unif_props.TexturePV):
			if node.name == "p_Decal":
				if node.value in ("", "None"):
					self.logger.log(25, "Part has no decal associated with it.")
				tmp = RE_TEXTURE_UE_INTERNAL_PATH.search(node.value)
				if tmp is None:
					self.logger.log(30, "Error while locating decal. Key found, but could not"
						" determine image path.")
					break
				decalimg = Path(self.in_dir, TEXTURE_FILE.format(tmp[1].split(UE_TEX_SEP)[-1]))
				if not decalimg.exists():
					self.logger.log(30, "Decal image not found on disk.")
					return None
				break
		else: #No key "p_Decal" was encountered
			self.logger.log(25, "Part has no decal associated with it.")
		return decalimg

	def _stamp_decal(self, overlay_arr, hard_mask_arr, decal_color,
			decal_area, decalpath, decalspec):
		"""
		Applies decal to `overlay_arr` in-place.

		overlay_arr : numpy.ndarray[np.uint8, ndin = 3] | Numpy array
			containing the overlay image generated so far.
		hard_mask_arr : numpy.ndarray[np.uint8, ndim = 3] | Numpy array
			containing the hard mask used to format decal.
		decalpath : str;pathlib.Path | Path to the decal image.
		decalspec : bl2_skingen.decalspec.Decalspec | Decalspec
			containing absolute pos transform values.
		decal_color : numpy.ndarray[np.uint8, ndim = 1] | Numpy array containing
			the coloring information for the decal in 4 ints, [R, G, B, A]
		decal_area : numpy.ndarray[np.uint8, ndim = 1] | Numpy array containing
			the decal area in 3 values.
		"""
		decal_image = Image.open(decalpath)
		processed_decal_arr = \
			apply_decal(
				decal_image,
				hard_mask_arr,
				decal_color,
				decal_area,
				decalspec.posx, decalspec.posy,
				decalspec.rot,
				decalspec.scalex, decalspec.scaley)
		blend_inplace(processed_decal_arr, overlay_arr)
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

		self.logger.log(20, f"Reading and converting part information...")
		self._fill_part_attrs(part)
		self.logger.log(19, f"Part colors:\n{part.colors}")
		self.logger.log(19, f"Decal colors: {part.decal_color}")
		self.logger.log(19, f"Decal area: {part.decal_area}")
		self.logger.log(19, f"Decalspec: {part.decalspec.__repr__()}")

		######DEBUG BLOCK
		if self.flag & FLAGS.DUMP_PALETTE:
			p = self.dump_color_palette(part.colors)
			self._save_image(p, Bodypart("palette"))
		######

		self.logger.log(25, f"Generating overlay image...")
		hard_mask_arr = numpy.array(hard_mask)
		soft_mask_arr = numpy.array(soft_mask)
		overlay_arr = ue_color_diff(hard_mask_arr, soft_mask_arr, part.colors)

		if not (self.flag & FLAGS.NO_DECAL):
			self.logger.log(25, f"Seeking decal...")
			decalpath = self._get_decal(part)
			if decalpath is not None:
				self.logger.log(20, f"Decal found: {decalpath}")
				self.logger.log(25, "Applying decal...")
				self._stamp_decal(
					overlay_arr,
					hard_mask_arr,
					part.decal_color,
					part.decal_area,
					decalpath,
					parse_decalspec(
						part.decalspec,
						difx, dify)
				)
			else:
				self.logger.log(25, "No decal found.")

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
