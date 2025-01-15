import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)

# Database configuration
db_url = os.environ.get('DATABASE_URL')

if db_url is None:
    # Fallback to a local SQLite database if DATABASE_URL is not set
    db_url = 'sqlite:///local_development.db'
    print("WARNING: DATABASE_URL is not set. Using a local SQLite database.")
else:
    # Ensure the URL uses the correct protocol
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Create engine and session
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

# Ensure the database tables are created
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
