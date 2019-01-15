from flask import Blueprint, request, jsonify, abort
from utils import dict_factory
from datetime import datetime
import sqlite3

db_name = 'database.db'

cart_api = Blueprint('cart_api', __name__)

# Complete the cart
# 1. Update each product's inventory_count
# 2. Remove all products from the cart
@cart_api.route('/api/cart/<int:cart_id>/complete', methods=['POST'])
def complete(cart_id):
	with sqlite3.connect(db_name) as conn:
		cur = conn.cursor()

		cur.execute('''UPDATE products
						SET inventory_count = inventory_count - (SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = products.product_id)
						WHERE product_id = (SELECT product_id FROM cart_items WHERE cart_id = ? AND product_id = products.product_id)''', (cart_id, cart_id))

		cur.execute('DELETE FROM cart_items WHERE cart_id = ?', (cart_id,))

	return jsonify('Cart %s completed' % cart_id)


# Add product to the cart
# GET to query all products added to the cart along with their total prices
# POST to add a new product to the car
# DELETE to remove all
@cart_api.route('/api/cart/<int:cart_id>', methods=['GET', 'POST', 'GET', 'DELETE'])
def cart(cart_id):
	with sqlite3.connect(db_name) as conn:
		conn.row_factory = dict_factory
		cur = conn.cursor()

		data = request.get_json()

		# Query cart by id and calculate total prices
		if request.method == 'GET':
			cur.execute('SELECT products.product_id, products.title, products.price, round(products.price * cart_items.quantity, 2) AS total, cart_items.quantity FROM products JOIN cart_items USING (product_id) WHERE cart_items.cart_id = ?', (cart_id,))
			out = cur.fetchall()
			total = round(sum(d['total'] for d in out), 2)
			out = jsonify({'total': total, 'products': out})

		elif request.method == 'POST':
			# Get parameters
			if data is None:
				return jsonify('product_id and quantity are required')

			try:
				product_id = int(data['product_id'])
				quantity = int(data['quantity'])

			# Handle KeyError for security reasons - to make sure that you have a correct type
			except ValueError:
				return jsonify('Bad input type')

			# All params are required
			except KeyError:
				return jsonify('product_id and quantity are required')

			# Create a cart with specified ID if it doesn't already exist
			cur.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,))
			if not cur.fetchone():
				date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				cur.execute('INSERT INTO carts (cart_id, date_created) VALUES (?, ?)', (cart_id, date_created))

			# Query inventory_count for later use (we will check if the specified quantity doesn't exceed it)
			cur.execute('SELECT inventory_count FROM products WHERE product_id = ?', (product_id,))
			inventory_count = cur.fetchone()
			if inventory_count is None:
				return jsonify('Product with this ID does not exist')
			inventory_count = inventory_count['inventory_count']

			# Check if this product has already been added to this cart
			cur.execute('SELECT quantity FROM cart_items WHERE product_id = ? AND cart_id = ?', (product_id, cart_id))
			cart_quantity = cur.fetchone()
			if cart_quantity:
				# Check if quantity doesn't exceed inventory_count
				if cart_quantity['quantity'] + quantity > inventory_count:
					return jsonify('inventory_count exceeded')

				# Update quantity in the database by the specified value
				cur.execute('UPDATE cart_items SET quantity = quantity + ? WHERE product_id = ? AND cart_id = ?', (quantity, product_id, cart_id))
			else:
				# Check if quantity doesn't exceed inventory_count
				if quantity > inventory_count:
					return jsonify('inventory_count exceeded')

				# Add an item to the cart
				cur.execute('INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)', (cart_id, product_id, quantity))

			out = jsonify('Product added')

		# Remove product from the cart
		elif request.method == 'DELETE':
			if data is None:
				return abort(400)

			try:
				product_id = data['product_id']
			except KeyError:
				return jsonify('product_id is required')
			cur.execute('DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?', (cart_id, product_id))

			# Check if product was removed
			if cur.rowcount is 1:
				out = jsonify('Deleted')
			else:
				out = jsonify('No such a product in this cart')


	return out
