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

def gen_value(tbody, depth, diff, name):
	if diff:
		if type(diff) in type_handlers:
			kind, classes, func = type_handlers[diff.__class__]
		else:
			kind = str(diff.__class__)

		tr = tbody.tr[("value", depth)]
		tr.td["diff"].div["value"][:] = diff
		tr.td["name"].div[:] = name

def __xxx__gen_different_types(tbody, depth, diff, name):
	l, r = diff.objects
	gen_value(tbody, depth, core.diff.Value(type(l), type(r)), name)

def gen_object_list_head(tbody, depth, diff, listname):
	if diff and listname:
		tr = tbody.tr[("list-head", depth)]
		tr.td
		tr.td["name"].div[:] = listname

		depth = depth + 1

	return depth

def __xxx__gen_object_list_body(tbody, depth, seq, listname):
	for name, what, obj in seq:
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

def gen_named_object_list(tbody, depth, diff, listname=None):
	if not diff:
		return

	depth = gen_object_list_head(tbody, depth, diff, listname)

	for entry in diff.entries:
		tr = tbody.tr[("list-entry", depth)] # TODO: more classes
		tr.td["type"].div # TODO: content
		tr.td["name"].div[:] = entry.name

		count = 0

		groups = {}
		for value, group in entry.value.values:
			if value is not None:
				count = groups.get(group, 0)
				groups[group] = count + 1

		def get_sorting(item):
			group, count = item
			return -count

		def get_group(item):
			group, count = item
			return group

		colors = [get_group(i) for i in sorted(groups.iteritems(), key=get_sorting)]

		for value, group in entry.value.values:
			classes = ["value"]

			if value is None:
				classes.append("miss")
			else:
				classes.append("have")

				color = colors.index(group)
				classes.append("color-%d" % color)

				count += 1

			tr.td[classes].div

		if count > 1:
			kind, classes, func = type_handlers[type(entry.diff)]
			func(tbody, depth, entry.diff)

def gen_ordered_object_list(tbody, depth, diff, listname):
	gen_value(tbody, depth, diff, listname)

# Database

def gen_database(tree, diff):
	table = tree.table["database"]
	gen_database_head(table, diff)
	gen_database_body(table, diff)

def gen_database_head(table, diff):
	tr = table.thead.tr
	tr.th(colspan=2)
	for obj in diff.objects:
		tr.th["db"].div[:] = obj.get_name()

def gen_database_body(table, diff):
	depth = Depth()

	tbody = table.tbody
	gen_named_object_list(tbody, depth, diff.languages)
	gen_named_object_list(tbody, depth, diff.namespaces)

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
	gen_named_object_list(tbody, depth + 1, diff.constraints, "constraints")

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
	gen_ordered_object_list(tbody, depth + 1, diff.columns, "columns")

def gen_rule_relation(tbody, depth, diff):
	gen_relation(tbody, depth, diff)
	gen_named_object_list(tbody, depth + 1, diff.rules, "rules")

def gen_table(tbody, depth, diff):
	gen_rule_relation(tbody, depth, diff)
	gen_named_object_list(tbody, depth + 1, diff.triggers, "triggers")
	gen_named_object_list(tbody, depth + 1, diff.constraints, "constraints")

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

# Constraint

def gen_constraint(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.definition, "definition")

def gen_column_constraint(tbody, depth, diff):
	gen_constraint(tbody, depth, diff)
	gen_ordered_object_list(tbody, depth + 1, diff.columns, "columns")

def gen_foreign_key(tbody, depth, diff):
	gen_column_constraint(tbody, depth, diff)
	gen_value(tbody, depth + 1, diff.foreign_table, "foreign-table")
	gen_ordered_object_list(tbody, depth + 1, diff.foreign_columns, "foreign-columns")

# Trigger

def gen_trigger(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.function, "function")
	gen_value(tbody, depth + 1, diff.description, "description")

# Rule

def gen_rule(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.definition, "definition")

# Operator

def gen_operator(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")

def gen_operator_class(tbody, depth, diff):
	gen_value(tbody, depth + 1, diff.owner, "owner")
	gen_value(tbody, depth + 1, diff.intype, "intype")
	gen_value(tbody, depth + 1, diff.default, "default")
	gen_value(tbody, depth + 1, diff.keytype, "keytype")

type_handlers = {
	core.data.CheckColumnConstraint:  ("check-column-constraint",  ["miss"], None),
	core.data.CheckConstraint:        ("check-constraint",         ["miss"], None),
	core.data.Column:                 ("column",                   ["miss"], None),
	core.data.Composite:              ("composite",                ["miss"], None),
	core.data.Domain:                 ("domain",                   ["miss"], None),
	core.data.ForeignKey:             ("foreign-key",              ["miss"], None),
	core.data.Function:               ("function",                 ["miss"], None),
	core.data.Index:                  ("index",                    ["miss"], None),
	core.data.Language:               ("language",                 ["miss"], None),
	core.data.Namespace:              ("namespace",                ["miss"], None),
	core.data.Operator:               ("operator",                 ["miss"], None),
	core.data.OperatorClass:          ("operator-class",           ["miss"], None),
	core.data.PrimaryKey:             ("primary-key",              ["miss"], None),
	core.data.Rule:                   ("rule",                     ["miss"], None),
	core.data.Sequence:               ("sequence",                 ["miss"], None),
	core.data.Table:                  ("table",                    ["miss"], None),
	core.data.Trigger:                ("trigger",                  ["miss"], None),
	core.data.Type:                   ("type",                     ["miss"], None),
	core.data.UniqueColumnConstraint: ("unique-column-constraint", ["miss"], None),
	core.data.UniqueConstraint:       ("unique-constraint",        ["miss"], None),
	core.data.View:                   ("view",                     ["miss"], None),

	core.diff.CheckColumnConstraint:  ("check-column-constraint",  [], gen_column_constraint),
	core.diff.CheckConstraint:        ("check-constraint",         [], gen_constraint),
	core.diff.Column:                 ("column",                   [], gen_column),
	core.diff.Composite:              ("composite",                [], gen_relation),
	core.diff.__xxx__DifferentTypes:  ("different-type",           [], __xxx__gen_different_types),
	core.diff.Domain:                 ("domain",                   [], gen_domain),
	core.diff.ForeignKey:             ("foreign-key",              [], gen_foreign_key),
	core.diff.Function:               ("function",                 [], gen_function),
	core.diff.Index:                  ("index",                    [], gen_relation),
	core.diff.Language:               ("language",                 [], gen_language),
	core.diff.Namespace:              ("namespace",                [], gen_namespace),
	core.diff.Operator:               ("operator",                 [], gen_operator),
	core.diff.OperatorClass:          ("operator-class",           [], gen_operator_class),
	core.diff.PrimaryKey:             ("primary-key",              [], gen_column_constraint),
	core.diff.Rule:                   ("rule",                     [], gen_rule),
	core.diff.Sequence:               ("sequence",                 [], gen_sequence),
	core.diff.Table:                  ("table",                    [], gen_table),
	core.diff.Trigger:                ("trigger",                  [], gen_trigger),
	core.diff.Type:                   ("type",                     [], gen_type),
	core.diff.UniqueColumnConstraint: ("unique-column-constraint", [], gen_column_constraint),
	core.diff.UniqueConstraint:       ("unique-constraint",        [], gen_constraint),
	core.diff.View:                   ("view",                     [], gen_rule_relation),
}

def generate(diff):
	tree = tags.TagTree()
	gen_database(tree, diff)
	return tree.get_element_tree()
