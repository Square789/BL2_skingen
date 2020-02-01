"""Hacky and unstable module to parse an unkown unreal engine file format.
It does not care about clarity / readability / efficiency.
See the Parser class and its parse method.
"""

"""The format seems to follow these rules: Key Value Pairs, key and value being
seperated by "=" and the pairs themselves seperated either by
\n or - when on the same line - ",". Values seem to be allowed to include spaces
as long as no termination via a , or \n occurs or the space is in front of the value.
Supports dicts with {}.
Keys may be suffixed with "[" <int> "]", where int indicates the length of a following
list, where all element's keys are "key_name[" <pos> "]".
As such, lists may not contain other lists.
"""

import re

RE_KEY = re.compile(r"[a-zA-Z0-9_]*")
RE_KEY_SUFFIX = re.compile(r"\[(\d*)\]")
#RE_EQ = re.compile(r"\s*=\s*")
# RE_EQ = re.compile(r"\s*=((?= \n))?(?(1).|\s*.)") # Weird cond lookahead relies on
#really specific formatting on empty simple parameters and a really ugly "-1"
# It works, just don't touch it please
RE_EQ = re.compile(r"\s*=((?= \n))?(?(1)|\s*)")
#haha eat a brick 20 minutes past square i touched it
RE_VAL = re.compile(r"(.*?)((,|\n|$)|(?=}))")
RE_WHITESPACE = re.compile(r"\s*")

class UnrealNotationParseError(ValueError):
	pass

class Parser():
	def __init__(self, raw_file):
		"raw_file: The file's complete contents."
		self.raw_file = raw_file
		self.pos = 0

	def parse(self):
		self._skip_whitespace()
		res = {}
		while True:
			res.update(self._ident_key_and_parse_kv_pair())
			self._skip_whitespace()
			if self.pos >= len(self.raw_file):
				break
		return res

	def _ident_key_and_parse_kv_pair(self):
		"""Called at the beginning/ after a kv pair is resolved.
		Resolves a k/v pair by getting the key name, looking at if it is followed
		by a special symbol and calling the appropiate parsing method.
		"""
		key_regex = RE_KEY.search(self.raw_file, self.pos)
		if not key_regex:
			raise ValueError()
		next_key_name = key_regex[0]
		self.pos += len(next_key_name)
		if self.raw_file[self.pos] == "[":
			is_list = True
			len_re = RE_KEY_SUFFIX.search(self.raw_file, self.pos)
			if not len_re:
				raise UnrealNotationParseError(f"Expected list length at around {self.pos}")
			self.pos += len(len_re[0])
			list_len = int(len_re[1])
		else:
			is_list = False
			list_len = -1
		self._skip_eq() # Eq also consumes whitespace
		# This could be: A string, list, dict
		return self._resolve_element(next_key_name, is_list, list_len)

	def _resolve_element(self, key_name, is_list, list_len = None):
		"""To be called when the pos is after an equal sign and its whitespace.
		Params: The preceding key and whether it is a list. If it is, include the
		expected list length"""
		if self.raw_file[self.pos] == "{" and not is_list:
			self.pos += 1
			return {key_name: self._parse_dict()}
		elif self.raw_file[self.pos] == "{" and is_list:
			self.pos += 1
			return {key_name: self._parse_list(list_len)}
		else:
			# print("Element resolver is calling simpl handler")
			return {key_name: self._parse_simple()}

	def _skip_whitespace(self):
		ws_match = RE_WHITESPACE.search(self.raw_file, self.pos)
		if ws_match:
			self.pos += len(ws_match[0])

	def _skip_eq(self):
		eq_search = RE_EQ.search(self.raw_file, self.pos)
		if not eq_search:
			raise UnrealNotationParseError(f"Expected an equal sign at around {self.pos}")
		self.pos += len(eq_search[0])

	def _parse_simple(self):
		"""Parses a simple quoteless key, up until a comma or newline is encountered.
		Will consume the separating newline/comma [EOF]
		"""
		val = RE_VAL.search(self.raw_file, self.pos)
		if not val:
			raise UnrealNotationParseError(f"Expected value at around {self.pos}")
		self.pos += len(val[0])
		return val[1] # regex also skips newline/comma

	def _parse_dict(self):
		"""Parses a dict starting from the current pos.
		"""
		res = {}
		while True:
			self._skip_whitespace()
			res.update(self._ident_key_and_parse_kv_pair())
			self._skip_whitespace()
			if self.raw_file[self.pos] == "}":
				self.pos += 1
				break
			elif self.pos >= len(self.raw_file) - 1:
				raise UnrealNotationParseError("EOF without closing dict bracket")
		return res

	def _parse_list(self, expected_len):
		"""Parses a list starting at self.pos, requires expected_len as an int."""
		res = [None for _ in range(expected_len)]
		while True:
			self._skip_whitespace()
			next_key = RE_KEY.search(self.raw_file, self.pos)
			next_key_name = next_key[0]
			self.pos += len(next_key_name)
			next_key_idx = RE_KEY_SUFFIX.search(self.raw_file, self.pos)
			if not next_key_idx:
				raise UnrealNotationParseError(f"Index-less list key at around {self.pos}")
			self.pos += len(next_key_idx[0])
			next_key_idx = int(next_key_idx[1])
			self._skip_eq()
			res[next_key_idx] = next(iter(self._resolve_element(next_key_name, False, -1).values()))

			self._skip_whitespace()
			if self.raw_file[self.pos] == "}":
				self.pos += 1
				break
			elif self.pos >= len(self.raw_file) - 1:
				raise UnrealNotationParseError("EOF without closing list bracket")
		return res

