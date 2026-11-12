
"""
app/database.py is responsible for setting up the database connection
and related SQLAlchemy configuration.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Database connection address
DATABASE_URL = os.getenv("DATABASE_URL")

# Creates the SQLAlchemy database engine
engine = create_engine(DATABASE_URL)

# Creates sessions for database operations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for SQLAlchemy models
Base = declarative_base()
