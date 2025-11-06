
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, abort, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'your-secret-key-change-this-in-production'  # Needed for sessions


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.139.8.30/proj1part2
#
# For example, if you had username ab1234 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://ab1234:123123@34.139.8.30/proj1part2"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "jcw2239"
DATABASE_PASSWRD = "047453"
DATABASE_HOST = "34.139.8.30"
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note: This code was creating a test table with sample data.
# Commented out to use your actual Part 2 database tables instead.
#
# with engine.begin() as conn:
# 	create_table_command = """
# 	CREATE TABLE IF NOT EXISTS test (
# 		id serial,
# 		name text
# 	)
# 	"""
# 	res = conn.execute(text(create_table_command))
# 	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
# 	res = conn.execute(text(insert_table_command))
# 	# engine.begin() automatically commits when the context exits


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
	# Redirect to restaurant directory as the main landing page
	return redirect('/restaurants')

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
# View all restaurants with search/filter functionality
@app.route('/restaurants')
def restaurants():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	# Get filter parameters
	search = request.args.get('search', '').strip()
	cuisine_filter = request.args.get('cuisine', '')
	price_filter = request.args.get('price_range', '')
	location_filter = request.args.get('location', '').strip()
	
	try:
		# Build dynamic query with filters
		base_query = """
		SELECT DISTINCT r.restaurantid, r.name, r.location, r.pricerange
		FROM restaurant r
		LEFT JOIN restaurantcuisine rc ON r.restaurantid = rc.restaurantid
		LEFT JOIN cuisine c ON rc.cuisineid = c.cuisineid
		WHERE 1=1
		"""
		params = {}
		
		if search:
			base_query += " AND r.name ILIKE :search"
			params['search'] = f"%{search}%"
		
		if cuisine_filter:
			base_query += " AND c.cuisinename = :cuisine"
			params['cuisine'] = cuisine_filter
		
		if price_filter:
			base_query += " AND r.pricerange = :price_range"
			params['price_range'] = price_filter
		
		if location_filter:
			base_query += " AND r.location = :location"
			params['location'] = location_filter
		
		base_query += " ORDER BY r.name;"
		
		cursor = g.conn.execute(text(base_query), params)
		restaurants = []
		for result in cursor:
			restaurants.append({
				'id': result[0],
				'name': result[1],
				'address': result[2] if result[2] else 'N/A',
				'price_range': result[3] if result[3] else 'N/A'
			})
		cursor.close()
		
		# Get filter options
		cuisines_query = "SELECT DISTINCT cuisinename FROM cuisine ORDER BY cuisinename;"
		cursor = g.conn.execute(text(cuisines_query))
		cuisines = [row[0] for row in cursor]
		cursor.close()
		
		price_ranges_query = "SELECT DISTINCT pricerange FROM restaurant WHERE pricerange IS NOT NULL ORDER BY pricerange;"
		cursor = g.conn.execute(text(price_ranges_query))
		price_ranges = [row[0] for row in cursor]
		cursor.close()
		
		locations_query = "SELECT DISTINCT location FROM restaurant WHERE location IS NOT NULL ORDER BY location;"
		cursor = g.conn.execute(text(locations_query))
		locations = [row[0] for row in cursor]
		cursor.close()
		
		print(f"Found {len(restaurants)} restaurants")
	except Exception as e:
		print(f"Error querying restaurants: {e}")
		import traceback
		traceback.print_exc()
		restaurants = []
		cuisines = []
		price_ranges = []
		locations = []
	
	context = dict(
		restaurants=restaurants,
		cuisines=cuisines,
		price_ranges=price_ranges,
		locations=locations,
		filters={
			'search': search,
			'cuisine': cuisine_filter,
			'price_range': price_filter,
			'location': location_filter
		}
	)
	return render_template("restaurants.html", **context)

