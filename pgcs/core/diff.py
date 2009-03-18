import difflib

from . import data

def get_value(obj):
	return obj and obj.get_value()

class Diff(object):
	def __init__(self, l, r):
		self.objects = l, r

	def __str__(self):
		return str(self.objects)

class AnyDiff(Diff):
	def __nonzero__(self):
		for key, value in self.__dict__.iteritems():
			if key != "objects" and value:
				return True
		return False

class Value(Diff):
	def __nonzero__(self):
		l, r = self.objects
		return l != r

class ObjectValue(Diff):
	def __nonzero__(self):
		l, r = self.objects
		return get_value(l) != get_value(r)

class ObjectListValue(Diff):
	def __nonzero__(self):
		l, r = self.objects
		value1 = [get_value(obj) for obj in l]
		value2 = [get_value(obj) for obj in r]
		return value1 != value2

class DifferentTypes(Diff):
	pass

class BaseObjectList(list):
	def append_object_diff(list, obj1, obj2):
		if type(obj1) != type(obj2):
			diff = DifferentTypes(obj1, obj2)
		else:
			diff = diff_types[type(obj1)](obj1, obj2)

		if diff:
			list.append((obj1.name, 0, diff))

class NamedObjectList(BaseObjectList):
	def __init__(self, seq1, seq2):
		BaseObjectList.__init__(self)

		names = set()

		def map(seq):
			map = {}
			for obj in seq:
				names.add(obj.name)
				map[obj.name] = obj
			return map

		map1 = map(seq1)
		map2 = map(seq2)

		for name in sorted(names):
			obj1 = map1.get(name)
			obj2 = map2.get(name)

			if obj1 and obj2:
				self.append_object_diff(obj1, obj2)
			elif obj1:
				self.append((name, -1, obj1))
			elif obj2:
				self.append((name, +1, obj2))

class NamedHash(object):
	__slots__ = ["object"]

	def __init__(self, object):
		self.object = object

	def __hash__(self):
		return hash(self.object.name)

	def __eq__(self, other):
		return self.object.name == other.object.name

class OrderedObjectList(BaseObjectList):
	def __init__(self, seq1, seq2):
		BaseObjectList.__init__(self)

		hash1 = [NamedHash(o) for o in seq1]
		hash2 = [NamedHash(o) for o in seq2]
		match = difflib.SequenceMatcher(a=hash1, b=hash2)

		for tag, i1, i2, j1, j2 in match.get_opcodes():
			if tag in ("delete", "replace"):
				for obj in seq1[i1:i2]:
					self.append((obj.name, -1, obj))

			if tag in ("insert", "replace"):
				for obj in seq2[j1:j2]:
					self.append((obj.name, +1, obj))

			if tag == "equal":
				for n in xrange(i2 - i1):
					obj1 = seq1[i1 + n]
					obj2 = seq2[j1 + n]
					self.append_object_diff(obj1, obj2)

class IndexedObjectList(OrderedObjectList):
	def __init__(self, map1, map2):
		seq1 = [map1[i] for i in sorted(map1)]
		seq2 = [map2[i] for i in sorted(map2)]

		OrderedObjectList.__init__(self, seq1, seq2)

# Database

