from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

db_name = 'database.db'

# Getting column names
def dict_factory(cursor, row):
	d = {}
	for idx,col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

# For POST or PUT requests
# It can add a new product or update an already existing one
def post_put(conn, qry, url_id=None):
	# Get parameters
	data = request.form.to_dict()
	title = data['title']
	price = data['price']
	inventory_count = data['inventory_count']

	cur = conn.cursor()
	if url_id is None:
		cur.execute(qry, (title, price, inventory_count))
	else:
		cur.execute(qry, (title, price, inventory_count, url_id))

# GET to query products
# POST to add a new product
# PUT to update a product
# DELETE to delete products
@app.route('/api/products', methods=['GET', 'POST', 'DELETE'])
@app.route('/api/products/<int:url_id>', methods=['GET', 'PUT', 'DELETE'])
def add(url_id=None):
	with sqlite3.connect(db_name) as conn:
		if request.method == 'GET':
			# Column names
			conn.row_factory = dict_factory

			cur = conn.cursor()
			if url_id is None:
				cur.execute('SELECT product_id, title, price, inventory_count FROM products')
				items = cur.fetchall()
			else:
				cur.execute('SELECT product_id, title, price, inventory_count FROM products WHERE product_id=?', (url_id,))
				items = cur.fetchone()

			return jsonify(items)

		elif request.method == 'DELETE':
			cur = conn.cursor()
			if url_id is None:
				cur.execute('DELETE FROM products')
			else:
				cur.execute('DELETE FROM products WHERE product_id=?', (url_id,))

			return('deleted')

		elif request.method == 'POST':
			post_put(conn, 'INSERT INTO products (title, price, inventory_count) VALUES (?, ?, ?)')
			return 'added'

		elif request.method == 'PUT':
			post_put('UPDATE products SET title=?, price=?, inventory_count=? WHERE product_id=?')
			return 'updated'

@app.route('/')
def main():
	return 'works'

if __name__ == '__main__':
	app.run(host='0.0.0.0')