# View restaurant details - shows all relationships
@app.route('/restaurants/<int:restaurant_id>')
def restaurant_details(restaurant_id):
	# Set search path like the home page does
	g.conn.execute(text(f"SET search_path TO jcw2239, public;"))
	
	try:
		# Schema has: RestaurantID, Name, Location, PriceRange
		# PostgreSQL converts to lowercase: restaurantid, name, location, pricerange
		select_query = "SELECT restaurantid, name, location FROM restaurant WHERE restaurantid = :id;"
		cursor = g.conn.execute(text(select_query), {'id': restaurant_id})
		restaurant = cursor.fetchone()
		cursor.close()
		
		if not restaurant:
			return "Restaurant not found", 404
		
		restaurant_info = {
			'id': restaurant[0],
			'name': restaurant[1],
			'address': restaurant[2] if restaurant[2] else 'N/A'
		}
		
		# Get dishes for this restaurant (including price)
		dishes_query = "SELECT dishid, name, COALESCE(price, 0.0) as price FROM dish WHERE restaurantid = :id ORDER BY name;"
		cursor = g.conn.execute(text(dishes_query), {'id': restaurant_id})
		dishes = []
		for result in cursor:
			dishes.append({
				'id': result[0], 
				'name': result[1],
				'price': float(result[2]) if result[2] else None
			})
		cursor.close()
		
		# Get reviews for this restaurant
		# Schema has: ReviewID, Rating, Comment, UserID, RestaurantID (no date column)
		reviews_query = """
		SELECT reviewid, userid, rating, comment 
		FROM review 
		WHERE restaurantid = :id 
		ORDER BY reviewid DESC;
		"""
		cursor = g.conn.execute(text(reviews_query), {'id': restaurant_id})
		reviews = []
		for result in cursor:
			reviews.append({
				'id': result[0],
				'user_id': result[1],
				'rating': result[2] if result[2] else 'N/A',
				'text': result[3] if result[3] else 'No text'
			})
		cursor.close()
		
		# Get cuisines for this restaurant (through restaurantcuisine table)
		# Schema uses CuisineName (PostgreSQL converts to lowercase: cuisinename)
		cuisines_query = """
		SELECT c.cuisineid, c.cuisinename as cuisine_name
		FROM cuisine c
		JOIN restaurantcuisine rc ON c.cuisineid = rc.cuisineid
		WHERE rc.restaurantid = :id
		ORDER BY c.cuisinename;
		"""
		cursor = g.conn.execute(text(cuisines_query), {'id': restaurant_id})
		cuisines = []
		for result in cursor:
			cuisines.append({'id': result[0], 'name': result[1]})
		cursor.close()
		
		# Get orders for this restaurant
		# Schema has: OrderID, Date, TotalPrice, UserID, RestaurantID
		# PostgreSQL converts to lowercase: orderid, date, totalprice, userid, restaurantid
		orders_query = """
		SELECT orderid, userid, date, totalprice 
		FROM orders 
		WHERE restaurantid = :id 
		ORDER BY date DESC;
		"""
		cursor = g.conn.execute(text(orders_query), {'id': restaurant_id})
		orders = []
		for result in cursor:
			orders.append({
				'id': result[0],
				'user_id': result[1],
				'date': result[2] if result[2] else 'N/A',
				'total': result[3] if result[3] else 'N/A'
			})
		cursor.close()
		
	except Exception as e:
		print(f"Error querying restaurant details: {e}")
		import traceback
		traceback.print_exc()
		return f"Error: {e}", 500
	
	context = dict(
		restaurant=restaurant_info,
		dishes=dishes,
		reviews=reviews,
		cuisines=cuisines,
		orders=orders
	)
	return render_template("restaurant_details.html", **context)


# View all users
@app.route('/users')
def users():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	try:
		# Schema has: UserID, Name, Username, Password, Role (NO email)
		# PostgreSQL converts to lowercase: userid, name, username, password, role
		select_query = "SELECT userid, username FROM users ORDER BY username;"
		cursor = g.conn.execute(text(select_query))
		users_list = []
		for result in cursor:
			users_list.append({
				'id': result[0],
				'username': result[1]
			})
		cursor.close()
		print(f"Found {len(users_list)} users")
	except Exception as e:
		print(f"Error querying users: {e}")
		import traceback
		traceback.print_exc()
		users_list = []
	
	context = dict(users=users_list)
	return render_template("users.html", **context)

