import sqlite3

conn = sqlite3.connect('database.db')

conn.execute('''CREATE TABLE products
				(product_id INTEGER PRIMARY KEY,
				title TEXT,
				price REAL,
				inventory_count INTEGER)''')
conn.close()