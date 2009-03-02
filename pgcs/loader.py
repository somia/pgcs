import contextlib

from . import objects

def get_schema(conn):
	schema = objects.Schema()

	with contextlib.closing(conn.cursor()) as cursor:
		populate_schema(schema, cursor)

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
	functions = {}
	operators = {}
	opclasses = {}

	cursor.execute("""SET search_path TO pg_catalog""")

	cursor.execute("""SELECT oid, rolname
	                  FROM pg_roles""")
	for row in cursor:
		oid, name = row
		roles[oid] = name

	cursor.execute("""SELECT oid, lanname, lanowner, lanispl
	                  FROM pg_language
	                  ORDER BY lanname""")
	for row in cursor:
		oid, name, owner_oid, userdefined = row
		language = objects.Language(name, roles[owner_oid])
		languages[oid] = language
		if userdefined:
			schema.members.append(language)

	cursor.execute("""SELECT oid, nspname, nspowner
	                  FROM pg_namespace
	                  ORDER BY nspname""")
	for row in cursor:
		oid, name, owner_oid = row
		namespace = objects.Namespace(name, roles[owner_oid])
		namespaces[oid] = namespace
		if not name.startswith("pg_"):
			schema.members.append(namespace)

	# TODO: domain basetype etc.
	cursor.execute("""SELECT oid, typname, typnamespace, typowner, typnotnull
	                  FROM pg_type
	                  ORDER BY typnamespace, typname""")
	for row in cursor:
		oid, name, namespace_oid, owner_oid, notnull = row
		type = objects.Type(name, roles[owner_oid], notnull)
		types[oid] = type
		namespaces[namespace_oid].members.append(type)

	cursor.execute("""SELECT oid, relname, relowner, relnamespace, relkind
	                  FROM pg_class
	                  ORDER BY relnamespace, relkind, relname""")
	for row in cursor:
		oid, name, owner_oid, namespace_oid, kind = row
		relation = relation_types[kind](name, roles[owner_oid])
		relations[oid] = relation
		namespaces[namespace_oid].members.append(relation)

	cursor.execute("""SELECT attrelid, attname, atttypid, attnotnull,
	                         pg_get_expr(adbin, attrelid)
	                  FROM pg_attribute
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE attnum > 0 AND NOT attisdropped
	                  ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, notnull, default = row
		columns = relations[relation_oid].columns
		if columns is not None:
			column = objects.Column(name, types[type_oid], notnull, default)
			columns.append(column)

	# TODO: function properties
	cursor.execute("""SELECT oid, proname, pronamespace, proowner, prolang
	                  FROM pg_proc
	                  ORDER BY pronamespace, proname""")
	for row in cursor:
		oid, name, namespace_oid, owner_oid, language_oid = row
		function = objects.Function(name, roles[owner_oid], languages[language_oid])
		functions[oid] = function
		namespaces[namespace_oid].members.append(function)

	# TODO: constraint triggers
	# TODO: trigger properties
	cursor.execute("""SELECT tgrelid, tgname, tgfoid
	                  FROM pg_trigger
	                  WHERE NOT tgisconstraint
	                  ORDER BY tgrelid, tgname""")
	for row in cursor:
		table_oid, name, function_oid = row
		trigger = objects.Trigger(name, functions[function_oid])
		relations[table_oid].triggers.append(trigger)

	# TODO: rule properties
	cursor.execute("""SELECT rulename, ev_class
	                  FROM pg_rewrite
                          WHERE rulename != '_RETURN'
	                  ORDER BY ev_class, rulename""")
	for row in cursor:
		name, table_oid = row
		rule = objects.Rule(name)
		relations[table_oid].rules.append(rule)

	# TODO: operator properties
	cursor.execute("""SELECT oid, oprname, oprnamespace, oprowner
	                  FROM pg_operator
	                  ORDER BY oprnamespace, oprname""")
	for row in cursor:
		oid, name, namespace_oid, owner_oid = row
		operator = objects.Operator(name, roles[owner_oid])
		operators[oid] = operator
		namespaces[namespace_oid].members.append(operator)

	# TODO: operator class operators/functions
	cursor.execute("""SELECT pg_opclass.oid, amname, opcname, opcnamespace, opcowner,
	                         opcintype, opcdefault, opckeytype
	                  FROM pg_opclass, pg_am
                          WHERE opcmethod = pg_am.oid
	                  ORDER BY opcnamespace, opcname, opcintype, amname""")
	for row in cursor:
		oid, method, name, namespace_oid, owner_oid, intype_oid, default, keytype_oid = row
		owner = roles[owner_oid]
		intype = types[intype_oid]
		keytype = types.get(keytype_oid)
		opclass = objects.OperatorClass(method, name, owner, intype, default, keytype)
		opclasses[oid] = opclass
		namespaces[namespace_oid].members.append(opclass)

	# TODO: casts
