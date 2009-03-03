import contextlib

from . import objects

def get_schema(conn):
	schema = objects.Schema()

	with contextlib.closing(conn.cursor()) as cursor:
		populate_schema(schema, cursor)

	return schema

def populate_schema(schema, cursor):
	roles = {}
	languages = {}
	namespaces = {}
	types = {}
	relations = {}
	functions = {}
	operators = {}
	opclasses = {}

	cursor.execute("""SET search_path TO pg_catalog""")

	# Roles

	cursor.execute("""SELECT oid, rolname
	                  FROM pg_roles""")
	for row in cursor:
		oid, name = row
		roles[oid] = name

	# Languages

	cursor.execute("""SELECT oid, lanname, lanowner, lanispl
	                  FROM pg_language
	                  ORDER BY lanname""")
	for row in cursor:
		oid, name, owner_oid, userdefined = row
		language = objects.Language(name, roles[owner_oid])
		languages[oid] = language
		if userdefined:
			schema.members.append(language)

	# Namespaces

	cursor.execute("""SELECT oid, nspname, nspowner
	                  FROM pg_namespace
	                  ORDER BY nspname""")
	for row in cursor:
		oid, name, owner_oid = row
		namespace = objects.Namespace(name, roles[owner_oid])
		namespaces[oid] = namespace
		if not name.startswith("pg_"):
			schema.members.append(namespace)

	# Types
	# TODO: type properties

	type_types = {
		"b": objects.Type,
		"c": objects.Type, # composite
		"d": objects.Domain,
		"e": objects.Type, # enum
		"p": objects.Type, # pseudo
	}

	cursor.execute("""SELECT oid, typname, typnamespace, typowner, typtype, typnotnull,
	                         typdefault
	                  FROM pg_type
	                  WHERE typisdefined
	                  ORDER BY typnamespace, typname""")
	for row in cursor:
		oid, name, namespace_oid, owner_oid, kind, notnull, default = row
		type = type_types[kind](name, roles[owner_oid], notnull, default)
		types[oid] = type
		if kind in "bde":
			namespaces[namespace_oid].members.append(type)

	cursor.execute("""SELECT oid, typbasetype
	                  FROM pg_type
	                  WHERE typisdefined AND typbasetype != 0""")
	for row in cursor:
		oid, base_oid = row
		types[oid].init_base(types[base_oid])

	# Relations

	relation_types = {
		"S": objects.Sequence,
		"c": objects.Composite,
		"i": objects.Index,
		"r": objects.Table,
		"t": objects.Table,
		"v": objects.View,
	}

	cursor.execute("""SELECT oid, relname, relowner, relnamespace, relkind
	                  FROM pg_class
	                  ORDER BY relnamespace, relkind, relname""")
	for row in cursor:
		oid, name, owner_oid, namespace_oid, kind = row
		relation = relation_types[kind](name, roles[owner_oid])
		relations[oid] = relation
		namespaces[namespace_oid].members.append(relation)

	cursor.execute("""SELECT attrelid, attname, atttypid, attnum, attnotnull,
	                         pg_get_expr(adbin, attrelid)
	                  FROM pg_attribute
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE attnum > 0 AND NOT attisdropped
	                  ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, num, notnull, default = row
		relation = relations[relation_oid]
		if relation.columns is not None:
			column = objects.Column(relation, name, types[type_oid], notnull, default)
			relation.columns[num] = column

	# Constraints

	table_constraint_types = {
		"c": objects.CheckColumnConstraint,
		"u": objects.UniqueColumnConstraint,
		"p": objects.PrimaryKey,
	}

	domain_constraint_types = {
		"c": objects.CheckConstraint,
		"u": objects.UniqueConstraint,
	}

	cursor.execute("""SELECT conname, contype, conrelid, contypid, confrelid, conkey, confkey,
	                         pg_get_constraintdef(oid)
	                  FROM pg_constraint
	                  ORDER BY conrelid, contype, conname""")
	for row in cursor:
		name, kind, table_oid, domain_oid, foreign_oid, column_nums, foreign_nums, \
			definition = row
		if table_oid:
			table = relations[table_oid]
			columns = [table.columns[n] for n in column_nums]
			if kind == "f":
				foreign_table = relations[foreign_oid]
				foreign_cols = [foreign_table.columns[n] for n in foreign_nums]
				cons = objects.ForeignKey(name, definition, columns, foreign_cols)
			else:
				cons = table_constraint_types[kind](name, definition, columns)
			table.constraints.append(cons)
		else:
			cons = domain_constraint_types[kind](name, definition)
			types[domain_oid].constraints.append(cons)

	# Functions

	cursor.execute("""SELECT oid, proname, pronamespace, proowner, prolang, prorettype,
	                         coalesce(proallargtypes, proargtypes), prosrc, probin
	                  FROM pg_proc
	                  ORDER BY pronamespace, proname""")
	for row in cursor:
		oid, name, namespace_oid, owner_oid, language_oid, rettype_oid, argtype_oids, \
			source1, source2 = row
		owner = roles[owner_oid]
		lang = languages[language_oid]
		rettype = types[rettype_oid]
		argtypes = [types[oid] for oid in argtype_oids]
		function = objects.Function(name, owner, lang, rettype, argtypes, source1, source2)
		functions[oid] = function
		namespaces[namespace_oid].members.append(function)

	# Triggers
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

	# Rules
	# TODO: rule properties

	cursor.execute("""SELECT rulename, ev_class
	                  FROM pg_rewrite
                          WHERE rulename != '_RETURN'
	                  ORDER BY ev_class, rulename""")
	for row in cursor:
		name, table_oid = row
		rule = objects.Rule(name)
		relations[table_oid].rules.append(rule)

	# Operators
	# TODO: operator properties
	# TODO: operator class operators/functions

	cursor.execute("""SELECT oid, oprname, oprnamespace, oprowner
	                  FROM pg_operator
	                  ORDER BY oprnamespace, oprname""")
	for row in cursor:
		oid, name, namespace_oid, owner_oid = row
		operator = objects.Operator(name, roles[owner_oid])
		operators[oid] = operator
		namespaces[namespace_oid].members.append(operator)

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
