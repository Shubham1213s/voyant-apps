import flask
from flask import Flask, Blueprint, render_template,  request, jsonify,  redirect, url_for, session, flash
from pymongo import MongoClient
from flask_pymongo import PyMongo
import json
import paho.mqtt.client as mqtt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message


main_app = Flask(__name__)

main_app.config['SECRET_KEY'] = "tsfyguaistyatuis589566875623568956"
main_app.config['MAIL_SERVER'] = "smtp.zoho.in"
main_app.config['MAIL_PORT'] = 587
main_app.config['MAIL_USE_TLS'] = True
main_app.config['MAIL_USERNAME'] = "info@voyant.in"
main_app.config['MAIL_PASSWORD'] = "Info@$12"
main_app.config['MAIL_DEFAULT_SENDER'] = 'info@voyant.in'  #
mail = Mail(main_app)

client4 = MongoClient('mongodb://localhost:27017/')
db4 = client4['MasterDB']  
users_collection4 = db4['users-log']

main_app.config['MONGO_URI'] = 'mongodb://localhost:27017/MasterDB'
mongo = PyMongo(main_app)

client = MongoClient('mongodb://localhost:27017/')
db = client['MasterDB']  # Replace 'your_database_name' with your actual database name
collection = db['AllDevicesInfo']  # Replace 'your_collection_name' with your actual collection name


@main_app.route('/')
def home():
    return render_template('index4.html')

@main_app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
         # Check if username or email already exists
        existing_user = users_collection4.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            flash('Username or email already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        # Check password complexity (add your own complexity requirements)
        if len(password) < 5:
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('register'))
        # Hash the password before storing it
        hashed_password = generate_password_hash(password)
        # Insert the user into the database 
        users_collection4.insert_one({'username': username, 'password': hashed_password, 'mobile_number': mobile_number, 'email': email})
        send_registration_email(email)
        # flash('Registration successful. Please log in.', 'success')
        # return redirect(url_for('login'))
        return redirect(url_for('login', registered=True))
        # return redirect(url_for('login'))  
    return render_template('register.html')
def send_registration_email(email):
    msg = Message('Welcome to YourApp!', recipients=[email])
    msg.body = render_template('email/welcome_email.txt')
    msg.html = render_template('email/welcome_email.html')
    mail.send(msg)


@main_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the user exists in the database
        user = users_collection4.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('profile'))
        return 'Invalid username or password'
    registered = request.args.get('registered')  # Check if registration was successful
    return render_template('login.html', registered=registered)


@main_app.route('/profile')
def profile():
    data = list(collection.find())
    if 'username' in session:
        username = session['username']
        return render_template('index.html', data=data, username=username)
    return redirect(url_for('login'))
    
    

# Add a route to serve the CSS file
@main_app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@main_app.route('/templates/index_AddDevice')
def index_AddDevice():
    return render_template('index_AddDevice.html')

@main_app.route('/submit', methods=['POST'])
# def submit():
#     data = request.form.to_dict()
#     mongo.db.AllDevicesInfo.insert_one(data)
#     return jsonify({'message': 'Data added to MongoDB successfully'})
def submit():
    data = request.form.to_dict()
    imei_to_check = data.get('IMEI')
    # Check if a record with the given IMEI already exists
    existing_device = mongo.db.AllDevicesInfo.find_one({'IMEI': imei_to_check})
    if existing_device:
        # IMEI already exists, return an error
        return jsonify({'message': 'Device already exists with this IMEI'})
    else:
        # IMEI doesn't exist, insert data into MongoDB
        mongo.db.AllDevicesInfo.insert_one(data)
        return jsonify({'message': 'Data added to MongoDB successfully'})


@main_app.route('/templates/index_appShowAll')
def index_appShowAll():
    data = list(collection.find())
    return render_template('index_appShowAll.html', data=data)

@main_app.route('/templates/index')
def index_main():
    data = list(collection.find())
    return render_template('index.html', data=data)


# MongoDB settings
mongo_uri2 = 'mongodb://localhost:27017/'
mongo_db_name2 = 'DevicesDB'

@main_app.route('/templates/index_individual')
def index_individual():
    # Retrieve a list of all collections in the database
    client = MongoClient(mongo_uri2)
    db = client[mongo_db_name2]
    collections = db.list_collection_names()
    return render_template('index_individual.html', collections=collections)


# MQTT settings
mqtt_broker = "test.mosquitto.org"
mqtt_port = 1883
mqtt_topic = "voyant/869009066595134/data"
# Store received messages
received_messages = []
# MQTT on_message callback
def on_message(client, userdata, message):
    payload = message.payload.decode('utf-8')
    received_messages.append(payload)
# MQTT setup
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(mqtt_broker, mqtt_port, 60)
mqtt_client.subscribe(mqtt_topic)
# Start MQTT loop in a separate thread
mqtt_client.loop_start()


@main_app.route('/collection/<collection_name>')
def show_collection_data(collection_name):
    # Retrieve data from the specified collection
    client = MongoClient(mongo_uri2)
    db = client[mongo_db_name2]
    collection = db[collection_name]
    data = collection.find()
    return render_template('collection_data.html', collection_name=collection_name, data=data)

# Route to handle the /voyant/ route and its subpaths
@main_app.route('/collection/voyant/<path:subpath>')
def handle_voyant(subpath):
    collection_name = f'voyant/{subpath}'
    # Retrieve data from the specified collection
    client = MongoClient(mongo_uri2)
    db = client[mongo_db_name2]
    collection = db[collection_name]
    data = collection.find()
    return render_template('collection_data.html', collection_name=collection_name, data=data)


@main_app.route('/search', methods=['POST'])
def search():
    collection_name = request.form['searchInput']
    client = MongoClient(mongo_uri2)
    db = client[mongo_db_name2]
    # Check if the collection exists in the database
    if collection_name not in db.list_collection_names():
        return collection_name + ' is not existed.'
        #return render_template('error.html', message=f"Collection '{collection_name}' does not exist.")
    collection_data = db[collection_name].find()

    return render_template('result.html', collection_name=collection_name, collection_data=collection_data)


@main_app.route('/get_messages')
def get_messages():
    return jsonify(messages=received_messages)

@main_app.route('/live_data')
def live_data():
    return render_template('live_data.html')

@main_app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    main_app.run(debug=True, port=5054)
