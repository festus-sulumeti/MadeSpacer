from app import bcrypt
from usermodel import User

def user_loader_callback(identity):
    return User.query.get(identity)