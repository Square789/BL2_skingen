import cython
import numpy as np
cimport numpy as np

from shared_funcs cimport scale_int
include "sqrt_arr.pxd"

np.import_array()

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[DTYPE_t, ndim = 3] multiply(
		np.ndarray[DTYPE_t, ndim = 3] top_img,
		np.ndarray[DTYPE_t, ndim = 3] base_img):
	"""Blends top_img with base_img using multiply,
	then takes the square root of the result, returning a numpy array.
	Top image should be supplied as RGBA, base image as RGB.
	"""
	if top_img.ndim != 3 or base_img.ndim != 3:
		raise ValueError("Supplied numpy arrays must be threedimensional!")

	if top_img.shape[0] != base_img.shape[0] or top_img.shape[1] != base_img.shape[1]:
		raise ValueError("Arrays must be of equal size!")

	if top_img.shape[0] == 0 or base_img.shape[1] == 0 or top_img.shape[0] == 0 or base_img.shape[1] == 0:
		raise ValueError("Arrays must not be 0 in width or height!")

	if top_img.shape[2] != 4:
		raise ValueError("Top Array must specify 4-value arrays as its innermost layer; [RGBA]")

	if base_img.shape[2] != 3:
		raise ValueError("Bottom array must specify 3-value arrays as its innermost layer; [RGB]")

	cdef np.ndarray[DTYPE_t, ndim = 3] res = np.ndarray([top_img.shape[0], top_img.shape[1], 3], dtype = DTYPE)
	cdef int y, x
	cdef int h = top_img.shape[0]
	cdef int w = top_img.shape[1]
	cdef unsigned char rgb
	cdef np.uint8_t tmp_col

	for y in range(h):
		for x in range(w):
			for rgb in range(3):
				tmp_col = sq_root[scale_int(top_img[y, x, rgb], base_img[y, x, rgb])]
				res[y, x, rgb] = (
					scale_int(top_img[y, x, 3], tmp_col) +
					scale_int((255 - top_img[y, x, 3]), base_img[y, x, rgb])
				)

	return res
