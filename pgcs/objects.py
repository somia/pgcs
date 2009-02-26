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

	def sort(self):
		self.members.sort(key=lambda member: (type(member), member))

	def dump(self):
		for member in self.members:
			member.dump()

class Schema(ContainerMixin):
	__slots__ = ("members",)

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

class EmptyRelation(NameOrderingMixin):
	__slots__ = ("name", "owner")

	columns = None

	def __init__(self, *values):
		self.name, self.owner = values

	def dump(self):
		print " ", repr(type(self)).split("'")[1].split(".")[2], self.name, self.owner

class Relation(EmptyRelation):
	__slots__ = ("name", "owner", "columns")

	def __init__(self, *values):
		EmptyRelation.__init__(self, *values)
		self.columns = []

	def dump(self):
		EmptyRelation.dump(self)
		for column in self.columns:
			column.dump()

class Composite(Relation): pass
class Index(Relation): pass
class Sequence(EmptyRelation): pass
class Table(Relation): pass
class View(Relation): pass

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
