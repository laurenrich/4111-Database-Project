
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
				if col == 'restaurant_id':
					restaurant_dict['id'] = result[i]
				elif col == 'name':
					restaurant_dict['name'] = result[i]
				elif col == 'address':
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
