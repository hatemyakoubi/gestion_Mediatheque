import pytest
from bson import ObjectId
import json
from datetime import datetime, timedelta

class TestLoans:
    def test_create_loan(self, client, mongo):
        # Insert test subscriber and document
        subscriber_id = mongo.db.subscribers.insert_one({
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com"
        }).inserted_id

        document_id = mongo.db.documents.insert_one({
            "title": "Test Book",
            "author": "Author",
            "available": True
        }).inserted_id

        loan_data = {
            "subscriber_id": str(subscriber_id),
            "document_id": str(document_id),
            "loan_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        }

        response = client.post('/api/loans',
                             data=json.dumps(loan_data),
                             content_type='application/json')
        assert response.status_code == 201

        # Verify document is no longer available
        document = mongo.db.documents.find_one({"_id": document_id})
        assert document["available"] is False

    def test_return_loan(self, client, mongo):
        # Setup test data
        subscriber_id = mongo.db.subscribers.insert_one({
            "first_name": "Test",
            "last_name": "User"
        }).inserted_id

        document_id = mongo.db.documents.insert_one({
            "title": "Test Book",
            "available": False
        }).inserted_id

        loan_id = mongo.db.loans.insert_one({
            "subscriber_id": subscriber_id,
            "document_id": document_id,
            "status": "active",
            "loan_date": datetime.utcnow(),
            "due_date": datetime.utcnow() + timedelta(days=14)
        }).inserted_id

        response = client.put(f'/api/loans/{str(loan_id)}',
                            data=json.dumps({"status": "returned"}),
                            content_type='application/json')
        assert response.status_code == 200

        # Verify document is available again
        document = mongo.db.documents.find_one({"_id": document_id})
        assert document["available"] is True