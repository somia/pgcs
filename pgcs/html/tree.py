import xml.etree.ElementTree as elementtree

def div(parent, cls):
	return elementtree.SubElement(parent, "div", {"class": cls})

def span(parent, cls):
	return elementtree.SubElement(parent, "span", {"class": cls})

def schema(obj):
	root = elementtree.Element("div", {"class": "schema"})
	named_seq(root, Language, obj.languages)
	# TODO: named_seq(root, Namespace, obj.namespaces)
	return elementtree.ElementTree(root)

class Language:
	name = "language"

	@staticmethod
	def populate(e, obj):
		if obj.owner:
			owner = span(e, "owner")
			span(owner, "left").text = obj.owner.left
			span(owner, "right").text = obj.owner.right

def named_seq(parent, impl, seq):
	container = div(parent, "%s-list" % impl.name)

	for name, what, obj in seq:
		item = span(container, impl.name)

		span(item, "name").text = name

		if what == 0:
			desc = div(item, "diff")
			impl.populate(desc, obj)
		elif what < 0:
			span(item, "left exist").text = "X"
			span(item, "right noexist")
		elif what > 0:
			span(item, "left noexist")
			span(item, "right exist").text = "X"
