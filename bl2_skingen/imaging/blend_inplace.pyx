import cython
import numpy as np
cimport numpy as np

from shared_funcs cimport calc_alpha, scale_int

np.import_array()

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[DTYPE_t, ndim = 3] blend_inplace(np.ndarray[DTYPE_t, ndim = 3] top_img, np.ndarray[DTYPE_t, ndim = 3] base_img):
	"""
	Blends top_img with base_img using regular alpha composition.
	base_img will be modified in the process.
	Both images should be supplied as RGBA.
	"""
	if top_img.ndim != 3 or base_img.ndim != 3:
		raise ValueError("Supplied numpy arrays must be threedimensional!")

	if top_img.shape[0] != base_img.shape[0] or top_img.shape[1] != base_img.shape[1]:
		raise ValueError("Arrays must be of equal size!")

	if top_img.shape[0] == 0 or base_img.shape[1] == 0 or top_img.shape[0] == 0 or base_img.shape[1] == 0:
		raise ValueError("Arrays must not be 0 in width or height!")

	if top_img.shape[2] != 4:
		raise ValueError("Top Array must specify 4-value arrays as its innermost layer; [RGBA]")

	if base_img.shape[2] != 4:
		raise ValueError("Bottom array must specify 3-value arrays as its innermost layer; [RGBA]")

	cdef int height, width, y, x
	cdef np.uint8_t c, alpha

	height = top_img.shape[0]
	width = top_img.shape[1]
	for y in range(height):
		for x in range(width):
			al = calc_alpha(top_img[y, x, 3], base_img[y, x, 3])
			base_img[y, x, 3] = al
			for c in range(3):
				base_img[y, x, c] = scale_int(top_img[y, x, c], top_img[y, x, 3]) + \
					scale_int(base_img[y, x, c], 255 - top_img[y, x, 3])