# View all dishes (across all restaurants)
@app.route('/dishes')
def dishes():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	try:
		# Schema has: DishID, Name, Ingredients, RestaurantID, Price
		# PostgreSQL converts to lowercase: dishid, name, ingredients, restaurantid, price
		select_query = """
		SELECT d.dishid, d.name, d.restaurantid, d.price, r.name as restaurant_name
		FROM dish d
		LEFT JOIN restaurant r ON d.restaurantid = r.restaurantid
		ORDER BY d.name;
		"""
		cursor = g.conn.execute(text(select_query))
		
		dishes = []
		for result in cursor:
			dishes.append({
				'id': result[0],
				'name': result[1],
				'restaurant_id': result[2],
				'price': float(result[3]) if result[3] else None,
				'restaurant_name': result[4] if result[4] else 'N/A'
			})
		
		cursor.close()
		print(f"Found {len(dishes)} dishes")
	except Exception as e:
		print(f"Error querying dishes: {e}")
		import traceback
		traceback.print_exc()
		dishes = []
	
	context = dict(dishes=dishes)
	return render_template("dishes.html", **context)

# View all orders (across all restaurants)
@app.route('/orders')
def orders():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	try:
		# Schema has: OrderID, Date, TotalPrice, UserID, RestaurantID
		# PostgreSQL converts to lowercase: orderid, date, totalprice, userid, restaurantid
		select_query = """
		SELECT o.orderid, o.userid, o.restaurantid, o.date, o.totalprice,
		       r.name as restaurant_name, u.username
		FROM orders o
		LEFT JOIN restaurant r ON o.restaurantid = r.restaurantid
		LEFT JOIN users u ON o.userid = u.userid
		ORDER BY o.date DESC;
		"""
		cursor = g.conn.execute(text(select_query))
		
		orders_list = []
		for result in cursor:
			orders_list.append({
				'id': result[0],
				'user_id': result[1],
				'restaurant_id': result[2],
				'date': result[3] if result[3] else 'N/A',
				'total': result[4] if result[4] else 'N/A',
				'restaurant_name': result[5] if result[5] else 'N/A',
				'username': result[6] if result[6] else 'N/A'
			})
		cursor.close()
		
		print(f"Found {len(orders_list)} orders")
	except Exception as e:
		print(f"Error querying orders: {e}")
		import traceback
		traceback.print_exc()
		orders_list = []
	
	context = dict(orders=orders_list)
	return render_template("orders.html", **context)

# View order details - shows order items
@app.route('/orders/<int:order_id>')
def order_details(order_id):
	g.conn.execute(text(f"SET search_path TO jcw2239, public;"))
	
	try:
		# Get order info
		# Schema has: OrderID, Date, TotalPrice, UserID, RestaurantID
		order_query = """
		SELECT o.orderid, o.userid, o.restaurantid, o.date, o.totalprice,
		       r.name as restaurant_name, u.username
		FROM orders o
		LEFT JOIN restaurant r ON o.restaurantid = r.restaurantid
		LEFT JOIN users u ON o.userid = u.userid
		WHERE o.orderid = :id;
		"""
		cursor = g.conn.execute(text(order_query), {'id': order_id})
		order = cursor.fetchone()
		cursor.close()
		
		if not order:
			return "Order not found", 404
		
		order_info = {
			'id': order[0],
			'user_id': order[1],
			'restaurant_id': order[2],
			'date': order[3] if order[3] else 'N/A',
			'total': order[4] if order[4] else 'N/A',
			'restaurant_name': order[5] if order[5] else 'N/A',
			'username': order[6] if order[6] else 'N/A'
		}
		
		# Get order items
		items_query = """
		SELECT oi.orderitemid, oi.dishid, oi.quantity,
		       d.name as dish_name
		FROM orderitem oi
		LEFT JOIN dish d ON oi.dishid = d.dishid
		WHERE oi.orderid = :id;
		"""
		cursor = g.conn.execute(text(items_query), {'id': order_id})
		items = []
		for result in cursor:
			items.append({
				'id': result[0],
				'dish_id': result[1],
				'quantity': result[2],
				'dish_name': result[3] if result[3] else 'N/A'
			})
		cursor.close()
		
	except Exception as e:
		print(f"Error querying order details: {e}")
		import traceback
		traceback.print_exc()
		return f"Error: {e}", 500
	
	context = dict(order=order_info, items=items)
	return render_template("order_details.html", **context)

