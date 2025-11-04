
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
from flask import Flask, request, render_template, g, redirect, Response, abort

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


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
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)

	#
	# Find all your tables in the database - check all schemas
	#
	# Get database name
	db_query = "SELECT current_database();"
	cursor = g.conn.execute(text(db_query))
	db_name = cursor.fetchone()[0]
	cursor.close()
	
	# Get all tables from all schemas
	tables_query = """
	SELECT table_schema, table_name 
	FROM information_schema.tables 
	WHERE table_type = 'BASE TABLE'
	AND table_schema NOT IN ('information_schema', 'pg_catalog')
	ORDER BY table_schema, table_name;
	"""
	cursor = g.conn.execute(text(tables_query))
	all_tables = []
	public_tables = []
	for result in cursor:
		schema, table = result[0], result[1]
		all_tables.append(f"{schema}.{table}")
		if schema == 'public':
			public_tables.append(table)
	cursor.close()
	
	print(f"Connected to database: {db_name}")
	print(f"Tables in 'public' schema: {public_tables}")
	if len(all_tables) > len(public_tables):
		print(f"Tables in other schemas: {[t for t in all_tables if not t.startswith('public.')]}")
	
	#
	# Query your actual data - using your restaurant tables
	#
	# Set the search path to your schema so we can use table names directly
	g.conn.execute(text(f"SET search_path TO jcw2239, public;"))
	
	# Query one of your actual tables - let's start with restaurant
	# Change this to query different tables: cuisine, dish, users, orders, etc.
	try:
		select_query = "SELECT name FROM restaurant LIMIT 10;"
		cursor = g.conn.execute(text(select_query))
		names = []
		for result in cursor:
			names.append(result[0])
		cursor.close()
			
		if len(names) == 0:
			names = ["No restaurants found in the database."]
		else:
			names.insert(0, f"Restaurants ({len(names)} shown):")
	except Exception as e:
		print(f"Error querying restaurant table: {e}")
		# Fallback: show table list
		names = [f"📊 Found {len(all_tables)} table(s) in database '{db_name}':"]
		for table in all_tables:
			names.append(f"  - {table}")
		names.append("")
		names.append(f"Error querying restaurant table: {e}")

	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
	context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
	return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
# View all restaurants
@app.route('/restaurants')
def restaurants():
	# Set search path to your schema
	g.conn.execute(text("SET search_path TO jcw2239, public;"))
	
	try:
		# First, let's see what columns exist in the restaurant table
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'restaurant'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		print(f"Restaurant table columns: {columns}")
		
		# Query all restaurants - try to get all columns first
		select_query = "SELECT * FROM restaurant ORDER BY name;"
		cursor = g.conn.execute(text(select_query))
		restaurants = []
		for result in cursor:
			# Try to map the columns - adjust based on your actual schema
			restaurant_dict = {}
			for i, col in enumerate(columns):
				if col == 'restaurantid' or col == 'restaurant_id':
					restaurant_dict['id'] = result[i]
				elif col == 'name':
					restaurant_dict['name'] = result[i]
				elif 'address' in col.lower() or 'location' in col.lower():
					restaurant_dict['address'] = result[i] if result[i] else 'N/A'
				else:
					restaurant_dict[col] = result[i] if result[i] else 'N/A'
			
			# Fallback: if we don't have the expected columns, just use what we have
			if 'id' not in restaurant_dict:
				restaurant_dict['id'] = result[0] if len(result) > 0 else 'N/A'
			if 'name' not in restaurant_dict:
				restaurant_dict['name'] = result[1] if len(result) > 1 else 'N/A'
			if 'address' not in restaurant_dict:
				restaurant_dict['address'] = result[2] if len(result) > 2 else 'N/A'
			
			restaurants.append(restaurant_dict)
		cursor.close()
		
		print(f"Found {len(restaurants)} restaurants")
	except Exception as e:
		print(f"Error querying restaurants: {e}")
		import traceback
		traceback.print_exc()
		restaurants = []
	
	context = dict(restaurants=restaurants)
	return render_template("restaurants.html", **context)

