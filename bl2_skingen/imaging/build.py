"""
Build script.
"""

import sys
only_needed = False
if "--build_needed_only" in sys.argv:
	only_needed = True
	sys.argv.remove("--build_needed_only")

from distutils.core import setup
from distutils.core import Extension
from Cython.Build import cythonize
from numpy import get_include

NEEDED_MODULES = (
	"apply_decal.pyx",
	"blend_inplace.pyx",
	"multiply_sqrt.pyx",
	"ue_color_diff.pyx",
)

UNUSED_MODULES = (
	"darken.pyx",
	"overlay.pyx"
)

to_compile = list(NEEDED_MODULES)
if not only_needed:
	to_compile.extend(UNUSED_MODULES)

setup(
	name = "BL2_skingen python imaging modules.",
	include_dirs = [get_include()],
	ext_modules = cythonize(
		to_compile,
		language_level = "3",
	)
)