# View all reviews (across all restaurants)
@app.route('/reviews')
def reviews():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	try:
		# Schema: ReviewID, Rating, Comment, UserID, RestaurantID (no date)
		# PostgreSQL converts to lowercase: reviewid, rating, comment, userid, restaurantid
		select_query = """
		SELECT r.reviewid, r.userid, r.restaurantid, r.rating, r.comment,
		       rest.name as restaurant_name, u.username
		FROM review r
		LEFT JOIN restaurant rest ON r.restaurantid = rest.restaurantid
		LEFT JOIN users u ON r.userid = u.userid
		ORDER BY r.reviewid DESC;
		"""
		cursor = g.conn.execute(text(select_query))
		reviews_list = []
		for result in cursor:
			review_dict = {
				'id': result[0],
				'user_id': result[1],
				'restaurant_id': result[2],
				'rating': result[3] if result[3] else 'N/A',
				'text': result[4] if result[4] else 'No text',
				'restaurant_name': result[5] if result[5] else 'N/A',
				'username': result[6] if result[6] else 'N/A',
				'date': 'N/A'  # No date column in schema
			}
			reviews_list.append(review_dict)
		cursor.close()
		print(f"Found {len(reviews_list)} reviews")
		if len(reviews_list) > 0:
			print(f"Sample review: {reviews_list[0]}")
	except Exception as e:
		print(f"Error querying reviews: {e}")
		import traceback
		traceback.print_exc()
		reviews_list = []
	
	context = dict(reviews=reviews_list)
	return render_template("reviews.html", **context)

# View all cuisines (global list)
@app.route('/cuisines')
def cuisines():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	try:
		# Schema has: CuisineID, CuisineName
		# PostgreSQL converts to lowercase: cuisineid, cuisinename
		select_query = "SELECT cuisineid, cuisinename FROM cuisine ORDER BY cuisinename;"
		cursor = g.conn.execute(text(select_query))
		cuisines_list = []
		for result in cursor:
			cuisines_list.append({
				'id': result[0],
				'name': result[1]
			})
		cursor.close()
		print(f"Found {len(cuisines_list)} cuisines")
		if len(cuisines_list) > 0:
			print(f"Sample cuisine: {cuisines_list[0]}")
	except Exception as e:
		print(f"Error querying cuisines: {e}")
		import traceback
		traceback.print_exc()
		cuisines_list = []
	
	context = dict(cuisines=cuisines_list)
	return render_template("cuisines.html", **context)


# Helper function to check user role
def check_user_role(user_id, required_roles):
	"""Check if user_id has one of the required roles. Returns (has_access, role)"""
	if not user_id:
		return False, None
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	try:
		query = "SELECT role FROM users WHERE userid = :user_id;"
		cursor = g.conn.execute(text(query), {'user_id': user_id})
		result = cursor.fetchone()
		cursor.close()
		if result:
			user_role = result[0]
			return user_role in required_roles, user_role
		return False, None
	except Exception as e:
		print(f"Error checking user role: {e}")
		return False, None

# Helper function to verify logged-in user can perform action
def verify_user_access(required_roles):
	"""Check if currently logged-in user (from session) has required role. Returns (has_access, user_id, role)"""
	user_id = session.get('user_id')
	if not user_id:
		return False, None, None
	has_access, role = check_user_role(user_id, required_roles)
	return has_access, user_id, role


