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
	__slots__ = ("members",)

class Language(NameOrderingMixin):
	__slots__ = ("name", "owner")

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print "Language", self.name, self.owner

class Namespace(NameOrderingMixin, ContainerMixin):
	__slots__ = ("name", "owner", "members")

	def __init__(self, *values):
		self.name, self.owner = values
		self.members = []

	def dump(self):
		print "Namespace", self.name, self.owner
		ContainerMixin.dump(self)

class Type(NameOrderingMixin):
	__slots__ = ("name", "owner", "notnull")

	def __init__(self, *values):
		self.name, self.owner, self.notnull = values

	def dump(self):
		print "  Type", self.name, self.owner

class Function(NameOrderingMixin):
	__slots__ = ("name", "owner", "language")

	def __init__(self, *values):
		self.name, self.owner, self.language = values

	def dump(self):
		print "  Function", self.name, self.owner, self.language

class Relation(NameOrderingMixin):
	__slots__ = ("name", "owner")

	columns = None

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print " ", repr(type(self)).split("'")[1].split(".")[2], self.name, self.owner

class ColumnRelation(Relation):
	__slots__ = ("name", "owner", "columns")

	def __init__(self, *values):
		Relation.__init__(self, *values)
		self.columns = []

	def dump(self):
		Relation.dump(self)
		for column in self.columns:
			column.dump()

class RuleRelation(ColumnRelation):
	__slots__ = ("name", "owner", "columns", "rules")

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
	__slots__ = ("name", "owner", "columns", "rules", "triggers")

	def __init__(self, *values):
		RuleRelation.__init__(self, *values)
		self.triggers = []

	def dump(self):
		RuleRelation.dump(self)
		for trigger in self.triggers:
			trigger.dump()

class Column(NamedMixin):
	__slots__ = ("name", "type", "notnull", "default")

	def __init__(self, *values):
		self.name, self.type, self.notnull, self.default = values

	def dump(self):
		print "    Column", self.name, self.type,
		if self.notnull:
			print "notnull",
		if self.default:
			print "default=" + self.default,
		print

class Trigger(NameOrderingMixin):
	__slots__ = ("name", "function")

	def __init__(self, *values):
		self.name, self.function = values

	def dump(self):
		print "    Trigger", self.name, self.function

class Rule(NameOrderingMixin):
	__slots__ = ("name",)

	def __init__(self, name):
		self.name = name

	def dump(self):
		print "    Rule", self.name

class Operator(NameOrderingMixin):
	__slots__ = ("name", "owner")

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print "  Operator", self.name, self.owner

class OperatorClass(NameOrderingMixin):
	__slots__ = ("method", "name", "owner", "intype", "default", "keytype")

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
