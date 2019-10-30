import cython
import numpy as np
cimport numpy as np

np.import_array()

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

cdef np.uint8_t scale_int(np.uint8_t a, np.uint8_t b):
	# Multiplies two integers [0x0; 0xFF] as if they were floats. (127, 127) -> 65
	cdef unsigned short product = (a * b) + 0x80
	return ((product >> 8) + product) >> 8

cdef np.uint8_t calc_alpha(np.uint8_t a, np.uint8_t b):
	return scale_int(a, (255 - b)) + b

cdef np.uint8_t col_median(np.uint8_t a, np.uint8_t b, np.uint8_t percentage):
	# Returns median value between input values; if percentage is 0, return a, if percentage is 255 return b
	return scale_int(a, (255 - percentage)) + scale_int(b, percentage)

cdef np.uint8_t swoop(np.uint8_t a, np.uint8_t b):
	# Fancy mathematics, possibly optimizable just a bit more.
	if a == 0 and b == 0:
		return 127
	if a >= b:
		return 127+int((1-(b/a))*128)
	else:
		return 127-int((1-(a/b))*127)

cpdef ue_color_diff(np.ndarray[DTYPE_t, ndim = 3] hard_mask, np.ndarray[DTYPE_t, ndim = 3] soft_mask, np.ndarray[DTYPE_t, ndim = 3] colors):
	# [0]: A, [1]: B, [2]: C
	# [x][0]: "shadow", [x][1]: "mid", [x][2]: "hilight"
	# [x][y][0]: R, [x][y][1]: G, [x][y][2]: B, [x][y][3]: A
	if hard_mask.ndim != 3 or soft_mask.ndim != 3:
		raise ValueError("Masks must be supplied as three dimensional arrays.")

	if hard_mask.shape[0] == 0 or hard_mask.shape[1] == 0 or soft_mask.shape[0] == 0 or soft_mask.shape[1] == 0:
		raise ValueError("Mask array must not be 0 in width or height!")

	if hard_mask.shape[2] != 3 or soft_mask.shape[2] != 3:
		raise ValueError("Mask image arrays must specify 3-value arrays as their innermost layer; [R, G, B]")

	if hard_mask.shape[0] != soft_mask.shape[0] or hard_mask.shape[1] != soft_mask.shape[1]:
		raise ValueError("Mask images must perfectly overlap eachother (so have the same size)")

	cdef np.ndarray[DTYPE_t, ndim = 3] res = np.ndarray([hard_mask.shape[0], hard_mask.shape[1], 4], dtype = DTYPE)

	cdef np.uint8_t rgb # channel iterator variable
	cdef np.uint8_t ccol # current color
	cdef np.uint8_t c0 # calculation storage
	cdef np.uint8_t c1 # calculation storage
	cdef np.uint8_t dif # mixing multiplier

	cdef int w = res.shape[1]
	cdef int h = res.shape[0] # y

	for y in range(h):
		for x in range(w):
			res[y, x, 3] = 0xFF
			#if hard_mask[y, x, 0] > hard_mask[y, x, 1] and hard_mask[y, x, 0] > hard_mask[y, x, 2]:   # A
			#	ccol = 0
			#elif hard_mask[y, x, 1] > hard_mask[y, x, 0] and hard_mask[y, x, 1] > hard_mask[y, x, 2]: # B
			#	ccol = 1
			#elif hard_mask[y, x, 2] > hard_mask[y, x, 0] and hard_mask[y, x, 2] > hard_mask[y, x, 1]: # C
			#	ccol = 2
			if hard_mask[y, x, 0] > 230:
				ccol = 0
			elif hard_mask[y, x, 1] > 230:
				ccol = 1
			elif hard_mask[y, x, 2] > 230:
				ccol = 2
			else:
				res[y, x, 3] = 0x00
				continue
			dif = swoop(soft_mask[y, x, 0], soft_mask[y, x, 1])
			for rgb in range(3):
				c0 = col_median(colors[ccol, 1, rgb], colors[ccol, 0, rgb], soft_mask[y, x, 1])
				c1 = col_median(colors[ccol, 1, rgb], colors[ccol, 2, rgb], soft_mask[y, x, 0])
				res[y, x, rgb] = col_median(c0, c1, dif)

	return res
