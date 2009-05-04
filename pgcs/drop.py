import sys

import core.data
import core.diff
import core.load

def get_entries(named_object_list):
	if named_object_list:
		return named_object_list.entries
	else:
		return []

def get_diff(entry):
	obj1, obj2 = entry.diff.objects
	if obj1 is None or obj2 is None:
		return None
	if isinstance(obj2, core.data.Table) and obj2.has_content:
		return None
	return entry.diff

def _get_diffs(diff):
	for entry in get_entries(diff.languages):
		yield get_diff(entry)

	for entry in get_entries(diff.namespaces):
		for seq in (entry.diff.types,
		            entry.diff.indexes,
		            entry.diff.tables,
		            entry.diff.views,
		            entry.diff.sequences,
		            entry.diff.functions):
			for e in get_entries(seq):
				yield get_diff(e)

def get_diffs(diff):
	for diff in _get_diffs(diff):
		if diff is not None:
			yield diff

commands = {
	core.data.Function: "DROP FUNCTION",
	core.data.Index: "DROP INDEX",
	core.data.Table: "DROP TABLE",
	core.data.View: "DROP VIEW",
}

def main():
	source, target = sys.argv[1:]

	databases = core.load.load_databases([source, target])
	diff_tree = core.diff.diff_databases(databases)

	for diff in get_diffs(diff_tree):
		obj1, obj2 = diff.objects
		kind = type(obj1)
		command = commands.get(kind)
		print "%s %s.%s;" % (command, obj2.namespace.name, obj2.get_name())

if __name__ == "__main__":
	main()
