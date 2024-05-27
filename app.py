from flask import Flask, request, jsonify
from datetime import datetime
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from datetime import timedelta
from models import db, User, Space, Booking
# from config import DATABASE_CONFIG  # Import the config
import secrets
# from payment import trigger_stk_push, query_stk_push
import os 
from dotenv import load_dotenv

app = Flask(_name_)
CORS(app)  # Enable CORS for all routes
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
# Generate a random secret key
jwt_secret_key = secrets.token_hex(32)  # Generate a 32-byte (256-bit) random key

# Set the JWT_SECRET_KEY in your Flask app's configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# URL Routing
@app.route('/')
def index():
    return "This is a basic Flask application"

# Admin Login Route with JWT Authentication
@app.route('/adminlogin', methods=['POST'])
def admin_login():
    data = request.get_json()

    # Check login credentials
    if data['email'] == 'admin@gmail.com' and data['password'] == 'password':
        expiration_time = timedelta(hours=1)
        token = create_access_token(identity=data['email'], expires_delta=expiration_time)

        return jsonify({"success": True, "message": "Login successful", "token": token, 'user_email': data['email'], 'role': 'admin'}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401


# Route for admin logout
@app.route('/adminlogout', methods=['POST'])
#@jwt_required()  # Protect this route with JWT authentication
def admin_logout():
    try:
        # Unset JWT cookies to log the user out
        response = jsonify({"success": True, "message": "Logout successful"})
        unset_jwt_cookies(response)
        return response, 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# Add Space Route
@app.route('/spaces', methods=['POST'])
#@jwt_required()  # Protect this route with JWT authentication
def add_space():
    data = request.get_json()
    new_space = Space(name=data['name'], description=data['description'], location=data['location'], price_per_hour=data['price_per_hour'], owner_id=data['owner_id'])
    db.session.add(new_space)
    db.session.commit()
    return jsonify({"success": True, "message": "Space added successfully"}), 201

# View All Spaces Route
@app.route('/spaces', methods=['GET'])
def get_spaces():
    spaces = Space.query.all()
    space_list = []
    for space in spaces:
        space_data = {
            'id': space.id,
            'name': space.name,
            'description': space.description,
            'location': space.location,
            'price_per_hour': str(space.price_per_hour),  # Convert to string for JSON compatibility
            'owner_id': space.owner_id,
            'created_at': str(space.created_at)  # Convert to string for JSON compatibility
        }
        space_list.append(space_data)
    return jsonify({"success": True, "spaces": space_list}), 200

# URL Route for adding a new user
@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    # Hash the password before storing it in the database
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"success": True, "message": "User added successfully"}), 201

@app.route('/userlogin', methods=['POST'])
def user_login():
    data = request.get_json()

    # Check if the user exists
    user = User.query.filter_by(email=data['email']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        expiration_time = timedelta(hours=1)
        token = create_access_token(identity=user.email, expires_delta=expiration_time)
        return jsonify({"success": True, "message": "Login successful", "token": token, 'user_email': user.email, 'role': user.role}), 200
    else:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401
    
# URL Route for getting all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role  # Include 'role' in the response
        }
        user_list.append(user_data)
    return jsonify({"success": True, "users": user_list}), 200

@app.route('/userlogout', methods=['POST'])
#@jwt_required()  # Protect this route with JWT authentication
def user_logout():
    try:
        # Unset JWT cookies to log the user out
        response = jsonify({"success": True, "message": "Logout successful"})
        unset_jwt_cookies(response)
        return response, 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}),

# # Update the delete_user route to handle user deletion
# @app.route('/delete_user', methods=['DELETE'])
# @jwt_required()  # Protect this route with JWT authentication
# def delete_user():
    try:
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()

        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({"success": True, "message": "User deleted successfully"}), 200
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/bookings', methods=['POST'])
def add_booking():
    data = request.get_json()
    
    required_fields = ['user_id', 'space_id', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    try:
        start_time = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M')
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date/time format. Use ISO 8601 format: YYYY-MM-DDTHH:MM"}), 400

    space = Space.query.get(data['space_id'])
    if not space:
        return jsonify({"success": False, "message": "Space not found"}), 404

    new_booking = Booking(
        user_id=data['user_id'],
        space_id=data['space_id'],
        start_time=start_time,
        end_time=end_time,
        status=data.get('status', 'pending'),
        payment_status=data.get('payment_status', 'unpaid')
    )
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"success": True, "message": "Booking added successfully"}), 201

@app.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Booking.query.all()
    booking_list = []
    for booking in bookings:
        booking_data = {
            'id': booking.id,
            'user_id': booking.user_id,
            'space_id': booking.space_id,
            'start_time': booking.start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_time': booking.end_time.strftime('%Y-%m-%dT%H:%M'),
            'status': booking.status,
            'payment_status': booking.payment_status,
            'created_at': booking.created_at.strftime('%Y-%m-%dT%H:%M')
        }
        booking_list.append(booking_data)
    return jsonify({"success": True, "bookings": booking_list}), 200

# @app.route('/make_payment', methods=['POST'])
# @jwt_required()
# def make_payment():
#     data = request.get_json()
#     # Extract payment details from request
#     phone_number = data['phone_number']
#     amount = data['amount']
#     callback_url = data['callback_url']
#     account_ref = data['account_ref']
#     description = data['description']

#     # Trigger STK push payment
#     payment_response = trigger_stk_push(phone_number, amount, callback_url, account_ref, description)
#     return jsonify(payment_response), 200

# @app.route('/check_payment_status', methods=['POST'])
# @jwt_required()
# def check_payment_status():
#     data = request.get_json()
#     checkout_request_id = data['checkout_request_id']

#     # Query STK push payment status
#     payment_status_response = query_stk_push(checkout_request_id)
#     return jsonify(payment_status_response), 200



if _name_ == '_main_':
    app.run(debug=False)
