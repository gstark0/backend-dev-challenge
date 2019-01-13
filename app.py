from flask import Flask, jsonify, request, Blueprint, redirect
from utils import dict_factory
from cart import cart_api
import sqlite3

app = Flask(__name__)
app.register_blueprint(cart_api)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

db_name = 'database.db'

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Redirect to HTTPS
@app.before_request
def before_request():
	if not request.is_secure and app.env != "development":
		url = request.url.replace("http://", "https://", 1)
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
		# Column names
		conn.row_factory = dict_factory
		cur = conn.cursor()

		if request.method == 'GET':

			# Query all products if url_id is not specified
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
		elif request.method == 'DELETE':
			if url_id is None:
				cur.execute('DELETE FROM products')
			else:
				cur.execute('DELETE FROM products WHERE product_id=?', (url_id,))

			out = jsonify('deleted')

		# Add a new product to database
		elif request.method == 'POST':

			# Get data from request
			data = request.form.to_dict()
			try:
				title = str(data['title'])
				price = float(data['price'])
				inventory_count = int(data['inventory_count'])

			# Handle KeyError for security reasons - to make sure that you have a correct type
			except ValueError:
				return 'Bad input type'

			# All params are required
			except KeyError:
				return 'title, price and inventory_count are required'

			# Add a new product to the database
			cur.execute('INSERT INTO products (title, price, inventory_count) VALUES (?, ?, ?)', (title, price, inventory_count))
			out = jsonify({'created_resource': '/api/products/%s' % cur.lastrowid}), 201

		# Update a product
		elif request.method == 'PUT':

			# Get data from request and update specified fields
			data = request.form.to_dict()
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
				return 'Bad input type'

			out = jsonify({'updated_resource': '/api/products/%s' % url_id})

	return out

# Buying products
@app.route('/api/products/<int:url_id>/purchase', methods=['POST'])
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