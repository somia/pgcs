import difflib
import sys

import core.data
import core.diff
import core.load
import html.diff

def get_object_name(object):
	return "%s.%s" % (object.namespace.name, object.get_name())

def get_diff_name(diff):
	return get_object_name(diff.objects[0])

def _copy_constraint(parent, name, definition):
	print "ALTER TABLE %s ADD CONSTRAINT %s %s;" % (parent, name, definition)

def copy_primary_key(parent, object):
	columns = [c.name for c in object.columns]
	definition = "PRIMARY KEY (%s)" % ", ".join(columns)
	_copy_constraint(parent, object.name, definition)

def copy_foreign_key(parent, object):
	_copy_constraint(parent, object.name, object.definition)

def copy_check_column_constraint(parent, object):
	_copy_constraint(parent, object.name, object.definition)

def alter_check_column_constraint(parent, object):
	print "ALTER TABLE %s DROP CONSTRAINT %s;" % (parent, object.name)
	copy_check_column_constraint(parent, object)

def copy_unique_column_constraint(parent, object):
	_copy_constraint(parent, object.name, object.definition)

copiers = {
	core.data.PrimaryKey: copy_primary_key,
	core.data.ForeignKey: copy_foreign_key,
	core.data.CheckColumnConstraint: copy_check_column_constraint,
	core.data.UniqueColumnConstraint: copy_unique_column_constraint,
}

alterers = {
	core.data.CheckColumnConstraint: alter_check_column_constraint,
}

def copy_entry(parent, entry):
	obj1, obj2 = entry.objects

	if obj1 is not None and obj2 is None:
		kind = type(obj1)
		copier = copiers.get(kind)
		if copier:
			copier(parent, obj1)

	if obj1 is not None and obj2 is not None:
		kind = type(obj1)
		alterer = alterers.get(kind)
		if alterer:
			alterer(parent, obj1)

def copy_entries(parent_diff, named_object_list):
	parent_name = get_diff_name(parent_diff)

	if named_object_list:
		for entry in named_object_list.entries:
			copy_entry(parent_name, entry)

def create_trigger(parent, object):
	print "%s;" % object.description

def drop_trigger(parent, object):
	print "DROP TRIGGER %s ON %s;" % (object.name, parent)

def alter_trigger(parent, object):
	drop_trigger(parent, object)
	create_trigger(parent, object)

def alter_trigger_entries(parent_diff, named_object_list):
	parent_name = get_diff_name(parent_diff)

	if named_object_list:
		for entry in named_object_list.entries:
			obj1, obj2 = entry.objects
			if obj1 is not None and obj2 is not None:
				alter_trigger(parent_name, obj1)
			elif obj1 is not None:
				create_trigger(parent_name, obj1)
			elif obj2 is not None:
				drop_trigger(parent_name, obj2)

def copy_table_column(table, object):
	definition = "%s.%s" % (object.type.namespace.name, object.type.name)
	if object.notnull:
		definition += " NOT NULL"
	if object.default:
		definition += " DEFAULT %s" % object.default
	print "ALTER TABLE %s ADD COLUMN %s %s;" % (table, object.name, definition)

def handle_table_columns(table_diff, seq1, seq2):
	table_name = get_diff_name(table_diff)

	hash1 = [html.diff.NamedHash(o) for o in seq1]
	hash2 = [html.diff.NamedHash(o) for o in seq2]
	match = difflib.SequenceMatcher(a=hash1, b=hash2)

	inserted = {}
	deleted = {}

	for tag, i1, i2, j1, j2 in match.get_opcodes():
		if tag == "delete":
			for obj in seq1[i1:i2]:
				deleted[obj.name] = obj

		elif tag == "insert":
			for obj in seq2[j1:j2]:
				inserted[obj.name] = obj

	for name, obj in deleted.iteritems():
		if name not in inserted:
			copy_table_column(table_name, obj)

def handle_table(diff):
	copy_entries(diff, diff.constraints)
	alter_trigger_entries(diff, diff.triggers)

	if diff.columns:
		handle_table_columns(diff, *diff.columns.lists)

def handle_function(diff):
	if diff.source1:
		obj1, obj2 = diff.objects
		if obj1 is not None and obj2 is not None:
			for referer in obj2.xrefs:
				assert isinstance(referer, core.data.Trigger)
				drop_trigger(get_object_name(referer.table), referer)

			name = get_object_name(obj2)
			print "DROP FUNCTION %s;" % name
			print "CREATE FUNCTION %s ... ADD CODE HERE ... ;" % name
			print "ALTER FUNCTION %s OWNER TO galleria;" % get_object_name(obj2)

			for referer in obj2.xrefs:
				create_trigger(get_object_name(referer.table), referer)

handlers = {
#	core.diff.Function: handle_function,
	core.diff.Table: handle_table,
}

def get_entries(named_object_list):
	if named_object_list:
		return named_object_list.entries
	else:
		return []

def get_diff(entry):
	obj1, obj2 = entry.diff.objects
	if obj1 is not None and obj2 is not None:
		return entry.diff
	else:
		return None

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

def main():
	source, target = sys.argv[1:]

	databases = core.load.load_databases([source, target])
	diff_tree = core.diff.diff_databases(databases)

	for diff in get_diffs(diff_tree):
		kind = type(diff)
		handler = handlers.get(kind)
		if handler:
			handler(diff)

if __name__ == "__main__":
	main()
