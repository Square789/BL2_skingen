"""Provides the method parse_decalspec, which does fancy stuff."""
import re
RE_DECALSPEC = re.compile(
	r"^(-?\d+)(%?)\s+(-?\d+)(%?)\s+(\d*\.?\d+)\s+(\d*\.?\d+)" \
	r"(?:\s+(\d*\.?\d+))?(?:\s+(y|n))?\s*$"
)
# 0: Global match
# 1: posx (int)
# 2: "" or "%", indicates whether posx should be treated relatively.
# 3: posy (int)
# 4: "" or "%", indicates whether posy should be treated relatively.
# 5: rot (float)
# 6: scale0 (float)
# 7: scale1 (float) *
# 8: repeat ("" or "y" or "n") *

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

def parse_decalspec(spec, base_x, base_y):
	"""
	Parses the spec and configures potential relatives with
	additional parameters.
	spec : str | Decalspec string
	base_x : int | Size of entire base image along x axis
	base_y : int | Size of entire base image along y axis
	"""
	matchobj = RE_DECALSPEC.match(spec)
	if matchobj[2] == "%":
		posx = (int(matchobj[1])/100) * base_x
	else:
		posx = int(matchobj[1])
	if matchobj[4] == "%":
		posy = (int(matchobj[3])/100) * base_y
	else:
		posy = int(matchobj[3])
	rot = float(matchobj[5])
	if matchobj[7] is None:
		#bi-axis scale
		scalex = (float(matchobj[6]))
		scaley = scalex
	else:
		#for-each axis scale
		scalex = (float(matchobj[6]))
		scaley = (float(matchobj[7]))
	if matchobj[8] == "y":
		repeat = True
	else:
		repeat = False

	return Decalspec(posx, posy, rot, scalex, scaley, repeat)
