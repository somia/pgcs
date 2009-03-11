import BaseHTTPServer as httpserver
import httplib
import sys

import core.database
import core.diff
import html.tree

tree = None

class Handler(httpserver.BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(httplib.OK)
		self.send_header("Content-Type", "text/html")
		self.send_header("Cache-Control", "no-cache, must-revalidate")
		self.end_headers()

		tree.write(self.wfile)

def main():
	global tree

	addr_str = sys.argv[1]
	config = sys.argv[2]

	with open(config) as file:
		sources = file.readlines()

	schemas = core.database.get_schemas(sources)
	diff = core.diff.Schema(*schemas)
	tree = html.tree.schema(diff)

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
