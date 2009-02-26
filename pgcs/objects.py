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

class Schema(object):
	def __init__(self):
		self.namespaces = {}
		self.types = {}
		self.relations = {}

	def sort(self):
		for namespace in self.namespaces.itervalues():
			namespace.sort()

	def dump(self):
		for namespace in sorted(self.namespaces.values()):
			namespace.dump()

class Namespace(NameOrderingMixin):
	__slots__ = ("oid", "name", "members")

	def __init__(self, *values):
		self.oid, self.name = values
		self.members = []

	def sort(self):
		self.members.sort()

	def dump(self):
		print "Namespace", self.name
		for member in self.members:
			member.dump()

class Type(NameOrderingMixin):
	# TODO: domain basetype etc.
	__slots__ = ("oid", "name", "notnull")

	def __init__(self, *values):
		self.oid, self.name, self.notnull = values

	def dump(self):
		print "  Type", self.name

class Relation(NameOrderingMixin):
	__slots__ = ("oid", "name", "columns")

	def __init__(self, *values):
		self.oid, self.name = values
		self.columns = []

	def dump(self):
		print " ", repr(type(self)).split("'")[1].split(".")[2], self.name
		for column in self.columns:
			column.dump()

class Table(Relation): pass
class View(Relation): pass
class Index(Relation): pass
class Sequence(Relation): pass
class Composite(Relation): pass

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
