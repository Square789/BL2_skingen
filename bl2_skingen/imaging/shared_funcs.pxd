"""
Serves as a host for scale_int and calc_alpha
"""
import cython
import numpy as np
cimport numpy as np

np.import_array()

#DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

cdef inline np.uint8_t scale_int(np.uint8_t a, np.uint8_t b):
	# Multiplies two integers [0x0; 0xFF] as if they were floats. (127, 127) -> 65
	cdef unsigned short product = (a * b) + 0x80
	return ((product >> 8) + product) >> 8

cdef inline np.uint8_t calc_alpha(np.uint8_t a, np.uint8_t b):
	return scale_int(a, (255 - b)) + b
