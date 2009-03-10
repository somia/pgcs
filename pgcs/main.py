import sys

import core.database
import core.diff
import html.tree

def main():
	filename = sys.argv[1]
	sources = sys.argv[2:]

	schemas = core.database.get_schemas(sources)
	diff = core.diff.Schema(*schemas)
	tree = html.tree.schema(diff)

	with open(filename, "w") as file:
		tree.write(file)

if __name__ == "__main__":
	main()
