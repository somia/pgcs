import re
import sys

import pgcs.core.data
import pgcs.core.diff
import pgcs.core.load
core = pgcs.core

def get_entries(named_object_list):
	if named_object_list:
		return named_object_list.entries
	else:
		return []

def get_object(entry):
	obj1, obj2 = entry.diff.objects
	if obj1 is not None and obj2 is None:
		return obj1
	else:
		return None

def _missing_objects(diff):
	for entry in get_entries(diff.languages):
		yield get_object(entry)

	for entry in get_entries(diff.namespaces):
		yield get_object(entry)

		for seq in (entry.diff.types,
		            entry.diff.indexes,
		            entry.diff.tables,
		            entry.diff.views,
		            entry.diff.sequences,
		            entry.diff.functions):
			for e in get_entries(seq):
				yield get_object(e)

def missing_objects(diff):
	for object in _missing_objects(diff):
		if object is not None:
			yield object

def format(object):
	return object.get_name()

def format_ns(object):
	return object.namespace.name, object.get_name()

info = {
	core.data.Language:  ("LANGUAGE", format),
	core.data.Namespace: ("SCHEMA",   format),
	core.data.Type:      ("TYPE",     format_ns),
	core.data.Index:     ("INDEX",    format_ns),
	core.data.Table:     ("TABLE",    format_ns),
	core.data.View:      ("VIEW",     format_ns),
	core.data.Sequence:  ("SEQUENCE", format_ns),
	core.data.Function:  ("FUNCTION", format_ns),
}

def handle_language(filters, tokens):
	nsname = tokens[5]
	name = tokens[6]
	return filters.get(("LANGUAGE", (nsname, name))) is not None

def handle_namespace(filters, tokens):
	kindname = tokens[3]
	name = tokens[5]
	return filters.get((kindname, name)) is not None

def handle_function(filters, tokens):
	kindname = tokens[3]
	nsname = tokens[4]
	name = " ".join(tokens[5:-1])
	name = transform_function_args(name)
	return filters.get((kindname, (nsname, name))) is not None

def transform_function_args(full_name):
	name, argstring = re.match(r"(.*)\((.*)\)", full_name).groups()
	args = []
	for oldarg in argstring.split(","):
		oldarg = oldarg.strip()
		newarg = function_arg_mappings.get(oldarg)
		if newarg is not None:
			args.append(newarg)
		else:
			args.append(oldarg)
	return "%s(%s)" % (name, ", ".join(args))

function_arg_mappings = {
	"boolean": "bool",
	"character varying": "varchar",
	"character": "bpchar",
	"character[]": "_bpchar",
	"integer": "int4",
	"timestamp without time zone": "timestamp",
}

def handle_other(filters, tokens):
	kindname = tokens[3]
	nsname = tokens[4]
	name = tokens[5]
	return filters.get((kindname, (nsname, name))) is not None

handlers = {
	"PROCEDURAL": handle_language,
	"SCHEMA":     handle_namespace,
	"TYPE":       handle_other,
	"INDEX":      handle_other,
	"TABLE":      handle_other,
	"VIEW":       handle_other,
	"SEQUENCE":   handle_other,
	"FUNCTION":   handle_function,
}

def main():
	source, target = sys.argv[1:]

	databases = core.load.load_databases([source, target])
	diff_tree = core.diff.diff_databases(databases)

	filters = {}

	for object in missing_objects(diff_tree):
		kind = type(object)
		kindname, formatter = info[kind]
		name = formatter(object)
		filters[(kindname, name)] = object

	for line in sys.stdin:
		if line.startswith(";"):
			print line,
		else:
			tokens = line.split()
			if len(tokens) >= 7:
				kind = tokens[3]
				handler = handlers.get(kind)
				if handler:
					if handler(filters, tokens):
						print line,

if __name__ == "__main__":
	main()
