from flask import request, jsonify
from app import app
from app import jwt
from usermodel import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify(message='Invalid username or password'), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role == 'admin':
        return jsonify(message='This is a protected route for admins only.'), 200
    else:
        return jsonify(message='You are not authorized to access this route.'), 403