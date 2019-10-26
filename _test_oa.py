import sys

from bl2_skingen.imaging.overlay import experimental_overlay
from PIL import Image
import numpy as np

i0 = Image.open("test0a.png")
i1 = Image.open("test1a.png")

i0a = np.array(i0)
i1a = np.array(i1)

if len(sys.argv) > 1:
	def scale_ints(a, b):
		t = (a * b) + 0x80
		return (((t) >> 8) + t) >> 8

	def normal_overlay(pxtop, pxbtm):
		res = [0, 0, 0]
		for chnl in range(3):
			if pxtop[chnl] < 127:
				res[chnl] = 2 * scale_ints(pxtop[chnl], pxbtm[chnl])
			else:
				res[chnl] = 255 - (2 * scale_ints((255 - pxtop[chnl]), (255 - pxbtm[chnl]) ))
		return tuple(res)

	import random
	itarget = np.array(Image.open("testshoulda.png"))
	icrrnt = np.array(Image.open("testouta.png"))
	print("Digging out values...")
	for _ in range(20):
		rndx = random.randint(0, i0a.shape[1])
		rndy = random.randint(0, i0a.shape[0])

		print(f"Pixel ({rndx: >4}|{rndy: >4})")

		for image, idesc in ((i0a, "Top  "), (i1a, "Bottm"), (itarget, "Targt"), (icrrnt, "Crrnt")):
			pr = image[rndy, rndx, 0]
			pg = image[rndy, rndx, 1]
			pb = image[rndy, rndx, 2]
			pa = image[rndy, rndx, 3]
			print(f"{idesc}: RGBA ({pr: >3}, {pg: >3}, {pb: >3}, {pa: >3})")

		print("Basic overlay:", normal_overlay(i0a[rndy, rndy], i1a[rndy, rndx]) )

		print("")
	exit()

r = experimental_overlay(i0a, i1a)

print(r.shape)

resimg = Image.fromarray(r, mode = "RGBA")
resimg.save("testouta.png")
