"""
Module for processing and unifying the props files.
"""

class SkippedNonNodelikeWarning(Warning):
	pass

class UnifiedProps():
	"""
	Serves as a namespace to make root attributes, ScalarParameterValues,
	TextureParameterValues and VectorParameterValues more accessible.
	"""
	def __init__(self, proc_dict):
		"""
		Create and setup this new UnifiedProps object

		proc_dict : dict | The preprocessed dict as returned by unify_props()
		"""
		self.TexturePV = proc_dict["TextureParameterValues"]
		self.ScalarPV = proc_dict["ScalarParameterValues"]
		self.VectorPV = proc_dict["VectorParameterValues"]
		self.root_elems = \
			{k: v for k ,v in proc_dict.items() if not k in (
				"TextureParameterValues", "ScalarParameterValues",
				"VectorParameterValues"
			)}

class UEParameterList():
	"""
	Makes Nodes easily accessible via a list-like structure.
	"""
	def __init__(self):
		self.node_list = []

	def append_node(self, node):
		if not isinstance(node, UEParameterNode):
			raise TypeError("Not a node.")
		if node.name in self:
			raise ValueError("Node name {} already in list.".format(node.name))
		self.node_list.append(node)

	def pop_node(self, idx):
		self.node_list.pop(idx)

	def get_node(self, name):
		"""
		Returns a node by its name.
		"""
		for i in self:
			if i.name == name:
				return i
		raise ValueError("Node {} not present in list.".format(name))

	def remove_node(self, name):
		"""
		Removes a node by its name.
		"""
		for i, j in enumerate(self):
			if name == j.name:
				self.node_list.pop(i)
				break
		else:
			raise ValueError("Node {} not present in list.".format(name))

	def __contains__(self, name):
		for i in self:
			if name == i.name:
				return True
		return False

	def __iter__(self):
		return iter(self.node_list)


class UEParameterNode():
	def __init__(self, name, value, info):
		self.name = name
		self.value = value
		self.info = info

	def __repr__(self):
		return "<UEParameterNode '{name}' at {addr}>".format(
			name = name, addr = hex(id(self)))

def _node_like(test_dict: dict):
	"""
	Evaluates whether a dict can be converted to a node safely.

	test_dict : dict | Dict to check
	"""
	if not isinstance(test_dict, dict):
		return False
	keys = list(test_dict.keys())
	try:
		keys.remove("ParameterName")
		keys.remove("ParameterValue")
		keys.remove("ParameterInfo")
	except ValueError:
		return False
	if keys:
		return False
	if not isinstance(test_dict["ParameterName"], str):
		return False
	if not isinstance(test_dict["ParameterInfo"], str):
		return False
	return True

def process_dict(p_dict):
	if _node_like(p_dict):
		return UEParameterNode(
			name = p_dict["ParameterName"],
			value = p_dict["ParameterValue"],
			info = p_dict["ParameterInfo"],
		)
	res = {}
	for k, v in p_dict.items():
		if isinstance(v, (list, tuple)):
			res[k] = process_list(v)
		elif isinstance(v, dict):
			res[k] = process_dict(v)
		else:
			res[k] = v
	return res

# THIS HEAVILY ASSUMES THE LISTS WILL NEVER CONTAIN SOLO LITERALS
def process_list(p_list):
	res = UEParameterList()
	for i in p_list:
		if _node_like(i):
			res.append_node(UEParameterNode(i["ParameterName"],
				i["ParameterValue"], i["ParameterInfo"]))
		else:
			raise SkippedNonNodelikeWarning("Skipped a non-nodelike element while creating "
				"UEParameterList. Please report this issue: {}".format(i))
	return res

def unify_props(p_dict):
	"""
	Parses a prop dict, breaking it further down into a unified
	structure.

	p_dict : dict | As returned by bl2_skingen.unreal_notation.Parser.parse

	Returns: UnifiedProps instance
	"""
	return UnifiedProps(process_dict(p_dict))
