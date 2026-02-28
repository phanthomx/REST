from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
# from models import User


app = Flask(__name__)

# CONFIG
app.config['SECRET_KEY'] = 'super-secret-key-change-in-prod'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-prod'

# INIT
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app) # Allow Vue to talk to Flask

# MODEL
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# CREATE DB (Run once)
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    # Hash password before saving!
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password=hashed_pw)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created"}), 201
    except:
        return jsonify({"message": "Username exists"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password, data['password']):
        # ⚠️ Convert user.id to string!
        token = create_access_token(identity=str(user.id))
        return jsonify({
            "token": token,
            "username": user.username
        }), 200
    
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/dashboard', methods=['GET'])
@jwt_required() # <-- PROTECTED ROUTE
def dashboard():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({"message": f"Welcome to the dashboard, {user.username}!", "secret_data": "12345"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)