# Add Restaurant (Admin only)
@app.route('/restaurants/add', methods=['GET', 'POST'])
def add_restaurant():
	# Check login and role
	check_result = require_login_check(required_roles=['Admin'])
	if check_result:
		return check_result
	
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	if request.method == 'POST':
		# Use logged-in user from session
		user_id = session.get('user_id')
		
		name = request.form.get('name', '').strip()
		location = request.form.get('location', '').strip() or None
		price_range = request.form.get('price_range', '').strip() or None
		
		if not name:
			return "Error: Restaurant name is required", 400
		
		try:
			with g.conn.begin():
				insert_query = """
				INSERT INTO restaurant (name, location, pricerange)
				VALUES (:name, :location, :price_range)
				RETURNING restaurantid;
				"""
				cursor = g.conn.execute(text(insert_query), {
					'name': name,
					'location': location,
					'price_range': price_range
				})
				restaurant_id = cursor.fetchone()[0]
				cursor.close()
			return redirect(f'/restaurants/{restaurant_id}')
		except Exception as e:
			print(f"Error adding restaurant: {e}")
			import traceback
			traceback.print_exc()
			return f"Error: {e}", 500
	
	# GET: Show form
	context = dict(current_user={'id': session.get('user_id'), 'username': session.get('username')})
	return render_template("add_restaurant.html", **context)


# Add Dish (Admin only)
@app.route('/restaurants/<int:restaurant_id>/add-dish', methods=['GET', 'POST'])
def add_dish(restaurant_id):
	# Check login and role
	check_result = require_login_check(required_roles=['Admin'])
	if check_result:
		return check_result
	
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	if request.method == 'POST':
		# Use logged-in user from session
		user_id = session.get('user_id')
		
		name = request.form.get('name', '').strip()
		ingredients = request.form.get('ingredients', '').strip() or None
		price_str = request.form.get('price', '').strip()
		price = float(price_str) if price_str else None
		
		if not name:
			return "Error: Dish name is required", 400
		
		try:
			with g.conn.begin():
				insert_query = """
				INSERT INTO dish (name, ingredients, restaurantid, price)
				VALUES (:name, :ingredients, :restaurant_id, :price)
				RETURNING dishid;
				"""
				cursor = g.conn.execute(text(insert_query), {
					'name': name,
					'ingredients': ingredients,
					'restaurant_id': restaurant_id,
					'price': price
				})
				dish_id = cursor.fetchone()[0]
				cursor.close()
			return redirect(f'/restaurants/{restaurant_id}')
		except Exception as e:
			print(f"Error adding dish: {e}")
			import traceback
			traceback.print_exc()
			return f"Error: {e}", 500
	
	# GET: Show form
	try:
		# Get restaurant info
		rest_query = "SELECT restaurantid, name FROM restaurant WHERE restaurantid = :id;"
		cursor = g.conn.execute(text(rest_query), {'id': restaurant_id})
		restaurant = cursor.fetchone()
		cursor.close()
		
		if not restaurant:
			return "Restaurant not found", 404
	except Exception as e:
		return f"Error: {e}", 500
	
	context = dict(restaurant={'id': restaurant[0], 'name': restaurant[1]}, 
	               current_user={'id': session.get('user_id'), 'username': session.get('username')})
	return render_template("add_dish.html", **context)


