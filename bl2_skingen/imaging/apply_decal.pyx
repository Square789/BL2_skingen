import cython
import PIL
import numpy as np
cimport numpy as np

np.import_array()

DTYPE = np.uint8
ctypedef np.uint8_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef insert_array(
		np.ndarray[DTYPE_t, ndim = 3] target,
		np.ndarray[DTYPE_t, ndim = 3] source,
		int offset_x = 0,
		int offset_y = 0):
	"""
	Inserts source into target, designed for a 2-Dimensional image with RGBA at the lowest level.
	Optionally offset the insertion by offset_x and offset_y.
	If the offset is negative/source image is too large, it will be cut off accordingly.
	"""
	cdef int target_x = target.shape[1]
	cdef int target_y = target.shape[0]
	cdef int target_c = target.shape[2]
	cdef int source_x = source.shape[1]
	cdef int source_y = source.shape[0]
	cdef int source_c = source.shape[2]

	cdef int rngx_beg, rngx_end, rngy_beg, rngy_end, rng_chl, srcx_idx, srcy_idx

	if offset_x > target_x or offset_y > target_y:
		return #No effect.

	srcx_idx = 0
	srcy_idx = 0
	# X
	if offset_x < 0: #Image offset before target array
		rngx_beg = 0
		srcx_idx = - offset_x
	else:
		rngx_beg = offset_x
	if offset_x + source_x > target_x: #Image flows out of target array
		rngx_end = target_x
	else:
		rngx_end = offset_x + source_x
	# Y
	if offset_y < 0: #Image offset before target array
		rngy_beg = 0
		srcy_idx = - offset_y
	else:
		rngy_beg = offset_y
	if offset_y + source_y > target_y: #Image flows out of target array
		rngy_end = target_y
	else:
		rngy_end = offset_y + source_y
 	# Channel
	if source_c > target_c:
		rng_chl = target_c
	else:
		rng_chl = source_c

	cdef int y, x
	cdef np.uint8_t rgba

	cdef int yi, xi
	yi = 0; xi = 0
	for y in range(rngy_beg, rngy_end):
		for x in range(rngx_beg, rngx_end):
			for rgba in range(rng_chl):
				target[y, x, rgba] = source[yi + srcy_idx, xi + srcx_idx, rgba]
			xi += 1
		xi = 0
		yi += 1

@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[DTYPE_t, ndim = 3] apply_decal(
		decal,
		np.ndarray[DTYPE_t, ndim = 3] hard_mask,
		int pos_x = 0,
		int pos_y = 0,
		int deg = 0,
		tuple scale = (1, 1),
		repeat = False):
	"""
	Takes a decal image, hard mask and additional parameters (see the
	explanation of the decalspec in `bl2_skingen.argparser`), returns
	a numpy array representing the decal transformed according to the
	parameters.

	decal : PIL.Image
	hard_mask : np.ndarray[uint_8, ndim=3]
	"""
	#if type(decal) is not PIL.Image:
	#	raise TypeError("Decal must be a PIL.Image!")

	cdef np.ndarray[DTYPE_t, ndim = 3] res = \
		np.ndarray([hard_mask.shape[0], hard_mask.shape[1], 4], dtype = DTYPE)
	
	insert_array(res, np.array(decal), pos_x, pos_y)

	# yeah complete this. returned array should be laid over the generated image
	# at the supplied position, using regular alpha composition
	return res