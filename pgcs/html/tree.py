import xml.etree.ElementTree as elementtree

def schema(obj):
	root = element(None, "table", "schema")
	named_seq(root, Language, obj.languages)
	# TODO: named_seq(root, Namespace, obj.namespaces)
	return elementtree.ElementTree(root)

class Language:
	name = "language"

	@staticmethod
	def populate(table, obj):
		if obj.owner:
			row = element(table, "tr", [name, "property"])
			element(row, "td", "key").text = "owner"
			element(row, "td", "left").text = obj.owner.left
			element(row, "td", "right").text = obj.owner.right

def named_seq(table, impl, seq):
	for name, what, obj in seq:
		if what != 0:
			kind = "missing"
		else:
			kind = "diff"

		row = element(table, "tr", [impl.name, kind])
		element(row, "td", "name").text = name

		if what < 0:
			element(row, "td", ["left", "exists"])
			element(row, "td", ["right", "missing"])
		elif what > 0:
			element(row, "td", ["left", "missing"])
			element(row, "td", ["right", "exists"])
		else:
			impl.populate(table, obj)

def element(parent, tag, classes=None):
	attribs = {}

	if classes:
		if isinstance(classes, (list, tuple, set)):
			classes = " ".join(classes)
		attribs["class"] = classes

	if parent is None:
		return elementtree.Element(tag, attribs)
	else:
		return elementtree.SubElement(parent, tag, attribs)
