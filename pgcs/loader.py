import contextlib

from . import objects

def get_schema(conn):
	schema = objects.Schema()

	with contextlib.closing(conn.cursor()) as cursor:
		populate_schema(schema, cursor)

	schema.sort()

	return schema

def populate_schema(schema, cursor):
	relation_types = {
		"r": objects.Table,
		"t": objects.Table,
		"v": objects.View,
		"i": objects.Index,
		"S": objects.Sequence,
		"c": objects.Composite,
	}

	cursor.execute("SET search_path = pg_catalog")

	cursor.execute("SELECT oid, nspname FROM pg_namespace")
	for row in cursor:
		oid, name = row
		schema.namespaces[oid] = objects.Namespace(oid, name)

	cursor.execute("SELECT oid, typname, typnamespace, typnotnull FROM pg_type")
	for row in cursor:
		oid, name, namespace_oid, notnull = row
		type = objects.Type(oid, name, notnull)
		schema.types[oid] = type
		schema.namespaces[namespace_oid].members.append(type)

	cursor.execute("SELECT oid, relname, relnamespace, relkind FROM pg_class")
	for row in cursor:
		oid, name, namespace_oid, kind = row
		relation = relation_types[kind](oid, name)
		schema.relations[oid] = relation
		schema.namespaces[namespace_oid].members.append(relation)

	cursor.execute("""SELECT attrelid, attname, atttypid, attnotnull, adbin FROM pg_attribute
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE attnum > 0 AND NOT attisdropped ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, notnull, default = row
		column = objects.Column(name, schema.types[type_oid], notnull, default)
		schema.relations[relation_oid].columns.append(column)
