import contextlib

import psycopg2
import psycopg2.extensions

from . import data
from . import future

def load_databases(sources):
	futures = [future.Future(load_database, s) for s in sources]
	return [f.get() for f in futures]

def load_database(source):
	db = data.Database(source)

	with contextlib.closing(psycopg2.connect(source)) as conn:
		conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
		with contextlib.closing(conn.cursor()) as cursor:
			populate_database(db, cursor)

	return db

def populate_database(db, cursor):
	db_prefix = "%s:" % db.get_name()

	roles = {}
	languages = {}
	namespaces = {}
	types = {}
	relations = {}
	tables = []
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
		language = data.Language(name, roles[owner_oid])
		languages[oid] = language
		if userdefined:
			db.languages.append(language)

	# namespaces

	cursor.execute("""SELECT oid, nspname, nspowner
	                  FROM pg_namespace
	                  ORDER BY nspname""")
	for row in cursor:
		oid, name, owner_oid = row
		ns = data.Namespace(name, roles[owner_oid])
		namespaces[oid] = ns
		if not name.startswith("pg_"):
			db.namespaces.append(ns)

	# Types
	# TODO: type properties

	type_types = {
		"b": data.Type,
		"c": data.Type, # composite
		"d": data.Domain,
		"e": data.Type, # enum
		"p": data.Type, # pseudo
	}

	cursor.execute("""SELECT a.oid, a.typname, a.typnamespace, a.typowner, a.typtype,
	                         a.typnotnull, a.typdefault, b.typrelid
	                  FROM pg_type AS a
	                  LEFT OUTER JOIN pg_type AS b ON a.typelem = b.oid
	                  WHERE a.typisdefined
	                  ORDER BY a.typnamespace, a.typname""")
	for row in cursor:
		oid, name, ns_oid, owner_oid, kind, notnull, default, super_oid = row
		ns = namespaces[ns_oid]
		type = type_types[kind](ns, name, roles[owner_oid], notnull, default)
		types[oid] = type
		if kind in "bde" and not super_oid:
			ns.types.append(type)

	cursor.execute("""SELECT oid, typbasetype
	                  FROM pg_type
	                  WHERE typisdefined AND typbasetype != 0""")
	for row in cursor:
		oid, base_oid = row
		types[oid].init_base(types[base_oid])

	# Relations

	relation_types = {
		"c": (data.Composite, "composites"),
		"i": (data.Index, "indexes"),
		"r": (data.Table, "tables"),
		"t": (data.Table, "tables"),
		"v": (data.View, "views"),
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
		if kind in "rt" and not ns.name.startswith("pg_"):
			full_name = '"%s"."%s"' % (ns.name, name)
			tables.append((full_name, relation))

	cursor.execute("""SELECT attrelid, attname, atttypid, attnum, attnotnull,
	                         pg_get_expr(adbin, attrelid)
	                  FROM pg_attribute
	                  INNER JOIN pg_class ON attrelid = pg_class.oid
	                  LEFT OUTER JOIN pg_attrdef ON attrelid = adrelid AND attnum = adnum
	                  WHERE relkind != 'S' AND attnum > 0 AND NOT attisdropped
	                  ORDER BY attrelid, attnum""")
	for row in cursor:
		relation_oid, name, type_oid, num, notnull, default = row
		column = data.Column(name, types[type_oid], notnull, default)
		relations[relation_oid].columns[num] = column

	for full_name, table in tables:
		cursor.execute("""SAVEPOINT table_savepoint""")
		try:
			cursor.execute("""SELECT 1 FROM %s LIMIT 1""" % full_name)
		except:
			cursor.execute("""ROLLBACK TO SAVEPOINT table_savepoint""")
			print db_prefix, "Failed to access table", full_name
		else:
			table.init_content(cursor.fetchone() is not None)
			cursor.execute("""RELEASE SAVEPOINT table_savepoint""")

	# Sequences

	cursor.execute("""SELECT relname, relowner, relnamespace
	                  FROM pg_class
	                  WHERE relkind = 'S'
	                  ORDER BY relnamespace, relname""")
	for row in cursor:
		name, owner_oid, ns_oid = row
		ns = namespaces[ns_oid]
		sequence = data.Sequence(ns, name, roles[owner_oid])
		full_name = '"%s"."%s"' % (ns.name, name)
		sequences.append((full_name, sequence))
		ns.sequences.append(sequence)

	for full_name, sequence in sequences:
		cursor.execute("""SAVEPOINT sequence""")
		try:
			cursor.execute("""SELECT increment_by, min_value, max_value
			                  FROM %s""" % full_name)
		except:
			cursor.execute("""ROLLBACK TO SAVEPOINT sequence""")
			print db_prefix, "Failed to access sequence", full_name
		else:
			sequence.init_values(*cursor.fetchone())
			cursor.execute("""RELEASE SAVEPOINT sequence""")

	# Constraints

	table_constraint_types = {
		"c": data.CheckColumnConstraint,
		"u": data.UniqueColumnConstraint,
		"p": data.PrimaryKey,
	}

	domain_constraint_types = {
		"c": data.CheckConstraint,
		"u": data.UniqueConstraint,
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
				cons = data.ForeignKey(name, definition, cols, f_table, f_cols)
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
		function = data.Function(ns, name, owner, lang, rettype, argtypes, src1, src2)
		functions[oid] = function
		ns.functions.append(function)

	# Triggers

	cursor.execute("""SELECT tgrelid, tgname, tgfoid, pg_get_triggerdef(oid)
	                  FROM pg_trigger
	                  WHERE NOT tgisconstraint
	                  ORDER BY tgrelid, tgname""")
	for row in cursor:
		table_oid, name, function_oid, description = row
		trigger = data.Trigger(name, functions[function_oid], description)
		relations[table_oid].triggers.append(trigger)

	# Rules

	cursor.execute("""SELECT rulename, ev_class, pg_get_ruledef(oid)
	                  FROM pg_rewrite
                          WHERE rulename != '_RETURN'
	                  ORDER BY ev_class, rulename""")
	for row in cursor:
		name, table_oid, definition = row
		rule = data.Rule(name, definition)
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
		operator = data.Operator(ns, name, roles[owner_oid])
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
		opclass = data.OperatorClass(ns, method, name, owner, intype, default, keytype)
		opclasses[oid] = opclass
		ns.opclasses.append(opclass)

	# TODO: casts
