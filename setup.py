import sys
from setuptools import setup, find_packages, Extension

only_needed = True
if "--build_unneeded" in sys.argv:
	only_needed = False
	sys.argv.remove("--build_unneeded")

from Cython.Build import cythonize
import numpy # Just for get_include()

NEEDED_MODULES = (
	Extension("bl2_skingen.imaging.apply_decal", ["bl2_skingen/imaging/apply_decal.pyx"], extra_compile_args = ["-DMS_WIN64"]),
	Extension("bl2_skingen.imaging.blend_inplace", ["bl2_skingen/imaging/blend_inplace.pyx"], extra_compile_args = ["-DMS_WIN64"]),
	Extension("bl2_skingen.imaging.multiply_sqrt", ["bl2_skingen/imaging/multiply_sqrt.pyx"], extra_compile_args = ["-DMS_WIN64"]),
	Extension("bl2_skingen.imaging.ue_color_diff", ["bl2_skingen/imaging/ue_color_diff.pyx"], extra_compile_args = ["-DMS_WIN64"]),
)

UNUSED_MODULES = (
	Extension("bl2_skingen.imaging.darken", ["bl2_skingen/imaging/darken.pyx"], extra_compile_args = ["-DMS_WIN64"]),
	Extension("bl2_skingen.imaging.overlay", ["bl2_skingen/imaging/overlay.pyx"], extra_compile_args = ["-DMS_WIN64"])
)

to_compile = list(NEEDED_MODULES)
if not only_needed:
	to_compile.extend(UNUSED_MODULES)

with open("README.md", "r") as h:
	l_desc = h.read()

with open("requirements.txt", "r") as h:
	req = h.read().splitlines()

setup(
	name = "BL2_skingen",
	version = "1.4.0",
	description = "Utility to generate png files from Borderlands 2 in-game skin files.",
	long_description = l_desc,
	long_description_content_type = "text/markdown",
	packages = ["bl2_skingen"],
	ext_modules = cythonize(to_compile, language_level = "3"),
	classifiers = [
		"License :: OSI Approved :: MIT License",
		"Natural Language :: English",
		"Operating System :: Microsoft :: Windows",
		"Programming Language :: Cython",
		"Programming Language :: Python",
		"Topic :: Multimedia :: Graphics :: Graphics Conversion",
	],
	install_requires = req,
	include_dirs = [numpy.get_include()],
	entry_points = {
		"console_scripts": [
			"bl2-skingen = bl2_skingen.skingen:main",
		]
	},
	url = "https://www.github.com/Square789/BL2_skingen/",
	zip_safe = False,
)
