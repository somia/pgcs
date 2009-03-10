import contextlib
import threading

import psycopg2
import psycopg2.extensions

from . import loader

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

def get_schema(source):
	with contextlib.closing(psycopg2.connect(source)) as conn:
		conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
		return loader.get_schema(conn)

def get_schemas(sources):
	futures = [Future(get_schema, source) for source in sources]
	return [future.get() for future in futures]
