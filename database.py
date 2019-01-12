import sqlite3

conn = sqlite3.connect('database.db')

conn.execute('''CREATE TABLE products
				(product_id INTEGER PRIMARY KEY,
				title TEXT,
				price REAL,
				inventory_count INTEGER)''')

conn.execute('''CREATE TABLE cart_items
				(item_id INTEGER PRIMARY KEY,
				product_id INTEGER,
				cart_id INTEGER,
				quantity INTEGER,
				FOREIGN KEY(product_id) REFERENCES products(product_id),
				FOREIGN KEY(cart_id) REFERENCES carts(cart_id))''')

conn.execute('''CREATE TABLE carts
				(cart_id INTEGER PRIMARY KEY,
				date_created TEXT)''')

conn.close()