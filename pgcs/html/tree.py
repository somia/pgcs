import xml.etree.ElementTree as elementtree

import pgcs.core.data
import pgcs.core.diff
core = pgcs.core

def generate(diff):
	table = element(None, "table", "database")
	gen_database_head(table, diff)
	gen_database_body(table, diff)
	return elementtree.ElementTree(table)

def gen_database_head(table, diff):
	head = element(table, "thead")
	row = element(head, "tr")
	element(row, "th").attrib["colspan"] = "2"
	element(element(row, "th", "left"), "div").text = diff.objects[0].get_name()
	element(element(row, "th", "right"), "div").text = diff.objects[1].get_name()

def gen_database_body(table, diff):
	body = element(table, "tbody")
	gen_named_seq(body, 0, diff.languages)
	gen_named_seq(body, 0, diff.namespaces)

def gen_value(body, depth, diff, name):
	row = element(body, "tr", "diff", depth)
	element(row, "td")
	element(element(row, "td", "name"), "div").text = name
	cell = element(row, "td", "diff")
	cell.attrib["colspan"] = "2"
	content = element(cell, "div", "value")
	content.text = unicode(diff)

def gen_different_types(body, depth, diff, name):
	gen_value(body, depth, core.diff.Value(type(diff.left), type(diff.right)), name)

def gen_language(body, depth, diff):
	gen_value(body, depth + 1, diff.owner, "owner")

def gen_namespace(body, depth, diff):
	gen_value(body, depth + 1, diff.owner, "owner")
	gen_named_seq(body, depth + 1, diff.types)
	# TODO: composites
	# TODO: indexes
	# TODO: tables
	# TODO: views
	# TODO: sequences
	gen_named_seq(body, depth + 1, diff.functions)
	# TODO: operators
	# TODO: opclasses

def gen_type(body, depth, diff):
	gen_value(body, depth + 1, diff.owner, "owner")
	gen_value(body, depth + 1, diff.notnull, "notnull")
	gen_value(body, depth + 1, diff.default, "default")

def gen_domain(body, depth, diff):
	gen_type(body, depth, diff)
	gen_value(body, depth + 1, diff.basetype, "basetype")
	# TODO: domain constraints

def gen_function(body, depth, diff):
	gen_value(body, depth + 1, diff.owner, "owner")
	gen_value(body, depth + 1, diff.language, "language")
	gen_value(body, depth + 1, diff.rettype, "rettype")
	gen_value(body, depth + 1, diff.argtypes, "argtypes")
	gen_value(body, depth + 1, diff.source1, "source1")
	gen_value(body, depth + 1, diff.source2, "source2")

object_types = {
	core.diff.DifferentTypes: ("different-type", None,   gen_different_types),
	core.diff.Domain:         ("domain",         None,   gen_domain),
	core.diff.Function:       ("function",       None,   gen_function),
	core.diff.Language:       ("language",       None,   gen_language),
	core.diff.Namespace:      ("namespace",      None,   gen_namespace),
	core.diff.Type:           ("type",           None,   gen_type),
	core.data.Domain:         ("domain",         "miss", None),
	core.data.Function:       ("function",       "miss", None),
	core.data.Language:       ("language",       "miss", None),
	core.data.Namespace:      ("namespace",      "miss", None),
	core.data.Type:           ("type",           "miss", None),
}

def gen_named_seq(body, depth, seq):
	for name, what, obj in seq or ():
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
