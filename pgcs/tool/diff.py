import sys
import xml.etree.ElementTree as elementtree

import pgcs.core.diff
import pgcs.core.load
import pgcs.html.diff
import pgcs.html.tags

def main(file, sources):
	databases = pgcs.core.load.load_databases(sources)
	diff = pgcs.core.diff.diff_databases(databases)
	diff_tree = pgcs.html.diff.generate(diff)

	doc = pgcs.html.tags.TagTree()
	html = doc.html
	html.head.link(rel="stylesheet", href="static/diff.css")
	html.head.script(type="text/javascript", src="static/jquery-1.3.2.js")
	html.head.script(type="text/javascript", src="static/diff.js")
	html.body.div
	doc_tree = doc.get_element_tree()

	doc_tree.find("body/div").append(diff_tree.getroot())
	doc_tree.write(file, "utf-8")

if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2:])
