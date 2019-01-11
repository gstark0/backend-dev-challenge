from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False

db_name = 'database.db'

# Getting column names
def dict_factory(cursor, row):
	d = {}
	for idx,col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

# For POST or PUT requests
# It can add a new product or update an already existing one
# It's just to make POST and PUT requests shorter
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

	return {'title': title, 'price': price, 'inventory_count': inventory_count}

# GET to query products
# POST to add a new product
# PUT to update a product
# DELETE to delete products
@app.route('/api/products', methods=['GET', 'POST', 'DELETE'])
@app.route('/api/products/<int:url_id>', methods=['GET', 'PUT', 'DELETE'])
def products(url_id=None):
	with sqlite3.connect(db_name) as conn:
		if request.method == 'GET':
			# Column names
			conn.row_factory = dict_factory

			cur = conn.cursor()
			if url_id is None:
				available = str(request.args.get('available')).lower()
				if available == 'true' or available == '1':
					cur.execute('SELECT product_id, title, price, inventory_count FROM products WHERE inventory_count > 0')
				else:
					cur.execute('SELECT product_id, title, price, inventory_count FROM products')
				items = cur.fetchall()
			else:
				cur.execute('SELECT product_id, title, price, inventory_count FROM products WHERE product_id=?', (url_id,))
				items = cur.fetchone()

			out = items

		elif request.method == 'DELETE':
			cur = conn.cursor()
			if url_id is None:
				cur.execute('DELETE FROM products')
			else:
				cur.execute('DELETE FROM products WHERE product_id=?', (url_id,))

			out = 'deleted'

		elif request.method == 'POST':
			out = post_put(conn, 'INSERT INTO products (title, price, inventory_count) VALUES (?, ?, ?)')

		elif request.method == 'PUT':
			out = post_put(conn, 'UPDATE products SET title=?, price=?, inventory_count=? WHERE product_id=?', url_id=url_id)
	return jsonify(out)

# Buying products
@app.route('/api/products/<int:url_id>/purchase', methods=['GET', 'POST'])
def purchase(url_id):
	with sqlite3.connect(db_name) as conn:
		cur = conn.cursor()
		cur.execute('''UPDATE products
						SET inventory_count = inventory_count - 1
						WHERE inventory_count > 0 AND product_id=?''', (url_id,))

		# If product's inventory_count was updated, return 'Ok'
		# or else return custom 404 message
		if cur.rowcount is 1:
			out = jsonify('Ok')
		else:
			out = jsonify('Product out of stock'), 404
	return out

# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
	return jsonify('Cannot %s %s' % (request.method, request.path)), 404

@app.route('/')
def main():
	return 'works'

if __name__ == '__main__':
	app.run(host='0.0.0.0')