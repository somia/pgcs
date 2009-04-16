import pgcs.core.data
import pgcs.core.diff
core = pgcs.core

from . import tags

def version_count(diff):
	count = 0
	for value, group in diff.values:
		if value is not None:
			count += 1
	return count

def gen_columns(parent, diff):
	groups = {}
	for value, group in diff.values:
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

	span = parent.span["columns"]

	for column, (value, group) in enumerate(diff.values):
		classes = ["column-%d" % column]

		if value is None:
			classes.append("miss")
		else:
			classes.append("have")

			color = colors.index(group)
			classes.append("color-%d" % color)

		span.span[classes].div

def gen_value(parent, diff, name):
	if diff:
		div = parent.div["value"]
		div.span["name"][:] = name
		gen_columns(div, diff)
		div.div["diff"][:] = diff

def gen_object_list_head(parent, diff, name):
	div = parent.div["list"]
	if name:
		head = div.div["head"]
		head.span["name"][:] = name
	return div

def gen_named_object_list(parent, diff, name=None):
	if diff:
		head = gen_object_list_head(parent, diff, name)

		for entry in diff.entries:
			kind, func = diff_types[type(entry.diff)]

			count = version_count(entry.value)

			div = head.div["entry"]

			if count > 1:
				div.div["expander"][:] = "+"

			div.span["type"][:] = kind
			div.span["name"][:] = entry.name

			gen_columns(div, entry.value)

			if count > 1:
				children = div.div["children"]
				func(children, entry.diff)

def gen_ordered_object_list(parent, diff, name):
	gen_value(parent, diff, name)

# Database

def gen_database(tree, diff):
	div = tree.div["database"]
	gen_database_head(div, diff)
	gen_database_body(div, diff)

def gen_database_head(parent, diff):
	span = parent.div["head"].span["columns"]
	for column, obj in enumerate(diff.objects):
		span.span[("column-%d" % column)][:] = obj.get_name()

def gen_database_body(parent, diff):
	body = parent.div["body"]
	body.div["expander"][:] = "+"
	div = body.div["children"]
	gen_named_object_list(div, diff.languages)
	gen_named_object_list(div, diff.namespaces)

# Language

def gen_language(div, diff):
	gen_value(div, diff.owner, "owner")

# Namespace

def gen_namespace(div, diff):
	gen_value(div, diff.owner, "owner")
	gen_named_object_list(div, diff.types)
	gen_named_object_list(div, diff.composites)
	gen_named_object_list(div, diff.indexes)
	gen_named_object_list(div, diff.tables)
	gen_named_object_list(div, diff.views)
	gen_named_object_list(div, diff.sequences)
	gen_named_object_list(div, diff.functions)
	gen_named_object_list(div, diff.operators)
	gen_named_object_list(div, diff.opclasses)

# Type

def gen_type(div, diff):
	gen_value(div, diff.owner, "owner")
	gen_value(div, diff.notnull, "notnull")
	gen_value(div, diff.default, "default")

def gen_domain(div, diff):
	gen_type(div, diff)
	gen_value(div, diff.basetype, "basetype")
	gen_named_object_list(div, diff.constraints, "constraints")

# Function

def gen_function(div, diff):
	gen_value(div, diff.owner, "owner")
	gen_value(div, diff.language, "language")
	gen_value(div, diff.rettype, "rettype")
	gen_value(div, diff.argtypes, "argtypes")
	gen_value(div, diff.source1, "source1")
	gen_value(div, diff.source2, "source2")

# Relation

def gen_relation(div, diff):
	gen_value(div, diff.owner, "owner")
	gen_ordered_object_list(div, diff.columns, "columns")

def gen_rule_relation(div, diff):
	gen_relation(div, diff)
	gen_named_object_list(div, diff.rules, "rules")

def gen_table(div, diff):
	gen_rule_relation(div, diff)
	gen_named_object_list(div, diff.triggers, "triggers")
	gen_named_object_list(div, diff.constraints, "constraints")

# Sequence

def gen_sequence(div, diff):
	gen_value(div, diff.owner, "owner")
	gen_value(div, diff.increment, "increment")
	gen_value(div, diff.minimum, "minimum")
	gen_value(div, diff.maximum, "maximum")

# Column

def gen_column(div, diff):
	gen_value(div, diff.type, "type")
	gen_value(div, diff.notnull, "notnull")
	gen_value(div, diff.default, "default")

# Constraint

def gen_constraint(div, diff):
	gen_value(div, diff.definition, "definition")

def gen_column_constraint(div, diff):
	gen_constraint(div, diff)
	gen_ordered_object_list(div, diff.columns, "columns")

def gen_foreign_key(div, diff):
	gen_column_constraint(div, diff)
	gen_value(div, diff.foreign_table, "foreign-table")
	gen_ordered_object_list(div, diff.foreign_columns, "foreign-columns")

# Trigger

def gen_trigger(div, diff):
	gen_value(div, diff.function, "function")
	gen_value(div, diff.description, "description")

# Rule

def gen_rule(div, diff):
	gen_value(div, diff.definition, "definition")

# Operator

def gen_operator(div, diff):
	gen_value(div, diff.owner, "owner")

def gen_operator_class(div, diff):
	gen_value(div, diff.owner, "owner")
	gen_value(div, diff.intype, "intype")
	gen_value(div, diff.default, "default")
	gen_value(div, diff.keytype, "keytype")

diff_types = {
	core.diff.CheckColumnConstraint:  ("check-column-constraint",  gen_column_constraint),
	core.diff.CheckConstraint:        ("check-constraint",         gen_constraint),
	core.diff.Column:                 ("column",                   gen_column),
	core.diff.Composite:              ("composite",                gen_relation),
	core.diff.Domain:                 ("domain",                   gen_domain),
	core.diff.ForeignKey:             ("foreign-key",              gen_foreign_key),
	core.diff.Function:               ("function",                 gen_function),
	core.diff.Index:                  ("index",                    gen_relation),
	core.diff.Language:               ("language",                 gen_language),
	core.diff.Namespace:              ("namespace",                gen_namespace),
	core.diff.Operator:               ("operator",                 gen_operator),
	core.diff.OperatorClass:          ("operator-class",           gen_operator_class),
	core.diff.PrimaryKey:             ("primary-key",              gen_column_constraint),
	core.diff.Rule:                   ("rule",                     gen_rule),
	core.diff.Sequence:               ("sequence",                 gen_sequence),
	core.diff.Table:                  ("table",                    gen_table),
	core.diff.Trigger:                ("trigger",                  gen_trigger),
	core.diff.Type:                   ("type",                     gen_type),
	core.diff.UniqueColumnConstraint: ("unique-column-constraint", gen_column_constraint),
	core.diff.UniqueConstraint:       ("unique-constraint",        gen_constraint),
	core.diff.View:                   ("view",                     gen_rule_relation),
}

def generate(diff):
	tree = tags.TagTree()
	gen_database(tree, diff)
	return tree.get_element_tree()
