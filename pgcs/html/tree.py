import xml.etree.ElementTree as elementtree

import pgcs.core.diff
import pgcs.core.objects
core = pgcs.core

empty = ()

def generate(obj):
	table = element(None, "table", "schema")
	gen_schema_head(table, obj)
	gen_schema_body(table, obj)
	return elementtree.ElementTree(table)

def gen_schema_head(table, obj):
	head = element(table, "thead")
	row = element(head, "tr")
	element(row, "th").attrib["colspan"] = "2"
	element(element(row, "th", "left"), "div").text = obj.databases[0].name
	element(element(row, "th", "right"), "div").text = obj.databases[1].name

def gen_schema_body(table, obj):
	body = element(table, "tbody")
	gen_named_seq(body, 0, obj.languages)
	gen_named_seq(body, 0, obj.namespaces)

def gen_value(body, depth, obj, name):
	if obj:
		row = element(body, "tr", "diff", depth)
		element(row, "td")
		element(element(row, "td", "name"), "div").text = name
		cell = element(row, "td", "diff")
		cell.attrib["colspan"] = "2"

		content = element(cell, "div", "value")
		content.text = unicode(obj)

def gen_language(body, depth, obj):
	gen_value(body, depth + 1, obj.owner, "owner")

def gen_namespace(body, depth, obj):
	gen_value(body, depth + 1, obj.owner, "owner")
	gen_named_seq(body, depth + 1, obj.types)
	# TODO: ...
	gen_named_seq(body, depth + 1, obj.functions)
	# TODO: ...

def gen_type(body, depth, obj):
	gen_value(body, depth + 1, obj.owner, "owner")
	gen_value(body, depth + 1, obj.notnull, "notnull")
	gen_value(body, depth + 1, obj.default, "default")

def gen_domain(body, depth, obj):
	gen_type(body, depth, obj)
	gen_value(body, depth + 1, obj.basetype, "basetype")
	# TODO: constraints

def gen_function(body, depth, obj):
	gen_value(body, depth + 1, obj.owner, "owner")
	gen_value(body, depth + 1, obj.language, "language")
	gen_value(body, depth + 1, obj.rettype, "rettype")
	gen_value(body, depth + 1, obj.argtypes, "argtypes")
	gen_value(body, depth + 1, obj.source1, "source1")
	gen_value(body, depth + 1, obj.source2, "source2")

object_types = {
	core.diff.Language:     ("language",  None,   gen_language),
	core.objects.Language:  ("language",  "miss", None),
	core.diff.Namespace:    ("namespace", None,   gen_namespace),
	core.objects.Namespace: ("namespace", "miss", None),
	core.diff.Type:         ("type",      None,   gen_type),
	core.objects.Type:      ("type",      "miss", None),
	core.diff.Domain:       ("domain",    None,   gen_domain),
	core.objects.Domain:    ("domain",    "miss", None),
	core.diff.Function:     ("function",  None,   gen_function),
	core.objects.Function:  ("function",  "miss", None),
}

def gen_named_seq(body, depth, seq):
	for name, what, obj in seq or empty:
		kind, classes, func = object_types[type(obj)]

		row = element(body, "tr", classes, depth)
		element(element(row, "td", "type"), "div").text = kind
		element(element(row, "td", "name"), "div").text = name

		if func:
			func(body, depth, obj)
		elif what < 0:
			element(element(row, "td", ["left", "yes"]), "div")
			element(element(row, "td", ["right", "no"]), "div")
		elif what > 0:
			element(element(row, "td", ["left", "no"]), "div")
			element(element(row, "td", ["right", "yes"]), "div")

def element(parent, tag, classes=None, depth=None):
	attribs = {}

	if classes and not isinstance(classes, (list, tuple, set)):
		classes = [classes]

	if depth is not None:
		if classes:
			classes = list(classes)
		else:
			classes = []
		classes.append("depth-%d" % depth)

	if classes:
		attribs["class"] = " ".join(classes)

	if parent is None:
		return elementtree.Element(tag, attribs)
	else:
		return elementtree.SubElement(parent, tag, attribs)
