import sys
import contextlib

import psycopg2
import psycopg2.extensions

from . import loader

def main():
	datasource, = sys.argv[1:]

	with contextlib.closing(psycopg2.connect(datasource)) as conn:
		conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
		schema = loader.get_schema(conn)

	schema.dump()

if __name__ == "__main__":
	main()
