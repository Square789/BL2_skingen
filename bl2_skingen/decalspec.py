"""Provides the method parse_decalspec, which does fancy stuff."""
import re
RE_DECALSPEC = re.compile(
	r"^(-?\d+)(%?)\s+(-?\d+)(%?)\s+(\d*\.?\d+)\s+(\d*\.?\d+)(%?)" \
	r"(?:\s+(\d*\.?\d+)(%?))?(?:\s+(y|n))?\s*$"
)
# 0: Global match
# 1: posx (int)
# 2: "" or "%", indicates whether posx should be treated relatively.
# 3: posy (int)
# 4: "" or "%", indicates whether posy should be treated relatively.
# 5: rot (float)
# 6: scale0 (float)
# 7: "" or "%", indicates whether scale should be treated relatively.
# 8: scale1 (float) *
# 9: "" or "%", indicates whether scale1 should be treated relatively. *
# 10: repeat ("" or "y" or "n") *

class Decalspec():
	def __init__(self, posx, posy, rot, scalex, scaley, repeat):
		self.posx = posx
		self.posy = posy
		self.rot = rot
		self.scalex = scalex
		self.scaley = scaley
		self.repeat = repeat

	def __repr__(self):
		return ("<Decalspec posx: {}, posy: {}, rotation: {}, scalex: {}, "
			"scaley: {}, repeat?: {}>".format(self.posx, self.posy,
				self.rot, self.scalex, self.scaley, self.repeat))

def validate_decalspec(spec):
	"""Validates the form of a decalspec, without needing any values
	to apply. Returns true if the spec was okay, else false.
	"""
	matchobj = RE_DECALSPEC.search(spec)
	if matchobj is None:
		return False
	return True

def parse_decalspec(spec, dim_x, dim_y):
	matchobj = RE_DECALSPEC.match(spec)
	if matchobj[2] == "%":
		posx = (int(matchobj[1])/100) * dim_x
	else:
		posx = int(matchobj[1])
	if matchobj[4] == "%":
		posy = (int(matchobj[3])/100) * dim_y
	else:
		posy = int(matchobj[3])
	rot = float(matchobj[5])
	if matchobj[8] is None:
		#bi-axis scale
		if matchobj[7] == "%":
			scalex = (float(matchobj[6])/100) * dim_x
			scaley = (float(matchobj[6])/100) * dim_y
		else:
			scalex = float(matchobj[6])
			scaley = scalex
	else:
		#for-each axis scale
		if matchobj[7] == "%":
			scalex = (float(matchobj[6])/100) * dim_x
		else:
			scalex = float(matchobj[6])
		if matchobj[9] == "%": # If 8 got detected, 9 will be "" or "%"
			scaley = (float(matchobj[8])/100) * dim_y
		else:
			scaley = float(matchobj[8])
	if matchobj[10] == "y":
		repeat = True
	else:
		repeat = False

	return Decalspec(posx, posy, rot, scalex, scaley, repeat)
