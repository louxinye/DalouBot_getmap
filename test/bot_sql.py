import sqlite3


def select(a):
	conn = sqlite3.connect('data/getmap.db')
	c = conn.cursor()
	try:
		result = c.execute(a)
	except ValueError:
		return 0
	return result
