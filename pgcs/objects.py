def typename(o):
	return repr(type(o)).split("'")[1].split(".")[2]

class NamedMixin(object):
	def __str__(self):
		return self.name

class TypeNameEqualityMixin(NamedMixin):
	def __eq__(self, other):
		return type(self) == type(other) and self.name == other.name

	def __ne__(self, other):
		return type(self) != type(other) or self.name != other.name

	def __hash__(self):
		return hash(self.name)

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

class Container(object):
	__slots__ = ["members"]

	def __init__(self):
		self.members = []

	def dump(self):
		for member in self.members:
			member.dump()

class Schema(Container): pass

class Language(XReferee, TypeNameEqualityMixin):
	__slots__ = XReferee.__slots__ + ["name", "owner"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.owner = values

	def dump(self):
		print "Language", self.name, self.owner

class Namespace(Container, TypeNameEqualityMixin):
	__slots__ = Container.__slots__ + ["name", "owner"]

	def __init__(self, *values):
		Container.__init__(self)
		self.name, self.owner = values

	def dump(self):
		print "Namespace", self.name, self.owner
		Container.dump(self)

class Type(XReferee, TypeNameEqualityMixin):
	__slots__ = XReferee.__slots__ + ["name", "owner", "notnull", "default"]

	def __init__(self, *values):
		XReferee.__init__(self)
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
		xref(self, self.basetype)

	def dump(self):
		print "  Domain", self.name, self.owner, self.basetype,
		if self.default:
			print "default=" + self.default,
		print
		for constraint in self.constraints:
			constraint.dump()

class Function(XReferee, TypeNameEqualityMixin):
	__slots__ = XReferee.__slots__ + ["name", "owner", "language", "rettype", "argtypes",
	                                  "source1", "source2"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.owner, self.language, self.rettype, self.argtypes, \
			self.source1, self.source2 = values
		xref(self, self.language)
		xref(self, self.rettype)
		xref(self, self.argtypes)

	def dump(self):
		print "  Function", self.name, self.owner, self.language, self.rettype
		for type in self.argtypes:
			print "    Type", type
		lines = self.source1.split("\n")
		while lines and not lines[0]:
			del lines[0]
		while lines and not lines[-1]:
			del lines[-1]
		print "    Source1", lines[0]
		for line in lines[1:]:
			print "           ", line
		print "    Source2", self.source2

class Relation(XReferee, TypeNameEqualityMixin):
	__slots__ = XReferee.__slots__ + ["name", "owner", "columns"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.owner = values
		self.columns = {}

	def dump(self):
		print " ", typename(self), self.name, self.owner
		for column in self.columns.itervalues():
			column.dump()

class RuleRelation(Relation):
	__slots__ = Relation.__slots__ + ["rules"]

	def __init__(self, *values):
		Relation.__init__(self, *values)
		self.rules = []

	def dump(self):
		Relation.dump(self)
		for rule in self.rules:
			rule.dump()

class Composite(Relation): pass
class Index(Relation): pass
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

class Sequence(TypeNameEqualityMixin):
	__slots__ = ["name", "owner", "increment", "minimum", "maximum"]

	def __init__(self, *values):
		self.name, self.owner = values

	def init_values(self, *values):
		self.increment, self.minimum, self.maximum = values

	def dump(self):
		print "  Sequence", self.name, self.owner, self.increment, self.minimum, \
			self.maximum

class Column(XReferee, NamedMixin):
	__slots__ = XReferee.__slots__ + ["name", "type", "notnull", "default"]

	def __init__(self, *values):
		XReferee.__init__(self)
		self.name, self.type, self.notnull, self.default = values
		xref(self, self.type)

	def dump(self):
		print "    Column", self.name, self.type,
		if self.notnull:
			print "notnull",
		if self.default:
			print "default=" + self.default,
		print

class Constraint(TypeNameEqualityMixin):
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
		xref(self, self.columns)

	def dump(self):
		Constraint.dump(self)
		for column in self.columns:
			print "      Column", column

class CheckColumnConstraint(ColumnConstraint): pass
class UniqueColumnConstraint(ColumnConstraint): pass
class PrimaryKey(ColumnConstraint): pass

class ForeignKey(ColumnConstraint):
	__slots__ = ColumnConstraint.__slots__ + ["foreign_table", "foreign_columns"]

	def __init__(self, *values):
		self.name, self.definition, self.columns, self.foreign_table, \
			self.foreign_columns = values
		xref(self, self.foreign_table)
		xref(self, self.foreign_columns)

	def dump(self):
		print "    ForeignKey", self.name, self.definition
		for column in self.columns:
			print "      Column", column
		print "      Table", self.foreign_table
		for column in self.foreign_columns:
			print "        Column %s" % column

class Trigger(TypeNameEqualityMixin):
	__slots__ = ["name", "function", "description"]

	def __init__(self, *values):
		self.name, self.function, self.description = values
		xref(self, self.function)

	def dump(self):
		print "    Trigger", self.name, self.function, self.description

class Rule(TypeNameEqualityMixin):
	__slots__ = ["name", "definition"]

	def __init__(self, *values):
		self.name, self.definition = values

	def dump(self):
		print "    Rule", self.name, self.definition

class Operator(TypeNameEqualityMixin):
	__slots__ = ["name", "owner"]

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print "  Operator", self.name, self.owner

class OperatorClass(TypeNameEqualityMixin):
	__slots__ = ["method", "name", "owner", "intype", "default", "keytype"]

	def __init__(self, *values):
		self.method, self.name, self.owner, self.intype, self.default, self.keytype \
			= values
		xref(self, self.intype)
		xref(self, self.keytype)

	def dump(self):
		print "  OperatorClass", self.name, self.owner, self.intype,
		if self.default:
			print "default",
		if self.keytype is not None:
			print "key=%s" % self.keytype,
		print
