# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from flask_sqlalchemy import SQLAlchemy
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
# from werkzeug.security import generate_password_hash, check_password_hash
# import os
# from app import *


# app.config['SECRET_KEY'] = 'super-secret-key-change-in-prod'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-prod'

# # INIT
# db = SQLAlchemy(app)


# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password = db.Column(db.String(120), nullable=False)

# # CREATE DB (Run once)
# with app.app_context():
#     db.create_all()