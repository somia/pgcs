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
		"S": objects.Sequence,
		"c": objects.Composite,
		"i": objects.Index,
		"r": objects.Table,
		"t": objects.Table,
		"v": objects.View,
	}

	roles = {}
	languages = {}
	namespaces = {}
	types = {}
	relations = {}

	cursor.execute("SET search_path = pg_catalog")

	cursor.execute("SELECT oid, rolname FROM pg_roles")
	for row in cursor:
		oid, name = row
		roles[oid] = name

	cursor.execute("SELECT oid, lanname, lanowner, lanispl FROM pg_language")
	for row in cursor:
		oid, name, owner_oid, userdefined = row
		language = objects.Language(name, roles[owner_oid])
		languages[oid] = language
		if userdefined:
			schema.members.append(language)

	cursor.execute("SELECT oid, nspname, nspowner FROM pg_namespace")
	for row in cursor:
		oid, name, owner_oid = row
		namespace = objects.Namespace(name, roles[owner_oid])
		namespaces[oid] = namespace
		if not name.startswith("pg_"):
			schema.members.append(namespace)

	# TODO: domain basetype etc.
	cursor.execute("SELECT oid, typname, typnamespace, typowner, typnotnull FROM pg_type")
	for row in cursor:
		oid, name, namespace_oid, owner_oid, notnull = row
		type = objects.Type(name, roles[owner_oid], notnull)
		types[oid] = type
		namespaces[namespace_oid].members.append(type)

	cursor.execute("SELECT oid, relname, relowner, relnamespace, relkind FROM pg_class")
	for row in cursor:
		oid, name, owner_oid, namespace_oid, kind = row
		relation = relation_types[kind](name, roles[owner_oid])
		relations[oid] = relation
		namespaces[namespace_oid].members.append(relation)

	cursor.execute("""SELECT attrelid, attname, atttypid, attnotnull, adbin FROM pg_attribute
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE attnum > 0 AND NOT attisdropped ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, notnull, default = row
		columns = relations[relation_oid].columns
		if columns is not None:
			column = objects.Column(name, types[type_oid], notnull, default)
			columns.append(column)

	# TODO: functions
	# TODO: operators, operator classes
	# TODO: rules
	# TODO: triggers
