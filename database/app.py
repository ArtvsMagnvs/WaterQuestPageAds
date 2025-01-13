from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from database.models.player_model import Base
import os

app = Flask(__name__)

# Database configuration for Railway PostgreSQL
db_url = os.environ.get('DATABASE_URL')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Ensure the database tables are created
with app.app_context():
    Base.metadata.create_all(db.engine)

if __name__ == '__main__':
    app.run(debug=True)
