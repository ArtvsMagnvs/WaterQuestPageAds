from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from .db.game_db import db_url, Base, engine

from .db.game_db import Session as Database
import os
from dotenv import load_dotenv

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Ensure the database tables are created
with app.app_context():
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    app.run(debug=True)
