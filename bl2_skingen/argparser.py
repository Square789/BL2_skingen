"""Provides the get_argparser method, which creates the skingen
argparser responsible for grabbing parameters from the command line.
"""

import argparse
import os

from bl2_skingen.argparse_formatter import SkingenArgparseFormatter
from bl2_skingen.flags import FLAGS

def get_argparser():
	"""Returns an argparser that is tailored to the skingenerator's
	requirements.
	"""
	argparser = argparse.ArgumentParser(formatter_class = SkingenArgparseFormatter)

	argparser.add_argument("-in", default = os.getcwd(), dest = "in_", help = \
		"Input directory from the extracted Unreal Package. It should follow a " \
		"format like CD_<Class>_Skin_<Skin_name>_SF.")
	argparser.add_argument("-out", "-o", default = os.getcwd(), help = \
		"Directory to save generated files to.")
	argparser.add_argument("-outname", default = "skin_{part}_{class_}", dest = "out_fmt", help = \
		"Name of the output file. Will be .format()-ted with the following fed into it:\n"
		"    class_ : Player class the skin is for\n"
		"    skin   : Internal Skin name, taken from the input directory\n"
		"    part   : \"head\" or \"body\"\n"
		"    date   : Date as DDMMYYYY-HHmmSS\n"
		"For example, \"{class_}_{skin}_{part}\" would result in output files being called "
		"\"Siren_BlueB_head.png\".")
	argparser.add_argument("-s", default = 0, action = "count", dest = "silence", help = \
		"Shut the script up to varying degrees (-s, -ss)")
	argparser.add_argument("-decalspec", dest = "decalspec", const = None, help = \
		"A set of positioning and rotation instructions for decals.\n"
		"        PosX[%%] PosY[%%] Rot Scale0[%%] [Scale1[%%]] [Repeat]\n"
		"    Ex.:50      50%%     270 100%%                  y\n"
		"    PosX/Y: Position of the decal texture's central point in pixels.\n"
		"    Rot   : Rotation of the decal around its center point.\n"
		"    Scale : If only Scale0 is defined, factor to scale image by along both axes\n"
		"        If Scale1 is defined, treat Scale0 as X- and Scale1 as Y-axis.\n"
		"    Repeat: Either \"y\" or \"n\". Whether the decal should be repeated along the entire skin.\n"
		"    If a percent sign is set at the allowed positions, the preceding value will be "
		"interpreted relatively to the decal dimensions.\n")
	argparser.add_argument("-noask", action = "append_const", dest = "flag", const = FLAGS.NO_ASK, help = \
		"On certain uncertanties (overwriting files etc.) do not prompt the user to "
		"confirm/cancel an operation, always pick the one that resumes execution.")
	argparser.add_argument("-debug", action = "append_const", dest = "flag", const = FLAGS.DEBUG, help = \
		"Decreases the logging threshold by 6. Basically counteracts two \"-s\".")
	argparser.add_argument("-palette", action = "append_const", dest = "flag", const = FLAGS.DUMP_PALETTE,
		help = "Creates a color palette, for debug purposes.")
	argparser.add_argument("-exc-head", action = "append_const", dest = "flag", const = FLAGS.EXCLUDE_HEAD,
		help = "Do not generate a head texture.")
	argparser.add_argument("-exc-body", action = "append_const", dest = "flag", const = FLAGS.EXCLUDE_BODY,
		help = "Do not generate a body texture.")
	argparser.add_argument("-keep-white", action = "append_const", dest = "flag", const = FLAGS.KEEP_WHITE,
		help = "As a hacky fix, if a color is too white (All channels > 235), its alpha will be set to 0. "
		"The reason for this is that skins such as Krieg's or faces would appear way brighter than "
		"they should be. With this switch, you can turn that behavior off.")

	return argparser
