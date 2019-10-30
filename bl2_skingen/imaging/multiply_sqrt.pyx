# cython: profile=True

import cython
import numpy as np
cimport numpy as np

np.import_array()

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

cdef np.uint8_t *sq_root = [0, 15, 22, 27, 31, 35, 39, 42, 45, 47, 50, 52, 55, 57, 59, 61, 63, 65, 67, 69, 71, 73, 74, 76,
	78, 79, 81, 82, 84, 85, 87, 88, 90, 91, 93, 94, 95, 97, 98, 99, 100, 102, 103, 104, 105, 107, 108, 109, 110, 111, 112,
	114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137,
	138, 139, 140, 141, 141, 142, 143, 144, 145, 146, 147, 148, 148, 149, 150, 151, 152, 153, 153, 154, 155, 156, 157, 158,
	158, 159, 160, 161, 162, 162, 163, 164, 165, 165, 166, 167, 168, 168, 169, 170, 171, 171, 172, 173, 174, 174, 175, 176,
	177, 177, 178, 179, 179, 180, 181, 182, 182, 183, 184, 184, 185, 186, 186, 187, 188, 188, 189, 190, 190, 191, 192, 192,
	193, 194, 194, 195, 196, 196, 197, 198, 198, 199, 200, 200, 201, 201, 202, 203, 203, 204, 205, 205, 206, 206, 207, 208,
	208, 209, 210, 210, 211, 211, 212, 213, 213, 214, 214, 215, 216, 216, 217, 217, 218, 218, 219, 220, 220, 221, 221, 222,
	222, 223, 224, 224, 225, 225, 226, 226, 227, 228, 228, 229, 229, 230, 230, 231, 231, 232, 233, 233, 234, 234, 235, 235,
	236, 236, 237, 237, 238, 238, 239, 240, 240, 241, 241, 242, 242, 243, 243, 244, 244, 245, 245, 246, 246, 247, 247, 248,
	248, 249, 249, 250, 250, 251, 251, 252, 252, 253, 253, 254, 255]
# Fast, so good enough I guess
# int(sqrt(i / 255.0) * 255))

cdef np.uint8_t scale_int(np.uint8_t a, np.uint8_t b):
	# Multiplies two integers [0x0; 0xFF] as if they were floats. (127, 127) -> 65
	cdef unsigned short product = (a * b) + 0x80
	return ((product >> 8) + product) >> 8

cdef np.uint8_t _min(np.uint8_t a, np.uint8_t b):
	if a > b:
		return b
	else:
		return a

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[DTYPE_t, ndim = 3] multiply(np.ndarray[DTYPE_t, ndim = 3] top_img, np.ndarray[DTYPE_t, ndim = 3] base_img):
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
		raise ValueError("Top Array must specify 4-value arrays as its innermost layser; [RGBA]")

	if base_img.shape[2] != 3:
		raise ValueError("Bottom array must specify 3-value arrays as its innermost layer; [RGB]")

	cdef np.ndarray[DTYPE_t, ndim = 3] res = np.ndarray([top_img.shape[0], top_img.shape[1], 3], dtype = DTYPE)
	cdef int y, x
	cdef int h = top_img.shape[0]
	cdef int w = top_img.shape[1]
	cdef unsigned char rgb
	cdef double tmp
	cdef np.uint8_t tmp_col

	for y in range(h):
		for x in range(w):
			for rgb in range(3):
				tmp_col = sq_root[scale_int(top_img[y, x, rgb], base_img[y, x, rgb])]
				res[y, x, rgb] = (scale_int(top_img[y, x, 3], tmp_col) + scale_int((255 - top_img[y, x, 3]), base_img[y, x, rgb]))

	return res
