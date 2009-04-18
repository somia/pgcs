FLAG_VALUE   = 0x0
FLAG_OBJECT  = 0x1
FLAG_LIST    = 0x2
FLAG_DICT    = 0x4
FLAG_KEY     = 0x8

class Data(object):
	def __init__(self):
		for name, flags in self.value_info:
			if flags & FLAG_LIST:
				setattr(self, name, [])
			elif flags & FLAG_DICT:
				setattr(self, name, {})
			else:
				# TODO: use __slots__ instead
				setattr(self, name, None)

		self.__hashcode = None
		self.__flat = None

	def __eq__(self, other):
		if other is None or not isinstance(other, Data):
			return False

		for name, flags in self.value_info:
			value1 = getattr(self, name)
			value2 = getattr(other, name)

			if flags & FLAG_OBJECT:
				if flags & FLAG_LIST:
					value1 = [flatten(o) for o in value1]
					value2 = [flatten(o) for o in value2]
				elif flags & FLAG_DICT:
					value1 = [flatten(o) for o in value1.values()]
					value2 = [flatten(o) for o in value2.values()]
				else:
					value1 = flatten(value1)
					value2 = flatten(value2)
			elif flags & FLAG_DICT:
				value1 = value1.values()
				value2 = value2.values()

			if value1 != value2:
				return False

		return True

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		if self.__hashcode is None:
			hashcode = 0

			for name, flags in self.value_info:
				value = getattr(self, name)
				value = self.__freeze(value, flags)
				hashcode ^= hash(value)

			self.__hashcode = hashcode

		return self.__hashcode

	def flatten(self):
		if self.__flat is None:
			flat = []

			for name, flags in self.value_info:
				if flags & FLAG_KEY:
					value = getattr(self, name)
					value = self.__freeze(value, flags)
					flat.append(value)

			self.__flat = tuple(flat)

		return self.__flat

	@staticmethod
	def __freeze(value, flags):
		if flags & FLAG_OBJECT:
			filter = flatten
		else:
			def filter(value):
				return value

		if flags & FLAG_LIST:
			value = tuple([filter(o) for o in value])
		elif flags & FLAG_DICT:
			value = tuple([filter(o) for o in value.values()])
		else:
			value = filter(value)

		return value

class XReferee(Data):
	def __init__(self):
		Data.__init__(self)
		self.xrefs = set()

def xref(source, target):
	if isinstance(target, (tuple, list, set)):
		for t in target:
			t.xrefs.add(source)
	elif target is not None:
		target.xrefs.add(source)

def flatten(data):
	return data and data.flatten()

# Database

class Database(Data):
	value_info = [
		("source",      FLAG_VALUE),
		("languages",   FLAG_OBJECT | FLAG_LIST),
		("namespaces",  FLAG_OBJECT | FLAG_LIST),
	]

	def __init__(self, source):
		Data.__init__(self)
		self.source = source

	def get_name(self):
		for token in self.source.split():
			key, value = token.split("=", 1)
			if key == "dbname":
				return value

		raise Exception("No dbname in DSN string")

# Language

class Language(XReferee):
	value_info = [
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
	]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.owner = values

# Namespace