class Database(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.languages = NamedObjectList(l.languages, r.languages) or None
		self.namespaces = NamedObjectList(l.namespaces, r.namespaces) or None

# Language

class Language(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None

# Namespace

class Namespace(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None
		self.types = NamedObjectList(l.types, r.types) or None
		self.composites = NamedObjectList(l.composites, r.composites) or None
		self.indexes = NamedObjectList(l.indexes, r.indexes) or None
		self.tables = NamedObjectList(l.tables, r.tables) or None
		self.views = NamedObjectList(l.views, r.views) or None
		self.sequences = NamedObjectList(l.sequences, r.sequences) or None
		self.functions = NamedObjectList(l.functions, r.functions) or None
		self.operators = NamedObjectList(l.operators, r.operators) or None
		self.opclasses = NamedObjectList(l.opclasses, r.opclasses) or None

# Type

class Type(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None
		self.notnull = Value(l.notnull, r.notnull) or None
		self.default = Value(l.default, r.default) or None

class Domain(Type):
	def __init__(self, l, r):
		Type.__init__(self, l, r)
		self.basetype = ObjectValue(l.basetype, r.basetype) or None
		self.constraints = NamedObjectList(l.constraints, r.constraints) or None

# Function

class Function(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None
		self.language = ObjectValue(l.language, r.language) or None
		self.rettype = ObjectValue(l.rettype, r.rettype) or None
		self.argtypes = ObjectListValue(l.argtypes, r.argtypes) or None
		self.source1 = Value(l.source1, r.source1) or None
		self.source2 = Value(l.source2, r.source2) or None

# Relation

class Relation(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None
		self.columns = IndexedObjectList(l.columns, r.columns) or None

class Composite(Relation):
	pass

class Index(Relation):
	pass

class RuleRelation(Relation):
	def __init__(self, l, r):
		Relation.__init__(self, l, r)
		self.rules = NamedObjectList(l.rules, r.rules) or None

class Table(RuleRelation):
	def __init__(self, l, r):
		RuleRelation.__init__(self, l, r)
		self.triggers = NamedObjectList(l.triggers, r.triggers) or None
		self.constraints = NamedObjectList(l.constraints, r.constraints) or None

class View(RuleRelation):
	pass

# Sequence

class Sequence(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None
		self.increment = Value(l.increment, r.increment) or None
		self.minimum = Value(l.minimum, r.minimum) or None
		self.maximum = Value(l.maximum, r.maximum) or None

# Column

class Column(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.type = ObjectValue(l.type, r.type) or None
		self.notnull = Value(l.notnull, r.notnull) or None
		self.default = Value(l.default, r.default) or None

# Constraint

class Constraint(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.definition = Value(l.definition, r.definition) or None

class CheckConstraint(Constraint):
	pass

class UniqueConstraint(Constraint):
	pass

class ColumnConstraint(Constraint):
	def __init__(self, l, r):
		Constraint.__init__(self, l, r)
		self.columns = OrderedObjectList(l.columns, r.columns) or None

class CheckColumnConstraint(ColumnConstraint):
	pass

class UniqueColumnConstraint(ColumnConstraint):
	pass

class PrimaryKey(ColumnConstraint):
	pass

class ForeignKey(ColumnConstraint):
	def __init__(self, l, r):
		ColumnConstraint.__init__(self, l, r)
		self.foreign_table = ObjectValue(l.foreign_table, r.foreign_table) or None
		self.foreign_columns = OrderedObjectList(l.foreign_columns, r.foreign_columns) or None

# Trigger

class Trigger(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.function = ObjectValue(l.function, r.function) or None
		self.description = Value(l.description, r.description) or None

# Rule

class Rule(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.definition = Value(l.definition, r.definition) or None

# Operator

class Operator(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None

class OperatorClass(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.owner = Value(l.owner, r.owner) or None
		self.intype = ObjectValue(l.intype, r.intype) or None
		self.default = Value(l.default, r.default) or None
		self.keytype = ObjectValue(l.keytype, r.keytype) or None

diff_types = {
	data.CheckColumnConstraint: CheckColumnConstraint,
	data.CheckConstraint: CheckConstraint,
	data.Column: Column,
	data.Composite: Composite,
	data.Domain: Domain,
	data.ForeignKey: ForeignKey,
	data.Function: Function,
	data.Index: Index,
	data.Language: Language,
	data.Namespace: Namespace,
	data.Operator: Operator,
	data.OperatorClass: OperatorClass,
	data.PrimaryKey: PrimaryKey,
	data.Rule: Rule,
	data.Sequence: Sequence,
	data.Table: Table,
	data.Trigger: Trigger,
	data.Type: Type,
	data.UniqueColumnConstraint: UniqueColumnConstraint,
	data.UniqueConstraint: UniqueConstraint,
	data.View: View,
}

def diff_databases(*objects):
	return Database(*objects)
