import difflib
import functools

from . import data

different = object()

def similar(a, b):
	if a == b:
		return a
	else:
		return different

def xgetattr(obj, attr):
	if obj is None:
		return None
	else:
		return getattr(obj, attr)

def parse(objects, kwargs):
	if objects is None:
		(attr, objects), = kwargs.items()
		objects = [xgetattr(obj, attr) for obj in objects]
	return objects

class Value(object):
	def __init__(self, values=None, **kwargs):
		values = parse(values, kwargs)

		self.values = []

		prototypes = []

		for obj in values:
			group = -1

			if obj is not None:
				found = False

				for group in xrange(len(prototypes)):
					if obj == prototypes[group]:
						found = True
						break

				if not found:
					group = len(prototypes)
					prototypes.append(obj)

			self.values.append((obj, group))

		self.groups = len(prototypes)

	def __nonzero__(self):
		return self.groups > 1

class ObjectValue(Value):
	def __init__(self, objects=None, **kwargs):
		self.objects = parse(objects, kwargs)
		Value.__init__(self, [data.flatten(obj) for obj in self.objects])

class ObjectListValue(Value):
	def __init__(self, lists=None, **kwargs):
		def flatten_seq(seq):
			if seq is None:
				return None
			else:
				return [data.flatten(obj) for obj in seq]

		lists = parse(lists, kwargs)
		Value.__init__(self, [flatten_seq(seq) for seq in lists])

class OrderedObjectList(ObjectListValue):
	def __init__(self, lists=None, **kwargs):
		self.lists = parse(lists, kwargs)
		ObjectListValue.__init__(self, self.lists)

class IndexedObjectList(OrderedObjectList):
	def __init__(self, maps=None, **kwargs):
		def flatten_map(map):
			if map is None:
				return None
			else:
				return [map[i] for i in sorted(map)]

		maps = parse(maps, kwargs)
		OrderedObjectList.__init__(self, [flatten_map(map) for map in maps])

class Entry(object):
	def __init__(self, name, objects=None, **kwargs):
		self.name = name
		self.objects = parse(objects, kwargs)
		self.value = Value(objects)

		kind = None
		for obj in self.objects:
			if obj is not None:
				if kind is None:
					kind = type(obj)
				elif kind != type(obj):
					print "Diffing different object types not supported"
					kind = None
					break

		if kind:
			self.diff = diff_types[kind](self.objects)
		else:
			self.diff = None

	def __nonzero__(self):
		return functools.reduce(similar, self.objects) is different

class NamedObjectList(object):
	def __init__(self, _sequences=None, **kwargs):
		sequences = parse(_sequences, kwargs)

		self.entries = []

		names = set()

		def name_map(seq):
			map = {}
			for obj in seq or ():
				names.add(obj.name)
				map[obj.name] = obj
			return map

		maps = [name_map(seq) for seq in sequences]

		for name in sorted(names):
			entry = Entry(name, [map.get(name) for map in maps])
			if entry:
				self.entries.append(entry)

	def __nonzero__(self):
		return bool(self.entries)

class Any(object):
	def __init__(self, objects):
		self.objects = objects

	def __nonzero__(self):
		for key, value in self.__dict__.iteritems():
			if key != "objects" and value:
				return True
		return False

# Database

class Database(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.languages = NamedObjectList(languages=objects) or None
		self.namespaces = NamedObjectList(namespaces=objects) or None

# Language

class Language(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None

# Namespace

class Namespace(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None
		self.types = NamedObjectList(types=objects) or None
		self.composites = NamedObjectList(composites=objects) or None
		self.indexes = NamedObjectList(indexes=objects) or None
		self.tables = NamedObjectList(tables=objects) or None
		self.views = NamedObjectList(views=objects) or None
		self.sequences = NamedObjectList(sequences=objects) or None
		self.functions = NamedObjectList(functions=objects) or None
		self.operators = NamedObjectList(operators=objects) or None
		self.opclasses = NamedObjectList(opclasses=objects) or None

# Type

class Type(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None
		self.notnull = Value(notnull=objects) or None
		self.default = Value(default=objects) or None

class Domain(Type):
	def __init__(self, objects):
		Type.__init__(self, objects)
		self.basetype = ObjectValue(basetype=objects) or None
		self.constraints = NamedObjectList(constraints=objects) or None

# Function

class Function(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None
		self.language = ObjectValue(language=objects) or None
		self.rettype = ObjectValue(rettype=objects) or None
		self.argtypes = ObjectListValue(argtypes=objects) or None
		self.source1 = Value(source1=objects) or None
		self.source2 = Value(source2=objects) or None

# Relation

class Relation(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None
		self.columns = IndexedObjectList(columns=objects) or None

class Composite(Relation):
	pass

class Index(Relation):
	pass

class RuleRelation(Relation):
	def __init__(self, objects):
		Relation.__init__(self, objects)
		self.rules = NamedObjectList(rules=objects) or None

class Table(RuleRelation):
	def __init__(self, objects):
		RuleRelation.__init__(self, objects)
		self.triggers = NamedObjectList(triggers=objects) or None
		self.constraints = NamedObjectList(constraints=objects) or None

class View(RuleRelation):
	pass

# Sequence

class Sequence(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None
		self.increment = Value(increment=objects) or None
		self.minimum = Value(minimum=objects) or None
		self.maximum = Value(maximum=objects) or None

# Column

class Column(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.name = Value(name=objects) or None
		self.type = ObjectValue(type=objects) or None
		self.notnull = Value(notnull=objects) or None
		self.default = Value(default=objects) or None

# Constraint

class Constraint(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.definition = Value(definition=objects) or None

class CheckConstraint(Constraint):
	pass

class UniqueConstraint(Constraint):
	pass

class ColumnConstraint(Constraint):
	def __init__(self, objects):
		Constraint.__init__(self, objects)
		self.columns = OrderedObjectList(columns=objects) or None

class CheckColumnConstraint(ColumnConstraint):
	pass

class UniqueColumnConstraint(ColumnConstraint):
	pass

class PrimaryKey(ColumnConstraint):
	pass

class ForeignKey(ColumnConstraint):
	def __init__(self, objects):
		ColumnConstraint.__init__(self, objects)
		self.foreign_table = ObjectValue(foreign_table=objects) or None
		self.foreign_columns = OrderedObjectList(foreign_columns=objects) or None

# Trigger

class Trigger(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.function = ObjectValue(function=objects) or None
		self.description = Value(description=objects) or None

# Rule

class Rule(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.definition = Value(definition=objects) or None

# Operator

class Operator(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None

class OperatorClass(Any):
	def __init__(self, objects):
		Any.__init__(self, objects)
		self.owner = Value(owner=objects) or None
		self.intype = ObjectValue(intype=objects) or None
		self.default = Value(default=objects) or None
		self.keytype = ObjectValue(keytype=objects) or None

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

def diff_databases(objects):
	return Database(objects)
