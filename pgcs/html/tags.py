import xml.etree.ElementTree as elementtree

class TagTree(object):
	def __init__(self):
		self._tree = None

	def __getattr__(self, name):
		assert self._tree is None
		element = elementtree.Element(name)
		self._tree = elementtree.ElementTree(element)
		return Tag(element)

	def get_element_tree(self):
		return self._tree

class Tag(object):
	__slots__ = ["_element"]

	def __init__(self, element, name=None):
		if name is None:
			self._element = element
		else:
			self._element = elementtree.SubElement(element, name)

	# Example: tag.div
	def __getattr__(self, name):
		return Tag(self._element, name)

	# Example: tag["my-class"]
	#          tag[("first-class", "second-class")]
	def __getitem__(self, classes):
		if isinstance(classes, (tuple, list, set)):
			classes = " ".join([str(c) for c in classes])

		self.__call__(**{"class": str(classes)})
		return self

	# Example: tag[:] = "text"
	def __setitem__(self, key, text):
		assert isinstance(key, slice)
		self._element.text = unicode(text)

	# Example: tag(colspan="2")
	def __call__(self, text=None, **kwargs):
		if text is not None:
			self._element.text = unicode(text)

		if kwargs:
			attrib = {}
			for key, value in kwargs.iteritems():
				attrib[key] = str(value)
			self._element.attrib.update(attrib)

		return self