# View restaurant details - shows all relationships
@app.route('/restaurants/<int:restaurant_id>')
def restaurant_details(restaurant_id):
	# Set search path like the home page does
	g.conn.execute(text(f"SET search_path TO jcw2239, public;"))
	
	try:
		# Get restaurant column names dynamically
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'restaurant'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		
		# Find ID and name columns
		rest_id_col = 'restaurantid'
		name_col = 'name'
		address_col = None
		
		for col in columns:
			if 'id' in col.lower() and 'restaurant' in col.lower():
				rest_id_col = col
			elif col == 'name':
				name_col = col
			elif 'address' in col.lower() or 'location' in col.lower():
				address_col = col
				break
		
		print(f"Restaurant columns: {columns}")
		print(f"Address/location column: {address_col}")
		
		# Build query with available columns
		if address_col:
			select_query = f"SELECT {rest_id_col}, {name_col}, {address_col} FROM restaurant WHERE {rest_id_col} = :id;"
		else:
			select_query = f"SELECT {rest_id_col}, {name_col} FROM restaurant WHERE {rest_id_col} = :id;"
		
		cursor = g.conn.execute(text(select_query), {'id': restaurant_id})
		restaurant = cursor.fetchone()
		cursor.close()
		
		if not restaurant:
			return "Restaurant not found", 404
		
		restaurant_info = {
			'id': restaurant[0],
			'name': restaurant[1]
		}
		
		# Add address/location if it exists
		if address_col and len(restaurant) > 2:
			restaurant_info['address'] = restaurant[2] if restaurant[2] else 'N/A'
		else:
			restaurant_info['address'] = 'N/A'
		
		# Get dishes for this restaurant
		dishes_query = "SELECT dishid, name FROM dish WHERE restaurantid = :id ORDER BY name;"
		cursor = g.conn.execute(text(dishes_query), {'id': restaurant_id})
		dishes = []
		for result in cursor:
			dishes.append({'id': result[0], 'name': result[1]})
		cursor.close()
		
		# Get reviews for this restaurant - use dynamic column discovery
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
		# Get column names dynamically
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'users'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		print(f"Users table columns: {columns}")
		
		select_query = "SELECT * FROM users ORDER BY username;"
		cursor = g.conn.execute(text(select_query))
		users_list = []
		for result in cursor:
			user_dict = {}
			for i, col in enumerate(columns):
				if col == 'userid' or col == 'user_id':
					user_dict['id'] = result[i]
				elif col == 'username':
					user_dict['username'] = result[i]
				elif col == 'email':
					user_dict['email'] = result[i] if result[i] else 'N/A'
				else:
					user_dict[col] = result[i] if result[i] else 'N/A'
			
			if 'id' not in user_dict:
				user_dict['id'] = result[0] if len(result) > 0 else 'N/A'
			if 'username' not in user_dict:
				user_dict['username'] = result[1] if len(result) > 1 else 'N/A'
			if 'email' not in user_dict:
				user_dict['email'] = result[2] if len(result) > 2 else 'N/A'
			
			users_list.append(user_dict)
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
		# Get column names dynamically
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'dish'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		print(f"Dish table columns: {columns}")
		print(f"ALL DISH COLUMNS: {[col for col in columns]}")
		
		# Get restaurant column name for JOIN
		rest_columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'restaurant'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(rest_columns_query))
		rest_columns = [row[0] for row in cursor]
		cursor.close()
		
		# Find the ID column names
		dish_id_col = 'dishid'
		rest_id_col = 'restaurantid'
		for col in columns:
			if 'id' in col.lower() and 'restaurant' not in col.lower():
				dish_id_col = col
				break
		for col in rest_columns:
			if 'id' in col.lower() and 'restaurant' in col.lower():
				rest_id_col = col
				break
		
		# Find restaurant name column
		rest_name_col = 'name'
		for col in rest_columns:
			if col == 'name':
				rest_name_col = col
				break
		
		# Find the restaurant FK column in dish table
		rest_fk_col = 'restaurantid'
		for col in columns:
			if 'restaurant' in col.lower() and 'id' in col.lower():
				rest_fk_col = col
				break
		
		# Use JOIN to get restaurant name
		select_query = f"""
		SELECT d.*, r.{rest_name_col} as restaurant_name
		FROM dish d
		LEFT JOIN restaurant r ON d.{rest_fk_col} = r.{rest_id_col}
		ORDER BY d.name;
		"""
		cursor = g.conn.execute(text(select_query))
		
		# Get result columns (including the joined restaurant_name)
		result_columns = columns + ['restaurant_name']
		
		dishes = []
		for result in cursor:
			dish_dict = {}
			# Map all columns first
			for i, col in enumerate(columns):
				if col == dish_id_col or col == 'dish_id':
					dish_dict['id'] = result[i]
				elif col == 'name':
					dish_dict['name'] = result[i]
				elif col == rest_fk_col or ('restaurant' in col.lower() and 'id' in col.lower()):
					dish_dict['restaurant_id'] = result[i]
			
			# Get restaurant_name from the last column (the JOIN result)
			if len(result) > len(columns):
				dish_dict['restaurant_name'] = result[len(columns)] if result[len(columns)] else 'N/A'
			else:
				dish_dict['restaurant_name'] = 'N/A'
			
			# Fallbacks - ensure we have all required fields
			if 'id' not in dish_dict:
				dish_dict['id'] = result[0] if len(result) > 0 else 'N/A'
			if 'name' not in dish_dict:
				# Find name column
				for i, col in enumerate(columns):
					if col == 'name':
						dish_dict['name'] = result[i] if result[i] else 'N/A'
						break
				if 'name' not in dish_dict:
					dish_dict['name'] = result[1] if len(result) > 1 else 'N/A'
			if 'restaurant_id' not in dish_dict:
				for i, col in enumerate(columns):
					if 'restaurant' in col.lower() and 'id' in col.lower():
						dish_dict['restaurant_id'] = result[i] if result[i] else 'N/A'
						break
			
			dishes.append(dish_dict)
		
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
		# Get column names dynamically
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'orders'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		print(f"Orders table columns: {columns}")
		
		# Get restaurant and user column names for JOINs
		rest_columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'restaurant'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(rest_columns_query))
		rest_columns = [row[0] for row in cursor]
		cursor.close()
		
		user_columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'users'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(user_columns_query))
		user_columns = [row[0] for row in cursor]
		cursor.close()
		
		# Find ID and name columns
		order_id_col = 'orderid'
		rest_id_col = 'restaurantid'
		user_id_col = 'userid'
		rest_name_col = 'name'
		user_name_col = 'username'
		date_col = 'orderdate'
		
		for col in columns:
			if 'id' in col.lower() and 'order' in col.lower():
				order_id_col = col
			elif 'date' in col.lower():
				date_col = col
		
		for col in rest_columns:
			if 'id' in col.lower() and 'restaurant' in col.lower():
				rest_id_col = col
			elif col == 'name':
				rest_name_col = col
		
		for col in user_columns:
			if 'id' in col.lower() and 'user' in col.lower():
				user_id_col = col
			elif 'username' in col.lower() or col == 'name':
				user_name_col = col
		
		# Find FK columns in orders table
		rest_fk_col = 'restaurantid'
		user_fk_col = 'userid'
		for col in columns:
			if 'restaurant' in col.lower() and 'id' in col.lower():
				rest_fk_col = col
			elif 'user' in col.lower() and 'id' in col.lower():
				user_fk_col = col
		
		# Use JOIN to get restaurant and user names
		select_query = f"""
		SELECT o.*, r.{rest_name_col} as restaurant_name, u.{user_name_col} as username
		FROM orders o
		LEFT JOIN restaurant r ON o.{rest_fk_col} = r.{rest_id_col}
		LEFT JOIN users u ON o.{user_fk_col} = u.{user_id_col}
		ORDER BY o.{date_col} DESC;
		"""
		cursor = g.conn.execute(text(select_query))
		
		orders_list = []
		for result in cursor:
			order_dict = {}
			# Map order columns
			for i, col in enumerate(columns):
				if col == order_id_col or col == 'order_id':
					order_dict['id'] = result[i]
				elif col == user_fk_col or ('user' in col.lower() and 'id' in col.lower()):
					order_dict['user_id'] = result[i]
				elif col == rest_fk_col or ('restaurant' in col.lower() and 'id' in col.lower()):
					order_dict['restaurant_id'] = result[i]
				elif 'date' in col.lower():
					order_dict['date'] = result[i] if result[i] else 'N/A'
				elif 'total' in col.lower() or 'amount' in col.lower():
					order_dict['total'] = result[i] if result[i] else 'N/A'
			
			# Get restaurant_name and username from JOIN results (last 2 columns)
			if len(result) > len(columns):
				order_dict['restaurant_name'] = result[len(columns)] if result[len(columns)] else 'N/A'
			else:
				order_dict['restaurant_name'] = 'N/A'
			if len(result) > len(columns) + 1:
				order_dict['username'] = result[len(columns) + 1] if result[len(columns) + 1] else 'N/A'
			else:
				order_dict['username'] = 'N/A'
			
			# Fallbacks
			if 'id' not in order_dict:
				order_dict['id'] = result[0] if len(result) > 0 else 'N/A'
			if 'user_id' not in order_dict:
				for i, col in enumerate(columns):
					if 'user' in col.lower() and 'id' in col.lower():
						order_dict['user_id'] = result[i] if result[i] else 'N/A'
						break
			if 'restaurant_id' not in order_dict:
				for i, col in enumerate(columns):
					if 'restaurant' in col.lower() and 'id' in col.lower():
						order_dict['restaurant_id'] = result[i] if result[i] else 'N/A'
						break
			if 'date' not in order_dict:
				for i, col in enumerate(columns):
					if 'date' in col.lower():
						order_dict['date'] = result[i] if result[i] else 'N/A'
						break
			if 'total' not in order_dict:
				for i, col in enumerate(columns):
					if 'total' in col.lower() or 'amount' in col.lower():
						order_dict['total'] = result[i] if result[i] else 'N/A'
						break
			
			orders_list.append(order_dict)
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
		# Get column names dynamically for review table
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'review'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		print(f"Review table columns: {columns}")
		
		# Use JOIN to get restaurant name and username
		# Schema: ReviewID, Rating, Comment, UserID, RestaurantID (no date)
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
		# Get column names dynamically
		columns_query = """
		SELECT column_name 
		FROM information_schema.columns 
		WHERE table_schema = 'jcw2239' AND table_name = 'cuisine'
		ORDER BY ordinal_position;
		"""
		cursor = g.conn.execute(text(columns_query))
		columns = [row[0] for row in cursor]
		cursor.close()
		print(f"Cuisine table columns: {columns}")
		
		# Find name column for ORDER BY (could be 'name' or 'cuisename')
		name_col = None
		for col in columns:
			if col == 'name' or col == 'cuisename':
				name_col = col
				break
		
		# If no name column, just order by first column
		if not name_col and len(columns) > 0:
			name_col = columns[0]
		
		if name_col:
			select_query = f"SELECT * FROM cuisine ORDER BY {name_col};"
		else:
			select_query = "SELECT * FROM cuisine;"
		
		cursor = g.conn.execute(text(select_query))
		cuisines_list = []
		for result in cursor:
			cuisine_dict = {}
			for i, col in enumerate(columns):
				if col == 'cuisineid' or col == 'cuisine_id':
					cuisine_dict['id'] = result[i]
				elif col == 'name' or col == 'cuisename':
					cuisine_dict['name'] = result[i]
				else:
					cuisine_dict[col] = result[i] if result[i] else 'N/A'
			
			if 'id' not in cuisine_dict:
				cuisine_dict['id'] = result[0] if len(result) > 0 else 'N/A'
			if 'name' not in cuisine_dict:
				# Try to find name column by position
				for i, col in enumerate(columns):
					if col == 'name' or col == 'cuisename':
						cuisine_dict['name'] = result[i] if result[i] else 'N/A'
						break
				if 'name' not in cuisine_dict:
					# Use first non-ID column as name, or second column
					if len(result) > 1:
						cuisine_dict['name'] = result[1] if result[1] else 'N/A'
					else:
						cuisine_dict['name'] = 'N/A'
			
			cuisines_list.append(cuisine_dict)
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


@app.route('/login')
def login():
	abort(401)
	# Your IDE may highlight this as a problem - because no such function exists (intentionally).
	# This code is never executed because of abort().
	this_is_never_executed()


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
