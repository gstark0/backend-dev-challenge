from flask import Flask, jsonify, request, Blueprint, redirect
from utils import dict_factory
from cart import cart_api
import sqlite3
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.register_blueprint(cart_api)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

db_name = 'database.db'

# Limit request rate to 2 per second
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=['2 per second'],
)

# Redirect to HTTPS
@app.before_request
def before_request():
	if not request.is_secure and app.env != 'development':
		url = request.url.replace('http://', 'https://', 1)
		code = 301
		return redirect(url, code=code)

# GET to query products
# POST to add a new product
# PUT to update a product
# DELETE to delete products
@app.route('/api/products', methods=['GET', 'POST', 'DELETE'])
@app.route('/api/products/<int:url_id>', methods=['GET', 'PUT', 'DELETE'])
def products(url_id=None):
	with sqlite3.connect(db_name) as conn:
		# SQLite3 doesn't return keys by default
		conn.row_factory = dict_factory
		cur = conn.cursor()

		data = request.get_json()

		# 1. If ID is not specified, query all products, else return the specific product
		# 2. If 'available' parameter is set to 'true' or '1', return products with inventory_count > 0
		if request.method == 'GET':

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

			out = jsonify(items)

		# Delete a product
		# 1. If ID is not specified, delete all prodcuts, else delete the specific product
		elif request.method == 'DELETE':
			if url_id is None:
				cur.execute('DELETE FROM products')
			else:
				cur.execute('DELETE FROM products WHERE product_id=?', (url_id,))

			out = jsonify('Deleted')

		# Add a new product to database
		# 1. Handle KeyError and ValueError for security reasons - to make sure that you have a correct type
		# 2. Check if all parameters are provided
		# 3. Add a new row to database
		elif request.method == 'POST':

			if data is None:
				return jsonify('title, price and inventory_count are required')

			try:
				title = str(data['title'])
				price = float(data['price'])
				inventory_count = int(data['inventory_count'])

			except ValueError:
				return jsonify('Bad input type')

			except KeyError:
				return jsonify('title, price and inventory_count are required')

			cur.execute('INSERT INTO products (title, price, inventory_count) VALUES (?, ?, ?)', (title, price, inventory_count))
			out = jsonify({'created_resource': '/api/products/%s' % cur.lastrowid}), 201

		# Update a product
		# 1. Handle ValueError to check if provided parameters are in correct type (e.g don't allow product_id as a string)
		# 2. Update rows in database with provided data
		elif request.method == 'PUT':
			try:
				try:
					title = str(data['title'])
					cur.execute('UPDATE products SET title = ? WHERE product_id = ?', (title, url_id))
				except KeyError:
					pass

				try:
					price = float(data['price'])
					cur.execute('UPDATE products SET price = ? WHERE product_id = ?', (price, url_id))
				except KeyError:
					pass

				try:
					inventory_count = int(data['inventory_count'])
					cur.execute('UPDATE products SET inventory_count = ? WHERE product_id = ?', (inventory_count, url_id))
				except KeyError:
					pass

			except ValueError:
				return jsonify('Bad input type')

			out = jsonify('Updated')

	return out

# Buying products
# 1. Decrement inventory_count
# 2. Check if product's inventory_count was updated, return 'Purchased', else return custom 404 message
@app.route('/api/products/<int:url_id>/purchase', methods=['POST'])
def purchase(url_id):
	with sqlite3.connect(db_name) as conn:
		cur = conn.cursor()
		cur.execute('''UPDATE products
						SET inventory_count = inventory_count - 1
						WHERE inventory_count > 0 AND product_id=?''', (url_id,))

		if cur.rowcount is 1:
			out = jsonify('Purchased')
		else:
			out = jsonify('Product out of stock'), 404
	return out

# Handle 400 errors - Bad request
@app.errorhandler(400)
def bad_request(e):
	return jsonify('Bad request'), 400

# Handle 404 errors - Page not found
@app.errorhandler(404)
def page_not_found(e):
	return jsonify('Cannot %s %s' % (request.method, request.path)), 404

# Handle 429 errors - Too many requests
@app.errorhandler(429)
def too_many_requests(e):
	return jsonify('Too many requests'), 429

# Handle 500 errors - Internal server error
@app.errorhandler(500)
def internal_server_error(e):
	return jsonify('Internal server error'), 500

@app.route('/')
def main():
	return 'API v1'

if __name__ == '__main__':
	app.run(host='0.0.0.0')