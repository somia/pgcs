import sys
from contextlib import closing

import psycopg2
import psycopg2.extensions

def main():
	datasource, = sys.argv[1:]

	with closing(psycopg2.connect(datasource)) as conn:
		conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
		with closing(conn.cursor()) as cursor:
			cursor.execute("select now()")
			for row in cursor:
				print row

if __name__ == "__main__":
	main()
