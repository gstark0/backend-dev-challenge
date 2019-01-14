from flask import Blueprint, request, jsonify
from utils import dict_factory
from datetime import datetime
import sqlite3

db_name = 'database.db'

cart_api = Blueprint('cart_api', __name__)

# Complete the cart
@cart_api.route('/api/cart/<int:cart_id>/complete', methods=['POST'])
def complete(cart_id):
	with sqlite3.connect(db_name) as conn:
		cur = conn.cursor()

		# Update product's inventory_count
		cur.execute('''UPDATE products
						SET inventory_count = inventory_count - (SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = products.product_id)
						WHERE product_id = (SELECT product_id FROM cart_items WHERE cart_id = ? AND product_id = products.product_id)''', (cart_id, cart_id))

		# Remove all products from the cart
		cur.execute('DELETE FROM cart_items WHERE cart_id = ?', (cart_id,))

	return jsonify('Cart %s completed' % cart_id)

# Add product to the cart
@cart_api.route('/api/cart/<int:cart_id>', methods=['GET', 'POST'])
def cart(cart_id):

	with sqlite3.connect(db_name) as conn:
		conn.row_factory = dict_factory
		cur = conn.cursor()

		if request.method == 'POST':
			# Get parameters
			data = request.form.to_dict()
			product_id = data['product_id']
			quantity = int(data['quantity'])

			# Create a cart with specified ID if it doesn't already exist
			cur.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,))
			if not cur.fetchone():
				date_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				cur.execute('INSERT INTO carts (cart_id, date_created) VALUES (?, ?)', (cart_id, date_created))

			# Query inventory_count for later use (we will check if the specified quantity doesn't exceed it)
			cur.execute('SELECT inventory_count FROM products WHERE product_id = ?', (product_id,))
			inventory_count = cur.fetchone()['inventory_count']

			# Check if this product has already been added to this cart
			cur.execute('SELECT quantity FROM cart_items WHERE product_id = ?', (product_id))
			cart_quantity = cur.fetchone()
			if cart_quantity:
				# Check if quantity doesn't exceed inventory_count
				if cart_quantity['quantity'] + quantity > inventory_count:
					return jsonify('inventory_count exceeded')

				# Update quantity in the database by the specified value
				cur.execute('UPDATE cart_items SET quantity = quantity + ? WHERE product_id = ?', (quantity, product_id))
			else:
				# Check if quantity doesn't exceed inventory_count
				if quantity > inventory_count:
					return jsonify('inventory_count exceeded')

				# Add an item to the cart
				cur.execute('INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)', (cart_id, product_id, quantity))

		# Query cart by id and calculate total prices
		cur.execute('SELECT products.product_id, products.title, products.price, round(products.price * cart_items.quantity, 2) AS total, cart_items.quantity FROM products JOIN cart_items USING (product_id)')
		out = cur.fetchall()
		total = round(sum(d['total'] for d in out), 2)

	return jsonify({'total': total, 'products': out})
