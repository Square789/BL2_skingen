from distutils.core import setup
from distutils.core import Extension
from Cython.Build import cythonize
import numpy

setup(name="ue_color_diff", include_dirs = [numpy.get_include()], ext_modules = cythonize("ue_color_diff.pyx", language_level="3") )
