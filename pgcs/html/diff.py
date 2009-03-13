import pgcs.core.data
import pgcs.core.diff
core = pgcs.core

from . import tags

class Depth(object):
	__slots__ = ["_value"]

	def __init__(self, value=0):
		self._value = value

	def __add__(self, value):
		return Depth(self._value + value)

	def __str__(self):
		return "depth-%d" % self._value

def generate(diff):
	tagtree = tags.TagTree()

	table = tagtree.table["database"]
	gen_database_head(table, diff)
	gen_database_body(table, diff)

	return tagtree.get_element_tree()

def gen_database_head(table, diff):
	tr = table.thead.tr
	tr.th(colspan=2)
	tr.th["left"].div[:] = diff.objects[0].get_name()
	tr.th["right"].div[:] = diff.objects[1].get_name()

def gen_database_body(table, diff):
	depth = Depth()

	tbody = table.tbody
	gen_named_seq(tbody, depth, diff.languages)
	gen_named_seq(tbody, depth, diff.namespaces)

def gen_value(tbody, depth, diff, name):
	tr = tbody.tr[("diff", depth)]
	tr.td
	tr.td["name"].div[:] = name
	tr.td["diff"](colspan=2).div["value"][:] = diff

def gen_different_types(tbody, depth, diff, name):
	gen_value(tbody, depth, core.diff.Value(type(diff.left), type(diff.right)), name)

def gen_language(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")

def gen_namespace(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_named_seq(tbody, depth + 1, diff.types)
	# TODO: composites
	# TODO: indexes
	# TODO: tables
	# TODO: views
	# TODO: sequences
	gen_named_seq(tbody, depth + 1, diff.functions)
	# TODO: operators
	# TODO: opclasses

def gen_type(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.notnull, "notnull")
	gen_value(tbody, depth + 1, diff.default, "default")

def gen_domain(tbody, depth, diff):
	gen_type(tbody, depth, diff)
	gen_value(tbody, depth + 1, diff.basetype, "basetype")
	# TODO: domain constraints

def gen_function(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.language, "language")
	gen_value(tbody, depth + 1, diff.rettype, "rettype")
	gen_value(tbody, depth + 1, diff.argtypes, "argtypes")
	gen_value(tbody, depth + 1, diff.source1, "source1")
	gen_value(tbody, depth + 1, diff.source2, "source2")

object_types = {
	core.diff.DifferentTypes: ("different-type", [],     gen_different_types),
	core.diff.Domain:         ("domain",         [],     gen_domain),
	core.diff.Function:       ("function",       [],     gen_function),
	core.diff.Language:       ("language",       [],     gen_language),
	core.diff.Namespace:      ("namespace",      [],     gen_namespace),
	core.diff.Type:           ("type",           [],     gen_type),
	core.data.Domain:         ("domain",         ["miss"], None),
	core.data.Function:       ("function",       ["miss"], None),
	core.data.Language:       ("language",       ["miss"], None),
	core.data.Namespace:      ("namespace",      ["miss"], None),
	core.data.Type:           ("type",           ["miss"], None),
}

def gen_named_seq(tbody, depth, seq):
	for name, what, obj in seq or ():
		kind, classes, func = object_types[type(obj)]

		tr = tbody.tr[classes + [depth]]
		tr.td["type"].div[:] = kind
		tr.td["name"].div[:] = name

		if func:
			func(tbody, depth, obj)
		elif what < 0:
			tr.td["left yes"].div
			tr.td["right no"].div
		elif what > 0:
			tr.td["left no"].div
			tr.td["right yes"].div
