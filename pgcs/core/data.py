class XReferee(object):
	__slots__ = ["xrefs"]

	def __init__(self):
		self.xrefs = set()

def xref(source, target):
	if isinstance(target, (tuple, list, set)):
		for t in target:
			t.xrefs.add(source)
	elif target is not None:
		target.xrefs.add(source)

def flatten(obj):
	return obj and obj.flatten()

# Database

class Database(object):
	__slots__ = ["source", "languages", "namespaces"]

	def __init__(self, source):
		self.source = source
		self.languages = []
		self.namespaces = []

	def get_name(self):
		for token in self.source.split():
			key, value = token.split("=", 1)
			if key == "dbname":
				return value

		raise Exception("No dbname in DSN string")

# Language

class Language(XReferee):
	__slots__ = XReferee.__slots__ + ["name", "owner"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.owner = values

	def flatten(self):
		return self.name

# Namespace

class Namespace(object):
	__slots__ = ["name", "owner", "types", "composites", "indexes", "tables", "views",
	             "sequences", "functions", "operators", "opclasses"]

	def __init__(self, *values):
		self.name, self.owner = values
		self.types = []
		self.composites = []
		self.indexes = []
		self.tables = []
		self.views = []
		self.sequences = []
		self.functions = []
		self.operators = []
		self.opclasses = []

	def flatten(self):
		return self.name

# Type

class Type(XReferee):
	__slots__ = XReferee.__slots__ + ["namespace", "name", "owner", "notnull", "default"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.namespace, self.name, self.owner, self.notnull, self.default = values

	def flatten(self):
		return self.namespace.name, self.name

class Domain(Type):
	__slots__ = Type.__slots__ + ["basetype", "constraints"]

	def __init__(self, *values):
		Type.__init__(self, *values)
		self.constraints = []

	def init_base(self, basetype):
		self.basetype = basetype
		xref(self, self.basetype)

# Function

class Function(XReferee):
	__slots__ = XReferee.__slots__ + ["namespace", "name", "owner", "language", "rettype",
	                                  "argtypes", "source1", "source2"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.namespace, self.name, self.owner, self.language, self.rettype, \
			self.argtypes, self.source1, self.source2 = values
		xref(self, self.language)
		xref(self, self.rettype)
		xref(self, self.argtypes)

	def flatten(self):
		return self.namespace.name, self.name

# Relation

class Relation(XReferee):
	__slots__ = XReferee.__slots__ + ["namespace", "name", "owner", "columns"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.namespace, self.name, self.owner = values
		self.columns = {}

	def flatten(self):
		return self.namespace.name, self.name

class Composite(Relation):
	pass

class Index(Relation):
	pass

class RuleRelation(Relation):
	__slots__ = Relation.__slots__ + ["rules"]

	def __init__(self, *values):
		Relation.__init__(self, *values)
		self.rules = []

class Table(RuleRelation):
	__slots__ = RuleRelation.__slots__ + ["triggers", "constraints"]

	def __init__(self, *values):
		RuleRelation.__init__(self, *values)
		self.triggers = []
		self.constraints = []

class View(RuleRelation):
	pass

# Sequence

class Sequence(object):
	__slots__ = ["namespace", "name", "owner", "increment", "minimum", "maximum"]

	def __init__(self, *values):
		self.namespace, self.name, self.owner = values
		self.increment = None
		self.minimum = None
		self.maximum = None

	def init_values(self, *values):
		self.increment, self.minimum, self.maximum = values

	def flatten(self):
		return self.namespace.name, self.name

# Column

class Column(XReferee):
	__slots__ = XReferee.__slots__ + ["name", "type", "notnull", "default"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.type, self.notnull, self.default = values
		xref(self, self.type)

	def __eq__(self, other):
		return self.name == other.name and flatten(self.type) == flatten(other.type) and \
		       self.notnull == other.notnull and self.default == other.default

	def __hash__(self):
		return hash(self.name) ^ hash(flatten(self.type)) ^ hash(self.notnull) ^ \
		       hash(self.default)

	def flatten(self):
		return self.name

# Constraint

class Constraint(object):
	__slots__ = ["name", "definition"]

	def __init__(self, *values):
		self.name, self.definition = values

	def flatten(self):
		return self.name

class CheckConstraint(Constraint):
	pass

class UniqueConstraint(Constraint):
	pass

class ColumnConstraint(Constraint):
	__slots__ = Constraint.__slots__ + ["columns"]

	def __init__(self, *values):
		self.name, self.definition, self.columns = values
		xref(self, self.columns)

class CheckColumnConstraint(ColumnConstraint):
	pass

class UniqueColumnConstraint(ColumnConstraint):
	pass

class PrimaryKey(ColumnConstraint):
	pass

class ForeignKey(ColumnConstraint):
	__slots__ = ColumnConstraint.__slots__ + ["foreign_table", "foreign_columns"]

	def __init__(self, *values):
		self.name, self.definition, self.columns, self.foreign_table, \
			self.foreign_columns = values
		xref(self, self.foreign_table)
		xref(self, self.foreign_columns)

# Trigger

class Trigger(object):
	__slots__ = ["name", "function", "description"]

	def __init__(self, *values):
		self.name, self.function, self.description = values
		xref(self, self.function)

	def flatten(self):
		return self.name

# Rule

class Rule(object):
	__slots__ = ["name", "definition"]

	def __init__(self, *values):
		self.name, self.definition = values

	def flatten(self):
		return self.name

# Operator

class Operator(object):
	__slots__ = ["namespace", "name", "owner"]

	def __init__(self, *values):
		self.namespace, self.name, self.owner = values

	def flatten(self):
		return self.namespace.name, self.name

class OperatorClass(object):
	__slots__ = ["namespace", "method", "name", "owner", "intype", "default", "keytype"]

	def __init__(self, *values):
		self.namespace, self.method, self.name, self.owner, self.intype, self.default, \
			self.keytype = values
		xref(self, self.intype)
		xref(self, self.keytype)

	def flatten(self):
		return self.namespace.name, self.method, self.name
