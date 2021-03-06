import cython
import numpy as np
cimport numpy as np

from shared_funcs cimport scale_int, calc_alpha

np.import_array()

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[DTYPE_t, ndim = 3] overlay_3D(np.ndarray[DTYPE_t, ndim = 3] top_img, np.ndarray[DTYPE_t, ndim = 3] base_img):
	"""
	Overlays top_img with base_img, returning a numpy array.
	Top image should be supplied as RGBA, base image as RGB.
	"""
	if top_img.ndim != 3 or base_img.ndim != 3:
		raise ValueError("Supplied numpy arrays must be threedimensional!")

	if top_img.shape[0] != base_img.shape[0] or top_img.shape[1] != base_img.shape[1]:
		raise ValueError("Arrays must be of equal size!")

	if top_img.shape[0] == 0 or base_img.shape[1] == 0 or top_img.shape[0] == 0 or base_img.shape[1] == 0:
		raise ValueError("Arrays must not be 0 in width or height!")

	if top_img.shape[2] != 4:
		raise ValueError("Top Array must specify 4-value arrays as its innermost layser; [RGBA]")

	if base_img.shape[2] != 3:
		raise ValueError("Bottom array must specify 3-value arrays as its innermost layer; [RGB]")

	cdef np.ndarray[DTYPE_t, ndim = 3] res = np.ndarray([top_img.shape[0], top_img.shape[1], 3], dtype = DTYPE)
	cdef int y, x
	cdef int h = top_img.shape[0]
	cdef int w = top_img.shape[1]
	cdef unsigned char rgb
	cdef np.uint8_t other_al
	cdef np.uint8_t third_al
	cdef np.uint8_t al
	cdef np.uint8_t tmp_col
	cdef bint debug = False

	for y in range(h):
		for x in range(w):
			for rgb in range(3):
				if base_img[y, x, rgb] < 128:
					tmp_col = 2 * scale_int(base_img[y, x, rgb], top_img[y, x, rgb])
				else:
					tmp_col = 255 - (2 * scale_int( (255 - base_img[y, x, rgb]), (255 - top_img[y, x, rgb])) )
				res[y, x, rgb] = ( scale_int(top_img[y, x, 3], tmp_col) + scale_int((255 - top_img[y, x, 3]), base_img[y, x, rgb]) )
	return res

cpdef np.ndarray[DTYPE_t, ndim = 3] experimental_overlay(np.ndarray[DTYPE_t, ndim = 3] top_img, np.ndarray[DTYPE_t, ndim = 3] base_img):
	"""
	WARNING: THIS ALGORITHM IS NOT IMPLEMENTED 100% CORRECTLY!
	If both images happen to have an alpha value of not 255 at the same position,
	the result ends up not as bright as in some image editing programs.
	"""

	if top_img.ndim != 3 or base_img.ndim != 3:
		raise ValueError("Supplied numpy arrays must be threedimensional!")

	if top_img.shape[0] != base_img.shape[0] or top_img.shape[1] != base_img.shape[1]:
		raise ValueError("Arrays must be of equal size!")

	if top_img.shape[0] == 0 or base_img.shape[1] == 0 or top_img.shape[0] == 0 or base_img.shape[1] == 0:
		raise ValueError("Arrays must not be 0 in width or height!")

	if top_img.shape[2] != 4:
		raise ValueError("Top Array must specify 4-value arrays as its innermost layser; [RGBA]")

	if base_img.shape[2] != 4:
		raise ValueError("Bottom array must specify 4-value arrays as its innermost layer; [RGBA]")

	cdef np.ndarray[DTYPE_t, ndim = 3] res = np.ndarray([top_img.shape[0], top_img.shape[1], 4], dtype = DTYPE)
	cdef int y, x
	cdef int h = top_img.shape[0]
	cdef int w = top_img.shape[1]
	cdef unsigned char rgb
	cdef np.uint8_t other_al
	cdef np.uint8_t third_al
	cdef np.uint8_t al
	cdef np.uint8_t tmp_col
	cdef bint debug = False

	for y in range(h):
		for x in range(w):
			al = calc_alpha(top_img[y, x, 3], base_img[y, x, 3])
			res[y, x, 3] = al

			if al != 0:
				for rgb in range(3):
					if base_img[y, x, rgb] < 128:
						tmp_col = 2 * scale_int(base_img[y, x, rgb], top_img[y, x, rgb])
					else:
						tmp_col = 255 - (2 * scale_int( (255 - base_img[y, x, rgb]), (255 - top_img[y, x, rgb])) )

					res[y, x, rgb] = scale_int(tmp_col, al) + scale_int(base_img[y, x, rgb], (255 - al))
	return res
