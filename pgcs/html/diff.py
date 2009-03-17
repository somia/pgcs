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
	gen_named_object_list(tbody, depth, diff.languages)
	gen_named_object_list(tbody, depth, diff.namespaces)

def gen_value(tbody, depth, diff, name):
	if diff:
		tr = tbody.tr[("diff", depth)]
		tr.td
		tr.td["name"].div[:] = name
		tr.td["diff"](colspan=2).div["value"][:] = diff

def gen_different_types(tbody, depth, diff, name):
	l, r = diff.objects
	gen_value(tbody, depth, core.diff.Value(type(l), type(r)), name)

def gen_named_object_list(tbody, depth, seq):
	for name, what, obj in seq or ():
		kind, classes, func = type_handlers[type(obj)]

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

def gen_ordered_object_list(tbody, depth, seq):
	gen_named_object_list(tbody, depth, seq)

# Language

def gen_language(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")

# Namespace

def gen_namespace(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_named_object_list(tbody, depth + 1, diff.types)
	gen_named_object_list(tbody, depth + 1, diff.composites)
	gen_named_object_list(tbody, depth + 1, diff.indexes)
	gen_named_object_list(tbody, depth + 1, diff.tables)
	gen_named_object_list(tbody, depth + 1, diff.views)
	gen_named_object_list(tbody, depth + 1, diff.sequences)
	gen_named_object_list(tbody, depth + 1, diff.functions)
	gen_named_object_list(tbody, depth + 1, diff.operators)
	gen_named_object_list(tbody, depth + 1, diff.opclasses)

# Type

def gen_type(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.notnull, "notnull")
	gen_value(tbody, depth + 1, diff.default, "default")

def gen_domain(tbody, depth, diff):
	gen_type(tbody, depth, diff)
	gen_value(tbody, depth + 1, diff.basetype, "basetype")
	# TODO: domain constraints

# Function

def gen_function(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.language, "language")
	gen_value(tbody, depth + 1, diff.rettype, "rettype")
	gen_value(tbody, depth + 1, diff.argtypes, "argtypes")
	gen_value(tbody, depth + 1, diff.source1, "source1")
	gen_value(tbody, depth + 1, diff.source2, "source2")

# Relation

def gen_relation(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_ordered_object_list(tbody, depth + 1, diff.columns)

def gen_rule_relation(tbody, depth, diff):
	gen_relation(tbody, depth, diff)
	# TODO: rules

def gen_table(tbody, depth, diff):
	gen_rule_relation(tbody, depth, diff)
	# TODO: triggers
	# TODO: table constraints

# Sequence

def gen_sequence(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.increment, "increment")
	gen_value(tbody, depth + 1, diff.minimum, "minimum")
	gen_value(tbody, depth + 1, diff.maximum, "maximum")

# Column

def gen_column(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.type, "type")
	gen_value(tbody, depth + 1, diff.notnull, "notnull")
	gen_value(tbody, depth + 1, diff.default, "default")

# Column

def gen_column(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.type, "type")
	gen_value(tbody, depth + 1, diff.notnull, "notnull")
	gen_value(tbody, depth + 1, diff.default, "default")

# Operator

def gen_operator(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")

def gen_operator_class(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.intype, "intype")
	gen_value(tbody, depth + 1, diff.default, "default")
	gen_value(tbody, depth + 1, diff.keytype, "keytype")

type_handlers = {
	core.diff.Column:         ("column",         [],       gen_column),
	core.diff.Composite:      ("composite",      [],       gen_relation),
	core.diff.DifferentTypes: ("different-type", [],       gen_different_types),
	core.diff.Domain:         ("domain",         [],       gen_domain),
	core.diff.Function:       ("function",       [],       gen_function),
	core.diff.Index:          ("index",          [],       gen_relation),
	core.diff.Language:       ("language",       [],       gen_language),
	core.diff.Namespace:      ("namespace",      [],       gen_namespace),
	core.diff.Operator:       ("operator",       [],       gen_operator),
	core.diff.OperatorClass:  ("operator-class", [],       gen_operator_class),
	core.diff.Sequence:       ("sequence",       [],       gen_sequence),
	core.diff.Table:          ("table",          [],       gen_table),
	core.diff.Type:           ("type",           [],       gen_type),
	core.diff.View:           ("view",           [],       gen_rule_relation),
	core.data.Column:         ("column",         ["miss"], None),
	core.data.Composite:      ("composite",      ["miss"], None),
	core.data.Domain:         ("domain",         ["miss"], None),
	core.data.Function:       ("function",       ["miss"], None),
	core.data.Index:          ("index",          ["miss"], None),
	core.data.Language:       ("language",       ["miss"], None),
	core.data.Namespace:      ("namespace",      ["miss"], None),
	core.data.Operator:       ("operator",       ["miss"], None),
	core.data.OperatorClass:  ("operator-class", ["miss"], None),
	core.data.Sequence:       ("sequence",       ["miss"], None),
	core.data.Table:          ("table",          ["miss"], None),
	core.data.Type:           ("type",           ["miss"], None),
	core.data.View:           ("view",           ["miss"], None),
}
