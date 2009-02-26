import sys
from contextlib import closing

import psycopg2
import psycopg2.extensions

class NameOrderMixin(object):
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
		self.relations = {}
		self.types = {}

	def sort(self):
		for namespace in self.namespaces.itervalues():
			namespace.sort()

	def dump(self):
		for namespace in sorted(self.namespaces.values()):
			namespace.dump()

class Namespace(NameOrderMixin):
	__slots__ = ("oid", "name", "children")

	def __init__(self, *values):
		self.oid, self.name = values
		self.children = []

	def sort(self):
		self.children.sort()

	def dump(self):
		print "Namespace", self.name
		for child in self.children:
			child.dump()

class Type(NameOrderMixin):
	__slots__ = ("oid", "name", "notnull")

	def __init__(self, *values):
		self.oid, self.name, self.notnull = values

	def dump(self):
		print "  Type", self.name

class Relation(NameOrderMixin):
	__slots__ = ("oid", "name", "columns")

	def __init__(self, *values):
		self.oid, self.name = values
		self.columns = []

	def dump(self):
		print " ", repr(type(self)).split("'")[1].split(".")[1], self.name
		for column in self.columns:
			column.dump()

class Table(Relation): pass
class View(Relation): pass
class Index(Relation): pass
class Sequence(Relation): pass
class Composite(Relation): pass

class Column(object):
	__slots__ = ("name", "type", "notnull", "default")

	def __init__(self, *values):
		self.name, self.type, self.notnull, self.default = values

	def dump(self):
		print "    Column", self.name, self.type,
		if self.notnull:
			print "notnull",
		if self.default:
			print "default",
		print

def load_schema(cursor):
	relation_types = {
		"r": Table,
		"t": Table,
		"v": View,
		"i": Index,
		"S": Sequence,
		"c": Composite,
	}

	schema = Schema()

	cursor.execute("SET search_path = pg_catalog")

	cursor.execute("SELECT oid, nspname FROM pg_namespace")
	for row in cursor:
		oid, name = row
		schema.namespaces[oid] = Namespace(oid, name)

	cursor.execute("SELECT oid, typname, typnamespace, typnotnull FROM pg_type")
	for row in cursor:
		oid, name, namespace_oid, notnull = row
		type = Type(oid, name, notnull)
		schema.types[oid] = type
		schema.namespaces[namespace_oid].children.append(type)

	cursor.execute("""SELECT oid, relname, relnamespace, relkind FROM pg_class""")
	for row in cursor:
		oid, name, namespace_oid, kind = row
		relation = relation_types[kind](oid, name)
		schema.relations[oid] = relation
		schema.namespaces[namespace_oid].children.append(relation)

	cursor.execute("""SELECT attrelid, attname, atttypid, attnotnull, adbin FROM pg_attribute
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE attnum > 0 AND NOT attisdropped ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, notnull, default = row
		column = Column(name, type_oid, notnull, default)
		schema.relations[relation_oid].columns.append(column)

	schema.sort()

	return schema

def main():
	datasource, = sys.argv[1:]

	with closing(psycopg2.connect(datasource)) as conn:
		conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
		with closing(conn.cursor()) as cursor:
			schema = load_schema(cursor)

	schema.dump()

if __name__ == "__main__":
	main()
