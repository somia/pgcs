def typename(o):
	return repr(type(o)).split("'")[1].split(".")[2]

class NamedMixin(object):
	def __str__(self): return self.name

class NameOrderingMixin(NamedMixin):
	def __lt__(self, other): return self.name < other.name
	def __le__(self, other): return self.name <= other.name
	def __eq__(self, other): return self.name == other.name
	def __ne__(self, other): return self.name != other.name
	def __gt__(self, other): return self.name > other.name
	def __ge__(self, other): return self.name >= other.name
	def __hash__(self): return hash(self.name)

class ContainerMixin(object):
	def __init__(self):
		self.members = []

	def dump(self):
		for member in self.members:
			member.dump()

class Schema(ContainerMixin):
	__slots__ = ["members"]

class Language(NameOrderingMixin):
	__slots__ = ["name", "owner"]

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print "Language", self.name, self.owner

class Namespace(NameOrderingMixin, ContainerMixin):
	__slots__ = ["name", "owner", "members"]

	def __init__(self, *values):
		self.name, self.owner = values
		self.members = []

	def dump(self):
		print "Namespace", self.name, self.owner
		ContainerMixin.dump(self)

class Type(NameOrderingMixin):
	__slots__ = ["name", "owner", "notnull", "default"]

	def __init__(self, *values):
		self.name, self.owner, self.notnull, self.default = values

	def dump(self):
		print "  Type", self.name, self.owner,
		if self.default:
			print "default=" + self.default,
		print

class Domain(Type):
	__slots__ = Type.__slots__ + ["basetype", "constraints"]

	def __init__(self, *values):
		Type.__init__(self, *values)
		self.constraints = []

	def init_base(self, basetype):
		self.basetype = basetype

	def dump(self):
		print "  Domain", self.name, self.owner, self.basetype,
		if self.default:
			print "default=" + self.default,
		print
		for constraint in self.constraints:
			constraint.dump()

class Function(NameOrderingMixin):
	__slots__ = ["name", "owner", "language", "rettype", "argtypes"]

	def __init__(self, *values):
		self.name, self.owner, self.language, self.rettype, self.argtypes = values

	def dump(self):
		print "  Function", self.name, self.owner, self.language, self.rettype
		for type in self.argtypes:
			print "    Type", type

class Relation(NameOrderingMixin):
	__slots__ = ["name", "owner"]

	columns = None

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print " ", typename(self), self.name, self.owner

class ColumnRelation(Relation):
	__slots__ = Relation.__slots__ + ["columns"]

	def __init__(self, *values):
		Relation.__init__(self, *values)
		self.columns = {}

	def dump(self):
		Relation.dump(self)
		for column in self.columns.itervalues():
			column.dump()

class RuleRelation(ColumnRelation):
	__slots__ = ColumnRelation.__slots__ + ["rules"]

	def __init__(self, *values):
		ColumnRelation.__init__(self, *values)
		self.rules = []

	def dump(self):
		ColumnRelation.dump(self)
		for rule in self.rules:
			rule.dump()

class Sequence(Relation): pass
class Composite(ColumnRelation): pass
class Index(ColumnRelation): pass
class View(RuleRelation): pass

class Table(RuleRelation):
	__slots__ = RuleRelation.__slots__ + ["triggers", "constraints"]

	def __init__(self, *values):
		RuleRelation.__init__(self, *values)
		self.triggers = []
		self.constraints = []

	def dump(self):
		RuleRelation.dump(self)
		for trigger in self.triggers:
			trigger.dump()
		for constraint in self.constraints:
			constraint.dump()

class Column(NamedMixin):
	__slots__ = ["parent", "name", "type", "notnull", "default"]

	def __init__(self, *values):
		self.parent, self.name, self.type, self.notnull, self.default = values

	def dump(self):
		print "    Column", self.name, self.type,
		if self.notnull:
			print "notnull",
		if self.default:
			print "default=" + self.default,
		print

class Constraint(NameOrderingMixin):
	__slots__ = ["name", "definition"]

	def __init__(self, *values):
		self.name, self.definition = values

	def dump(self):
		print "   ", typename(self), self.name, self.definition

class CheckConstraint(Constraint): pass
class UniqueConstraint(Constraint): pass

class ColumnConstraint(Constraint):
	__slots__ = Constraint.__slots__ + ["columns"]

	def __init__(self, *values):
		self.name, self.definition, self.columns = values

	def dump(self):
		Constraint.dump(self)
		for column in self.columns:
			print "      Column", column

class CheckColumnConstraint(ColumnConstraint): pass
class UniqueColumnConstraint(ColumnConstraint): pass
class PrimaryKey(ColumnConstraint): pass

class ForeignKey(ColumnConstraint):
	__slots__ = ColumnConstraint.__slots__ + ["foreign_columns"]

	def __init__(self, *values):
		self.name, self.definition, self.columns, self.foreign_columns = values

	def dump(self):
		print "    ForeignKey", self.name, self.definition
		for column in self.columns:
			print "      Column", column
		for column in self.foreign_columns:
			print "      Column %s.%s" % (column.parent, column)

class Trigger(NameOrderingMixin):
	__slots__ = ["name", "function"]

	def __init__(self, *values):
		self.name, self.function = values

	def dump(self):
		print "    Trigger", self.name, self.function

class Rule(NameOrderingMixin):
	__slots__ = ["name"]

	def __init__(self, name):
		self.name = name

	def dump(self):
		print "    Rule", self.name

class Operator(NameOrderingMixin):
	__slots__ = ["name", "owner"]

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print "  Operator", self.name, self.owner

class OperatorClass(NameOrderingMixin):
	__slots__ = ["method", "name", "owner", "intype", "default", "keytype"]

	def __init__(self, *values):
		self.method, self.name, self.owner, self.intype, self.default, self.keytype \
			= values

	def dump(self):
		print "  OperatorClass", self.name, self.owner, self.intype,
		if self.default:
			print "default",
		if self.keytype is not None:
			print "key=%s" % self.keytype,
		print