class Namespace(Data):
	value_info = [
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
		("types",       FLAG_OBJECT | FLAG_LIST),
		("composites",  FLAG_OBJECT | FLAG_LIST),
		("indexes",     FLAG_OBJECT | FLAG_LIST),
		("tables",      FLAG_OBJECT | FLAG_LIST),
		("views",       FLAG_OBJECT | FLAG_LIST),
		("sequences",   FLAG_OBJECT | FLAG_LIST),
		("functions",   FLAG_OBJECT | FLAG_LIST),
		("operators",   FLAG_OBJECT | FLAG_LIST),
		("opclasses",   FLAG_OBJECT | FLAG_LIST),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.name, self.owner = values

# Type

class Type(XReferee):
	value_info = [
		("namespace",   FLAG_OBJECT | FLAG_KEY),
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
		("notnull",     FLAG_VALUE),
		("default",     FLAG_VALUE),
	]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.namespace, self.name, self.owner, self.notnull, self.default = values

class Domain(Type):
	value_info = Type.value_info + [
		("basetype",    FLAG_OBJECT),
		("constraints", FLAG_OBJECT | FLAG_LIST),
	]

	def __init__(self, *values):
		Type.__init__(self, *values)

	def init_base(self, basetype):
		self.basetype = basetype
		xref(self, self.basetype)

# Function

class Function(XReferee):
	value_info = [
		("namespace",   FLAG_OBJECT | FLAG_KEY),
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
		("language",    FLAG_OBJECT),
		("rettype",     FLAG_OBJECT),
		("argtypes",    FLAG_OBJECT | FLAG_LIST),
		("source1",     FLAG_VALUE),
		("source2",     FLAG_VALUE),
	]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.namespace, self.name, self.owner, self.language, self.rettype, \
			self.argtypes, self.source1, self.source2 = values
		xref(self, self.language)
		xref(self, self.rettype)
		xref(self, self.argtypes)

# Relation

class Relation(XReferee):
	value_info = [
		("namespace",   FLAG_OBJECT | FLAG_KEY),
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
		("columns",     FLAG_OBJECT | FLAG_DICT),
	]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.namespace, self.name, self.owner = values

class Composite(Relation):
	pass

class Index(Relation):
	pass

class RuleRelation(Relation):
	value_info = Relation.value_info + [
		("rules",       FLAG_OBJECT | FLAG_LIST),
	]

class Table(RuleRelation):
	value_info = RuleRelation.value_info + [
		("triggers",    FLAG_OBJECT | FLAG_LIST),
		("constraints", FLAG_OBJECT | FLAG_LIST),
	]

	def __init__(self, *values):
		RuleRelation.__init__(self, *values)
		self.has_content = None

	def init_content(self, has_content):
		self.has_content = has_content

class View(RuleRelation):
	pass

# Sequence

class Sequence(Data):
	value_info = [
		("namespace",   FLAG_OBJECT | FLAG_KEY),
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
		("increment",   FLAG_VALUE),
		("minimum",     FLAG_VALUE),
		("maximum",     FLAG_VALUE),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.namespace, self.name, self.owner = values

	def init_values(self, *values):
		self.increment, self.minimum, self.maximum = values

# Column

class Column(XReferee):
	value_info = [
		("name",        FLAG_VALUE  | FLAG_KEY),
		("type",        FLAG_OBJECT),
		("notnull",     FLAG_VALUE),
		("default",     FLAG_VALUE),
	]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.type, self.notnull, self.default = values
		xref(self, self.type)

# Constraint

class Constraint(Data):
	value_info = [
		("name",        FLAG_VALUE  | FLAG_KEY),
		("definition",  FLAG_VALUE),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.name, self.definition = values

class CheckConstraint(Constraint):
	pass

class UniqueConstraint(Constraint):
	pass

class ColumnConstraint(Constraint):
	value_info = Constraint.value_info + [
		("columns",     FLAG_OBJECT | FLAG_LIST),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.name, self.definition, self.columns = values
		xref(self, self.columns)

class CheckColumnConstraint(ColumnConstraint):
	pass

class UniqueColumnConstraint(ColumnConstraint):
	pass

class PrimaryKey(ColumnConstraint):
	pass

class ForeignKey(ColumnConstraint):
	value_info = ColumnConstraint.value_info + [
		("foreign_table",   FLAG_OBJECT),
		("foreign_columns", FLAG_OBJECT | FLAG_LIST),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.name, self.definition, self.columns, self.foreign_table, \
			self.foreign_columns = values
		xref(self, self.foreign_table)
		xref(self, self.foreign_columns)

# Trigger

class Trigger(Data):
	value_info = [
		("name",        FLAG_VALUE  | FLAG_KEY),
		("function",    FLAG_OBJECT),
		("description", FLAG_VALUE),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.name, self.function, self.description = values
		xref(self, self.function)

# Rule

class Rule(Data):
	value_info = [
		("name",        FLAG_VALUE  | FLAG_KEY),
		("definition",  FLAG_VALUE),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.name, self.definition = values

# Operator

class Operator(Data):
	value_info = [
		("namespace",   FLAG_OBJECT | FLAG_KEY),
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.namespace, self.name, self.owner = values

class OperatorClass(Data):
	value_info = [
		("namespace",   FLAG_OBJECT | FLAG_KEY),
		("method",      FLAG_VALUE  | FLAG_KEY),
		("name",        FLAG_VALUE  | FLAG_KEY),
		("owner",       FLAG_VALUE),
		("intype",      FLAG_OBJECT),
		("default",     FLAG_VALUE),
		("keytype",     FLAG_OBJECT),
	]

	def __init__(self, *values):
		Data.__init__(self)
		self.namespace, self.method, self.name, self.owner, self.intype, \
			self.default, self.keytype = values
		xref(self, self.intype)
		xref(self, self.keytype)
