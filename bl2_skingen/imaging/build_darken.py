from distutils.core import setup
from distutils.core import Extension
from Cython.Build import cythonize
import numpy

setup(name="darken", include_dirs = [numpy.get_include()], ext_modules = cythonize("darken.pyx", language_level = "3") )