# Add Review (Admin or Customer)
@app.route('/restaurants/<int:restaurant_id>/add-review', methods=['GET', 'POST'])
def add_review(restaurant_id):
	# Check login and role
	check_result = require_login_check(required_roles=['Admin', 'Cust'])
	if check_result:
		return check_result
	
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	if request.method == 'POST':
		# Use logged-in user from session
		user_id = session.get('user_id')
		
		rating = request.form.get('rating', type=int)
		comment = request.form.get('comment', '').strip() or None
		
		if not rating or rating < 1 or rating > 5:
			return "Error: Rating must be between 1 and 5", 400
		
		try:
			with g.conn.begin():
				insert_query = """
				INSERT INTO review (rating, comment, userid, restaurantid)
				VALUES (:rating, :comment, :user_id, :restaurant_id)
				RETURNING reviewid;
				"""
				cursor = g.conn.execute(text(insert_query), {
					'rating': rating,
					'comment': comment,
					'user_id': user_id,
					'restaurant_id': restaurant_id
				})
				review_id = cursor.fetchone()[0]
				cursor.close()
			return redirect(f'/restaurants/{restaurant_id}')
		except Exception as e:
			print(f"Error adding review: {e}")
			import traceback
			traceback.print_exc()
			return f"Error: {e}", 500
	
	# GET: Show form
	try:
		# Get restaurant info
		rest_query = "SELECT restaurantid, name FROM restaurant WHERE restaurantid = :id;"
		cursor = g.conn.execute(text(rest_query), {'id': restaurant_id})
		restaurant = cursor.fetchone()
		cursor.close()
		
		if not restaurant:
			return "Restaurant not found", 404
	except Exception as e:
		return f"Error: {e}", 500
	
	context = dict(restaurant={'id': restaurant[0], 'name': restaurant[1]},
	               current_user={'id': session.get('user_id'), 'username': session.get('username')})
	return render_template("add_review.html", **context)


