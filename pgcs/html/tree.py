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
	gen_named_seq(body, obj.languages)
	gen_named_seq(body, obj.namespaces)

def gen_value(body, obj, name):
	if obj:
		row = element(body, "tr", "value")
		element(element(row, "td", "type"), "div").text = name
		element(row, "td")
		element(element(row, "td", "left"), "div").text = unicode(obj.left)
		element(element(row, "td", "right"), "div").text = unicode(obj.right)

def gen_language(body, obj):
	gen_value(body, obj.owner, "owner")

def gen_namespace(body, obj):
	gen_value(body, obj.owner, "owner")
	gen_named_seq(body, obj.types)
	# TODO: ...

def gen_type(body, obj):
	gen_value(body, obj.owner, "owner")
	gen_value(body, obj.notnull, "notnull")
	gen_value(body, obj.default, "default")

def gen_domain(body, obj):
	gen_type(body, obj)
	gen_value(body, obj.basetype, "basetype")

object_types = {
	core.diff.Language:     (["language",  "diff"], gen_language),
	core.objects.Language:  (["language",  "miss"], None),
	core.diff.Namespace:    (["namespace", "diff"], gen_namespace),
	core.objects.Namespace: (["namespace", "miss"], None),
	core.diff.Type:         (["type",      "diff"], gen_type),
	core.objects.Type:      (["type",      "miss"], None),
	core.diff.Domain:       (["domain",    "diff"], gen_domain),
	core.objects.Domain:    (["domain",    "miss"], None),
}

def gen_named_seq(body, seq):
	for name, what, obj in seq or empty:
		classes, func = object_types[type(obj)]
		kind, mode = classes

		row = element(body, "tr", classes)
		element(element(row, "td", "type"), "div").text = kind
		element(element(row, "td", "name"), "div").text = name

		if func:
			func(body, obj)
		elif what < 0:
			element(element(row, "td", ["left", "yes"]), "div")
			element(element(row, "td", ["right", "no"]), "div")
		elif what > 0:
			element(element(row, "td", ["left", "no"]), "div")
			element(element(row, "td", ["right", "yes"]), "div")

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
