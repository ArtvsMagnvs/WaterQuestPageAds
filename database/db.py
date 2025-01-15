import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
import json
from datetime import datetime

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

# Create engine and session
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()