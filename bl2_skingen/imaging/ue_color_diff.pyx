import cython
import numpy as np
cimport numpy as np

from libc.math cimport abs

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

@cython.boundscheck(False)
@cython.wraparound(False)
cdef ue_color_diff_body(dict col_dict, np.ndarray[DTYPE_t, ndim = 3] res,
		np.ndarray[DTYPE_t, ndim = 3] h_msk, np.ndarray[DTYPE_t, ndim = 3] s_msk):
	# if res, hard_mask and soft_mask are not same size here, then idk man reevaluate the universe you live in.
	cdef int w, h, y, x
	cdef int AmidR = col_dict["A"]["midtone"]["R"]
	cdef int AmidG = col_dict["A"]["midtone"]["G"]
	cdef int AmidB = col_dict["A"]["midtone"]["B"]
	cdef int AshdR = col_dict["A"]["shadow"]["R"]
	cdef int AshdG = col_dict["A"]["shadow"]["G"]
	cdef int AshdB = col_dict["A"]["shadow"]["B"]
	cdef int AhilR = col_dict["A"]["hilight"]["R"]
	cdef int AhilG = col_dict["A"]["hilight"]["G"]
	cdef int AhilB = col_dict["A"]["hilight"]["B"]
	cdef int BmidR = col_dict["B"]["midtone"]["R"]
	cdef int BmidG = col_dict["B"]["midtone"]["G"]
	cdef int BmidB = col_dict["B"]["midtone"]["B"]
	cdef int BshdR = col_dict["B"]["shadow"]["R"]
	cdef int BshdG = col_dict["B"]["shadow"]["G"]
	cdef int BshdB = col_dict["B"]["shadow"]["B"]
	cdef int BhilR = col_dict["B"]["hilight"]["R"]
	cdef int BhilG = col_dict["B"]["hilight"]["G"]
	cdef int BhilB = col_dict["B"]["hilight"]["B"]
	cdef int CmidR = col_dict["C"]["midtone"]["R"]
	cdef int CmidG = col_dict["C"]["midtone"]["G"]
	cdef int CmidB = col_dict["C"]["midtone"]["B"]
	cdef int CshdR = col_dict["C"]["shadow"]["R"]
	cdef int CshdG = col_dict["C"]["shadow"]["G"]
	cdef int CshdB = col_dict["C"]["shadow"]["B"]
	cdef int ChilR = col_dict["C"]["hilight"]["R"]
	cdef int ChilG = col_dict["C"]["hilight"]["G"]
	cdef int ChilB = col_dict["C"]["hilight"]["B"] # :yes:

	w = res.shape[1]
	h = res.shape[0] # y

	for y in range(h):
		for x in range(w):
			res[y, x, 3] = 0xFE

			# print(type(h_msk[y, x]))
			if h_msk[y, x, 0] == 255 and h_msk[y, x, 1] == 0 and h_msk[y, x, 2] == 0:   # A
				#res[y, x, 0] = 255
				res[y, x, 0] = int(int(AmidR + (abs(AmidR - AshdR) * (s_msk[y, x, 1] / 255)) ) + (abs(AmidR - AhilR) * (s_msk[y, x, 0] / 255)) )//2
				res[y, x, 1] = int(int(AmidG + (abs(AmidG - AshdG) * (s_msk[y, x, 1] / 255)) ) + (abs(AmidG - AhilG) * (s_msk[y, x, 0] / 255)) )//2
				res[y, x, 2] = int(int(AmidB + (abs(AmidB - AshdB) * (s_msk[y, x, 1] / 255)) ) + (abs(AmidB - AhilB) * (s_msk[y, x, 0] / 255)) )//2 # Just shadow for now
			elif h_msk[y, x, 0] == 0 and h_msk[y, x, 1] == 255 and h_msk[y, x, 2] == 0: # B
				#res[y, x, 1] = 255
				res[y, x, 0] = int(int(BmidR + (abs(BmidR - BshdR) * (s_msk[y, x, 1] / 255)) ) + (abs(BmidR - BhilR) * (s_msk[y, x, 0] / 255)) )
				res[y, x, 1] = int(int(BmidG + (abs(BmidG - BshdG) * (s_msk[y, x, 1] / 255)) ) + (abs(BmidG - BhilG) * (s_msk[y, x, 0] / 255)) )
				res[y, x, 2] = int(int(BmidB + (abs(BmidB - BshdB) * (s_msk[y, x, 1] / 255)) ) + (abs(BmidB - BhilB) * (s_msk[y, x, 0] / 255)) ) # Just shadow for now
			elif h_msk[y, x, 0] == 0 and h_msk[y, x, 1] == 0 and h_msk[y, x, 2] == 255: # C
				#res[y, x, 2] = 255
				res[y, x, 0] = int(int(CmidR + (abs(CmidR - CshdR) * (s_msk[y, x, 1] / 255)) ) + (abs(CmidR - ChilR) * (s_msk[y, x, 0] / 255)) )
				res[y, x, 1] = int(int(CmidG + (abs(CmidG - CshdG) * (s_msk[y, x, 1] / 255)) ) + (abs(CmidG - ChilG) * (s_msk[y, x, 0] / 255)) )
				res[y, x, 2] = int(int(CmidB + (abs(CmidB - CshdB) * (s_msk[y, x, 1] / 255)) ) + (abs(CmidB - ChilB) * (s_msk[y, x, 0] / 255)) ) # Just shadow for now
			else:
				pass
			 	#print("other")

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
			#if hard_mask[y, x, 0] == 255 and hard_mask[y, x, 1] == 0 and hard_mask[y, x, 2] == 0:   # A
			#	res[y, x, 0] = col_median(colors[0, 1, 0], colors[0, 0, 0], soft_mask[y, x, 1])
			#	res[y, x, 1] = col_median(colors[0, 1, 1], colors[0, 0, 1], soft_mask[y, x, 1])
			#	res[y, x, 2] = col_median(colors[0, 1, 2], colors[0, 0, 2], soft_mask[y, x, 1])
			#elif hard_mask[y, x, 0] == 0 and hard_mask[y, x, 1] == 255 and hard_mask[y, x, 2] == 0: # B
			#	res[y, x, 0] = col_median(colors[1, 1, 0], colors[1, 0, 0], soft_mask[y, x, 1])
			#	res[y, x, 1] = col_median(colors[1, 1, 1], colors[1, 0, 1], soft_mask[y, x, 1])
			#	res[y, x, 2] = col_median(colors[1, 1, 2], colors[1, 0, 2], soft_mask[y, x, 1])
			#elif hard_mask[y, x, 0] == 0 and hard_mask[y, x, 1] == 0 and hard_mask[y, x, 2] == 255: # C
			#	res[y, x, 0] = col_median(colors[2, 1, 0], colors[2, 0, 0], soft_mask[y, x, 1])
			#	res[y, x, 1] = col_median(colors[2, 1, 1], colors[2, 0, 1], soft_mask[y, x, 1])
			#	res[y, x, 2] = col_median(colors[2, 1, 2], colors[2, 0, 2], soft_mask[y, x, 1])
			#else:
			#	res[y, x, 3] = 0x00
			if hard_mask[y, x, 0] == 255 and hard_mask[y, x, 1] == 0 and hard_mask[y, x, 2] == 0:   # A
				ccol = 0
			elif hard_mask[y, x, 0] == 0 and hard_mask[y, x, 1] == 255 and hard_mask[y, x, 2] == 0: # B
				ccol = 1
			elif hard_mask[y, x, 0] == 0 and hard_mask[y, x, 1] == 0 and hard_mask[y, x, 2] == 255: # C
				ccol = 2
			else:
				res[y, x, 3] = 0x00
				continue
			if soft_mask[y, x, 1] >= soft_mask[y, x, 0]:
				dif = 127 + (127)
			else:
				dif = 
			for rgb in range(3):
				c0 = col_median(colors[ccol, 1, rgb], colors[ccol, 0, rgb], soft_mask[y, x, 1])
				c1 = col_median(colors[ccol, 1, rgb], colors[ccol, 2, rgb], soft_mask[y, x, 0])
				res[y, x, rgb] = col_median(c0, c1, dif)
			

	return res