# Create Order (Admin or Customer)
@app.route('/restaurants/<int:restaurant_id>/add-order', methods=['GET', 'POST'])
def create_order(restaurant_id):
	# Check login and role
	check_result = require_login_check(required_roles=['Admin', 'Cust'])
	if check_result:
		return check_result
	
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	if request.method == 'POST':
		# Use logged-in user from session
		user_id = session.get('user_id')
		
		if not user_id:
			return "Error: You must be logged in to create an order", 400
		
		# Verify user exists in database (commit any pending transaction first)
		try:
			g.conn.commit()
		except:
			pass  # If no transaction, that's fine
		
		user_check = "SELECT userid FROM users WHERE userid = :user_id;"
		cursor = g.conn.execute(text(user_check), {'user_id': user_id})
		user_exists = cursor.fetchone()
		cursor.close()
		
		# Commit the user check query
		try:
			g.conn.commit()
		except:
			pass
		
		if not user_exists:
			return f"Error: User ID {user_id} not found in database. Please log out and log back in.", 400
		
		# Get dish IDs and quantities from form
		dish_ids = request.form.getlist('dish_id[]')
		quantities = request.form.getlist('quantity[]')
		
		if not dish_ids or not all(dish_ids):
			return "Error: At least one dish is required", 400
		
		try:
			# Calculate total price
			total_price = 0
			order_items = []
			
			for dish_id_str, quantity_str in zip(dish_ids, quantities):
				if not dish_id_str or not quantity_str:
					continue
				dish_id = int(dish_id_str)
				quantity = int(quantity_str)
				
				if quantity <= 0:
					continue
				
				# Get dish price from dish table (current price)
				# This preserves the price at the time of order
				price_query = "SELECT COALESCE(price, 0.0) FROM dish WHERE dishid = :dish_id;"
				cursor = g.conn.execute(text(price_query), {'dish_id': dish_id})
				price_result = cursor.fetchone()
				price = float(price_result[0]) if price_result and price_result[0] else 0.0
				cursor.close()
				
				order_items.append({
					'dish_id': dish_id,
					'quantity': quantity,
					'price': price
				})
				total_price += price * quantity
			
			if not order_items:
				return "Error: At least one valid dish with quantity > 0 is required", 400
			
			# Commit any pending queries before starting transaction
			try:
				g.conn.commit()
			except:
				pass
			
			# Create order and items in a transaction
			trans = g.conn.begin()
			try:
				# Create order
				order_query = """
				INSERT INTO orders (userid, restaurantid, totalprice)
				VALUES (:user_id, :restaurant_id, :total_price)
				RETURNING orderid;
				"""
				cursor = g.conn.execute(text(order_query), {
					'user_id': user_id,
					'restaurant_id': restaurant_id,
					'total_price': total_price
				})
				order_id = cursor.fetchone()[0]
				cursor.close()
				
				# Add order items
				for item in order_items:
					item_query = """
					INSERT INTO orderitem (orderid, dishid, quantity, price)
					VALUES (:order_id, :dish_id, :quantity, :price);
					"""
					g.conn.execute(text(item_query), {
						'order_id': order_id,
						'dish_id': item['dish_id'],
						'quantity': item['quantity'],
						'price': item['price']
					})
				
				# Commit the transaction
				trans.commit()
			except Exception as e:
				# Rollback on error
				trans.rollback()
				raise e
			
			return redirect(f'/orders/{order_id}')
		except Exception as e:
			print(f"Error creating order: {e}")
			import traceback
			traceback.print_exc()
			error_msg = str(e)
			# Check for common constraint violations
			if "foreign key" in error_msg.lower() or "violates foreign key constraint" in error_msg.lower():
				if "userid" in error_msg.lower():
					return f"Error: Your user account (ID: {user_id}) is not valid. Please log out and log back in. Full error: {error_msg}", 400
				elif "dishid" in error_msg.lower():
					return f"Error: One or more dishes are invalid. Please refresh the page and try again. Full error: {error_msg}", 400
				elif "restaurantid" in error_msg.lower():
					return f"Error: Restaurant (ID: {restaurant_id}) is not valid. Full error: {error_msg}", 400
			return f"Error creating order: {error_msg}", 500
	
	# GET: Show form
	try:
		# Get restaurant info
		rest_query = "SELECT restaurantid, name FROM restaurant WHERE restaurantid = :id;"
		cursor = g.conn.execute(text(rest_query), {'id': restaurant_id})
		restaurant = cursor.fetchone()
		cursor.close()
		
		if not restaurant:
			return "Restaurant not found", 404
		
		# Get dishes for this restaurant (including price)
		dishes_query = """
		SELECT dishid, name, COALESCE(price, 0.0) as price
		FROM dish 
		WHERE restaurantid = :id 
		ORDER BY name;
		"""
		cursor = g.conn.execute(text(dishes_query), {'id': restaurant_id})
		dishes = []
		for row in cursor:
			dishes.append({
				'id': row[0], 
				'name': row[1],
				'price': float(row[2]) if row[2] else 0.0
			})
		cursor.close()
	except Exception as e:
		return f"Error: {e}", 500
	
	context = dict(restaurant={'id': restaurant[0], 'name': restaurant[1]}, dishes=dishes,
	               current_user={'id': session.get('user_id'), 'username': session.get('username')})
	return render_template("create_order.html", **context)


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	if request.method == 'POST':
		username = request.form.get('username', '').strip()
		password = request.form.get('password', '').strip()
		
		if not username or not password:
			return render_template("login.html", error="Username and password are required")
		
		try:
			# Check credentials
			query = "SELECT userid, username, role FROM users WHERE username = :username AND password = :password;"
			cursor = g.conn.execute(text(query), {'username': username, 'password': password})
			user = cursor.fetchone()
			cursor.close()
			
			if user:
				session['user_id'] = user[0]
				session['username'] = user[1]
				session['role'] = user[2]
				return redirect(request.args.get('next', '/'))
			else:
				return render_template("login.html", error="Invalid username or password")
		except Exception as e:
			print(f"Error during login: {e}")
			return render_template("login.html", error="Login error occurred")
	
	# GET: Show login form
	return render_template("login.html")

# Logout
@app.route('/logout')
def logout():
	session.clear()
	return redirect('/')

# Require login wrapper function
def require_login_check(required_roles=None):
	"""Check if user is logged in and has required role"""
	if 'user_id' not in session:
		return redirect(f'/login?next={request.url}')
	if required_roles:
		has_access, user_id, role = verify_user_access(required_roles)
		if not has_access:
			return f"Access denied: This action requires {', '.join(required_roles)} role", 403
	return None  # Access granted


if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
