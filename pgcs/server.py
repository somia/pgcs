import BaseHTTPServer as httpserver
import httplib
import os
import sys

import core.diff
import core.load
import html.diff

tree = None

class Handler(httpserver.BaseHTTPRequestHandler):
	mimetypes = {
		"css": "text/css",
		"html": "text/html",
		"js": "text/javascript",
	}

	rewrites = {
		"/": "/static/ui.html",
	}

	def do_GET(self):
		path = self.rewrites.get(self.path, self.path)
		comps = path.split("/")
		if comps[1] == "static":
			self.get_static(comps[2:])
		elif comps[1] == "dynamic":
			self.get_dynamic(comps[2:])

	def get_static(self, comps):
		comps = [c for c in comps if c != ".."]
		path = os.path.join("static", os.path.sep.join(comps))

		base, suffix = path.rsplit(".", 1)
		mimetype = self.mimetypes[suffix]

		with open(path) as file:
			content = file.read()

		self.send_response(httplib.OK)
		self.send_header("Content-Type", mimetype)
		self.send_header("Content-Length", len(content))
		self.end_headers()

		self.wfile.write(content)

	def get_dynamic(self, comps):
		self.send_response(httplib.OK)
		self.send_header("Content-Type", "text/xml")
		self.send_header("Cache-Control", "no-cache, must-revalidate")
		self.send_header("Connection", "close")
		self.end_headers()

		print >>self.wfile, '<?xml version="1.0" encoding="UTF-8"?>'
		tree.write(self.wfile, "utf-8")

def main():
	global tree

	addr_str = sys.argv[1]
	config = sys.argv[2]

	with open(config) as file:
		sources = file.readlines()

	databases = core.load.load_databases(sources)
	diff = core.diff.diff_databases(databases)
	tree = html.diff.generate(diff)

	if ":" in addr_str:
		host, port = addr_str.split(":")
		address = host, int(port)
	else:
		address = "", int(addr_str)

	server = httpserver.HTTPServer(address, Handler)

	print "Initialized"

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()
