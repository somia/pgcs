from . import objects

class Diff(object):
	def __init__(self, l, r):
		self.objects = l, r

	def __str__(self):
		return str(self.objects)

class AnyDiff(Diff):
	def __nonzero__(self):
		return any(self.__dict__.itervalues())

class Value(Diff):
	def __nonzero__(self):
		l, r = self.objects
		return l != r

class ObjectValue(Diff):
	def __nonzero__(self):
		l, r = self.objects
		return l.get_value() != r.get_value()

class ObjectListValue(Diff):
	def __nonzero__(self):
		l, r = self.objects
		value1 = [obj.get_value() for obj in l]
		value2 = [obj.get_value() for obj in r]
		return value1 != value2

class DifferentTypes(Diff):
	pass

class NamedObjectList(list):
	def __init__(self, seq1, seq2):
		list.__init__(self)

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
				if type(obj1) != type(obj2):
					diff = DifferentTypes(obj1, obj2)
				else:
					diff = diff_types[type(obj1)](obj1, obj2)

				if diff:
					self.append((name, 0, diff))

			elif obj1:
				self.append((name, -1, obj1))

			elif obj2:
				self.append((name, +1, obj2))

# Schema

class Schema(AnyDiff):
	def __init__(self, l, r):
		AnyDiff.__init__(self, l, r)
		self.languages = NamedObjectList(l.languages, r.languages) or None
		self.namespaces = NamedObjectList(l.namespaces, r.namespaces) or None

	def __nonzero__(self):
		return bool(self.languages or self.namespaces)

# Language

class Language(AnyDiff):
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner) or None

# Namespace

class Namespace(AnyDiff):
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner) or None
		self.types = NamedObjectList(l.types, r.types) or None
		self.composites = NamedObjectList(l.composites, r.composites) or None
		self.indexes = NamedObjectList(l.indexes, r.indexes) or None
		self.tables = NamedObjectList(l.tables, r.tables) or None
		self.views = NamedObjectList(l.views, r.views) or None
		self.sequences = NamedObjectList(l.sequences, r.sequences) or None
		self.functions = NamedObjectList(l.functions, r.functions) or None
		# TODO: operators
		# TODO: opclasses

# Type

class Type(AnyDiff):
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner) or None
		self.notnull = Value(l.notnull, r.notnull) or None
		self.default = Value(l.default, r.default) or None

class Domain(Type):
	def __init__(self, l, r):
		Type.__init__(self, l, r)
		self.basetype = ObjectValue(l.basetype, r.basetype) or None
		# TODO: domain constraints

# Function

class Function(AnyDiff):
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner) or None
		self.language = ObjectValue(l.language, r.language) or None
		self.rettype = ObjectValue(l.rettype, r.rettype) or None
		self.argtypes = ObjectListValue(l.argtypes, r.argtypes) or None
		self.source1 = Value(l.source1, r.source1) or None
		self.source2 = Value(l.source2, r.source2) or None

# Relation

class Relation(AnyDiff):
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner) or None
		# TODO: columns

class Composite(Relation):
	pass

class Index(Relation):
	pass

class RuleRelation(Relation):
	def __init__(self, l, r):
		Relation.__init__(self, l, r)
		# TODO: rules

class Table(RuleRelation):
	def __init__(self, l, r):
		RuleRelation.__init__(self, l, r)
		# TODO: triggers
		# TODO: table constraints

class View(RuleRelation):
	pass

# Sequence

class Sequence(AnyDiff):
	def __init__(self, l, r):
		self.owner = Value(l.owner, r.owner) or None
		self.increment = Value(l.increment, r.increment) or None
		self.minimum = Value(l.minimum, r.minimum) or None
		self.maximum = Value(l.maximum, r.maximum) or None

diff_types = {
	objects.Composite: Composite,
	objects.Domain: Domain,
	objects.Function: Function,
	objects.Index: Index,
	objects.Language: Language,
	objects.Namespace: Namespace,
	objects.Sequence: Sequence,
	objects.Table: Table,
	objects.Type: Type,
	objects.View: View,
}

def diff_schemas(*schemas):
	return Schema(*schemas)
