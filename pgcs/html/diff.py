import difflib

import pgcs.core.data
import pgcs.core.diff
core = pgcs.core

from . import tags

database_objects = None

def get_colors(values):
	groups = {}
	for value, group in values:
		if value is not None:
			assert group >= 0
			count = groups.get(group, 0)
			groups[group] = count + 1
		else:
			assert group == -1

	def get_sorting(item):
		group, count = item
		return -count

	def get_group(item):
		group, count = item
		return group

	return [get_group(i) for i in sorted(groups.iteritems(), key=get_sorting)]

def gen_columns(parent, diff):
	colors = get_colors(diff.values)

	span = parent.span["columns"]

	for column, (value, group) in enumerate(diff.values):
		classes = ["column-%d" % column]

		content = ""

		if value is None:
			classes.append("miss")
		else:
			classes.append("have")

			color = colors.index(group)
			classes.append("color-%d" % color)

			if isinstance(value, core.data.Table):
				if value.has_content is core.data.unknown:
					content = "?"
				elif value.has_content:
					content = "1"
				else:
					content = "0"

		span.span[classes].div[:] = content

def gen_value(parent, diff, name):
	if diff:
		div = parent.div["value"]
		div.span["name"][:] = name
		gen_columns(div, diff)
		div.div["diff"][:] = diff

def gen_named_object_list(parent, diff, name=None):
	if diff:
		element = parent.div["list"]

		if name:
			element.div["head"].span["name"][:] = name

		for entry in diff.entries:
			kind, func = diff_types[type(entry.diff)]

			div = element.div["entry"]

			if entry.value:
				div.div["expander"][:] = "+"

			div.span["type"][:] = kind
			div.span["name"][:] = entry.name

			gen_columns(div, entry.value)

			if entry.value:
				children = div.div["children"]
				func(children, entry.diff)

def gen_ordered_object_list(parent, diff, name):
	if diff:
		element = parent.div["list"]

		head = element.div["head"]
		head.span["name"][:] = name

		table = element.table

		obis_by_group = []
		dbis_by_group = []

		for group in xrange(diff.groups):
			obis = []
			obis_by_group.append(obis)

			dbis = []
			dbis_by_group.append(dbis)

			for i, (o, g) in enumerate(diff.values):
				if g == group:
					obis.append(i)
					dbis.append(i)

		colors = get_colors(diff.values)

		tr = table.tr
		for color, group in enumerate(colors):
			dbis = dbis_by_group[group]
			dbns = [database_objects[i].get_name() for i in dbis]
			tr.th["color-%d" % color].div[:] = " ".join(dbns)

		def listlen(l):
			if l is None:
				return 0
			else:
				return len(l)

		if len(colors) == 2:
			lists = [diff.lists[obis_by_group[g][0]] for g in colors]
			gen_2column(table, *lists)
		else:
			for i in xrange(max([listlen(l) for l in diff.lists])):
				tr = table.tr
				for group in colors:
					obi = obis_by_group[group][0]
					lis = diff.lists[obi]
					if lis is None:
						print diff.lists
						print diff.values
					td = tr.td
					if i < len(lis):
						td.div[:] = dump_column(lis[i])

def dump_column(obj):
	s = "%s %s" % (obj.name, obj.type.name)
	if obj.notnull:
		s += " notnull"
	if obj.default:
		s += " %s" % obj.default
	return s

class NamedHash(object):
	def __init__(self, object):
		self.object = object

	def __hash__(self):
		return hash(self.object.name)

	def __eq__(self, other):
		return self.object.name == other.object.name

def gen_2column(table, seq1, seq2):
	hash1 = [NamedHash(o) for o in seq1]
	hash2 = [NamedHash(o) for o in seq2]
	match = difflib.SequenceMatcher(a=hash1, b=hash2)

	for tag, i1, i2, j1, j2 in match.get_opcodes():
		if tag == "delete":
			for obj in seq1[i1:i2]:
				tr = table.tr

				tr.td.div[:] = dump_column(obj)
				tr.td

		elif tag == "insert":
			for obj in seq2[j1:j2]:
				tr = table.tr

				tr.td
				tr.td.div[:] = dump_column(obj)

		elif tag in ("replace", "equal"):
			for n in xrange(i2 - i1):
				tr = table.tr

				if i1 + n < i2:
					obj1 = seq1[i1 + n]
					tr.td.div[:] = dump_column(obj1)
				else:
					tr.td

				if j1 + n < j2:
					obj2 = seq2[j1 + n]
					tr.td.div[:] = dump_column(obj2)
				else:
					tr.td

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
	global database_objects
	database_objects = diff.objects

	tree = tags.TagTree()
	gen_database(tree, diff)
	return tree.get_element_tree()
