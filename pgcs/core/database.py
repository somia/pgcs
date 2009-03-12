import contextlib
import threading

import psycopg2
import psycopg2.extensions

from . import loader
from . import objects

class Future(object):
	def __init__(self, call, *args):
		self._thread = threading.Thread(target=self._run, args=(call, args))
		self._thread.daemon = True
		self._thread.start()

	def _run(self, call, args):
		try:
			self._result = call(*args)
			self._error = None
		except Exception as e:
			self._error = e

	def get(self):
		self._thread.join()
		if self._error is not None:
			raise self._error
		return self._result

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
	futures = [Future(db.get_schema) for db in databases]
	return [future.get() for future in futures]
