# tests/conftest.py
import pytest
from flask import Flask
from flask_pymongo import PyMongo
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # Import your Flask app

@pytest.fixture
def test_app():
    app.config.update({
        "TESTING": True,
        "MONGO_URI": "mongodb://localhost:27017/mediatheque_test"
    })
    return app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def mongo(test_app):
    mongo = PyMongo(test_app)
    # Clear collections before each test
    mongo.db.subscribers.delete_many({})
    mongo.db.documents.delete_many({})
    mongo.db.loans.delete_many({})
    return mongo