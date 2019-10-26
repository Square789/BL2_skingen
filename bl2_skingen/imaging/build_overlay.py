from distutils.core import setup
from distutils.core import Extension
from Cython.Build import cythonize
import numpy

setup(name="overlay", include_dirs = [numpy.get_include()], ext_modules = cythonize("overlay.pyx", language_level = "3") )
