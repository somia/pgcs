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
	sequences = []
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
			schema.languages.append(language)

	# namespaces

	cursor.execute("""SELECT oid, nspname, nspowner
	                  FROM pg_namespace
	                  ORDER BY nspname""")
	for row in cursor:
		oid, name, owner_oid = row
		ns = objects.Namespace(name, roles[owner_oid])
		namespaces[oid] = ns
		if not name.startswith("pg_"):
			schema.namespaces.append(ns)

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
		oid, name, ns_oid, owner_oid, kind, notnull, default = row
		ns = namespaces[ns_oid]
		type = type_types[kind](ns, name, roles[owner_oid], notnull, default)
		types[oid] = type
		if kind in "bde":
			ns.types.append(type)

	cursor.execute("""SELECT oid, typbasetype
	                  FROM pg_type
	                  WHERE typisdefined AND typbasetype != 0""")
	for row in cursor:
		oid, base_oid = row
		types[oid].init_base(types[base_oid])

	# Relations

	relation_types = {
		"c": (objects.Composite, "composites"),
		"i": (objects.Index, "indexes"),
		"r": (objects.Table, "tables"),
		"t": (objects.Table, "tables"),
		"v": (objects.View, "views"),
	}

	cursor.execute("""SELECT oid, relname, relowner, relnamespace, relkind
	                  FROM pg_class
	                  WHERE relkind != 'S'
	                  ORDER BY relnamespace, relkind, relname""")
	for row in cursor:
		oid, name, owner_oid, ns_oid, kind = row
		ns = namespaces[ns_oid]
		classtype, listname = relation_types[kind]
		relation = classtype(ns, name, roles[owner_oid])
		relations[oid] = relation
		getattr(ns, listname).append(relation)

	cursor.execute("""SELECT attrelid, attname, atttypid, attnum, attnotnull,
	                         pg_get_expr(adbin, attrelid)
	                  FROM pg_attribute
	                  INNER JOIN pg_class ON attrelid = pg_class.oid
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE relkind != 'S' AND attnum > 0 AND NOT attisdropped
	                  ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, num, notnull, default = row
		column = objects.Column(name, types[type_oid], notnull, default)
		relations[relation_oid].columns[num] = column

	# Sequences

	cursor.execute("""SELECT relname, relowner, relnamespace
	                  FROM pg_class
	                  WHERE relkind = 'S'
	                  ORDER BY relnamespace, relname""")
	for row in cursor:
		name, owner_oid, ns_oid = row
		ns = namespaces[ns_oid]
		sequence = objects.Sequence(ns, name, roles[owner_oid])
		full_name = '"%s"."%s"' % (ns.name, name)
		sequences.append((full_name, sequence))
		ns.sequences.append(sequence)

	for full_name, sequence in sequences:
		cursor.execute("""SELECT increment_by, min_value, max_value
		                  FROM %s""" % full_name)
		sequence.init_values(*cursor.fetchone())

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
		name, kind, table_oid, domain_oid, f_oid, col_nums, f_nums, definition = row
		if table_oid:
			table = relations[table_oid]
			cols = [table.columns[n] for n in col_nums]
			if kind == "f":
				f_table = relations[f_oid]
				f_cols = [f_table.columns[n] for n in f_nums]
				cons = objects.ForeignKey(name, definition, cols, f_table, f_cols)
			else:
				cons = table_constraint_types[kind](name, definition, cols)
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
		oid, name, ns_oid, owner_oid, lang_oid, rettype_oid, argtype_oids, src1, src2 = row
		ns = namespaces[ns_oid]
		owner = roles[owner_oid]
		lang = languages[lang_oid]
		rettype = types[rettype_oid]
		argtypes = [types[oid] for oid in argtype_oids]
		function = objects.Function(ns, name, owner, lang, rettype, argtypes, src1, src2)
		functions[oid] = function
		ns.functions.append(function)

	# Triggers

	cursor.execute("""SELECT tgrelid, tgname, tgfoid, pg_get_triggerdef(oid)
	                  FROM pg_trigger
	                  WHERE NOT tgisconstraint
	                  ORDER BY tgrelid, tgname""")
	for row in cursor:
		table_oid, name, function_oid, description = row
		trigger = objects.Trigger(name, functions[function_oid], description)
		relations[table_oid].triggers.append(trigger)

	# Rules

	cursor.execute("""SELECT rulename, ev_class, pg_get_ruledef(oid)
	                  FROM pg_rewrite
                          WHERE rulename != '_RETURN'
	                  ORDER BY ev_class, rulename""")
	for row in cursor:
		name, table_oid, definition = row
		rule = objects.Rule(name, definition)
		relations[table_oid].rules.append(rule)

	# Operators
	# TODO: operator properties
	# TODO: operator class operators/functions

	cursor.execute("""SELECT oid, oprname, oprnamespace, oprowner
	                  FROM pg_operator
	                  ORDER BY oprnamespace, oprname""")
	for row in cursor:
		oid, name, ns_oid, owner_oid = row
		ns = namespaces[ns_oid]
		operator = objects.Operator(ns, name, roles[owner_oid])
		operators[oid] = operator
		ns.operators.append(operator)

	cursor.execute("""SELECT pg_opclass.oid, amname, opcname, opcnamespace, opcowner,
	                         opcintype, opcdefault, opckeytype
	                  FROM pg_opclass, pg_am
                          WHERE opcmethod = pg_am.oid
	                  ORDER BY opcnamespace, opcname, opcintype, amname""")
	for row in cursor:
		oid, method, name, ns_oid, owner_oid, intype_oid, default, keytype_oid = row
		ns = namespaces[ns_oid]
		owner = roles[owner_oid]
		intype = types[intype_oid]
		keytype = types.get(keytype_oid)
		opclass = objects.OperatorClass(ns, method, name, owner, intype, default, keytype)
		opclasses[oid] = opclass
		ns.opclasses.append(opclass)

	# TODO: casts
