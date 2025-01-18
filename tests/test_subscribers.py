# tests/test_subscribers.py
import pytest
import json
from datetime import datetime
from bson import ObjectId

def test_get_subscribers_empty(client):
    response = client.get('/api/subscribers/')
    assert response.status_code == 200

def test_add_subscriber(client, mongo):
    subscriber_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "address": "123 Test St"
    }
    
    response = client.post(
        '/api/subscribers',
        json=subscriber_data  # Use json instead of data with json.dumps
    )
    assert response.status_code == 201
    assert "id" in response.json

def test_get_subscriber(client, mongo):
    # Insert test subscriber
    result = mongo.db.subscribers.insert_one({
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "inscription_date": datetime.utcnow()
    })
    
    subscriber_id = str(result.inserted_id)
    response = client.get(f'/api/subscribers/{subscriber_id}')
    assert response.status_code == 200
    assert response.json["email"] == "test@example.com"

def test_update_subscriber(client, mongo):
    # Insert test subscriber
    result = mongo.db.subscribers.insert_one({
        "first_name": "Old",
        "last_name": "Name",
        "email": "old@example.com"
    })
    
    subscriber_id = str(result.inserted_id)
    update_data = {
        "first_name": "New",
        "last_name": "Name",
        "email": "new@example.com"
    }

    response = client.put(
        f'/api/subscribers/{subscriber_id}',
        json=update_data  # Use json instead of data with json.dumps
    )
    assert response.status_code == 200