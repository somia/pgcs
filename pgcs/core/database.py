import contextlib

import psycopg2
import psycopg2.extensions

from . import future
from . import loader
from . import objects

class Database(object):
	def __init__(self, source):
		self.source = source
		self.name = None

		for token in source.split():
			if token.startswith("dbname="):
				self.name = token.split("=", 1)[1]
				break

		if self.name is None:
			raise Exception("No dbname in DSN string")

	def get_schema(self):
		schema = objects.Schema(self)

		with contextlib.closing(psycopg2.connect(self.source)) as conn:
			conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
			loader.load_schema(schema, conn)

		return schema

databases = []

def register(source):
	db = Database(source)
	databases.append(db)
	return db

def get_schemas():
	futures = [future.Future(db.get_schema) for db in databases]
	return [f.get() for f in futures]
