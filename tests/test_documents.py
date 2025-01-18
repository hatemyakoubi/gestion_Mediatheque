import pytest
from bson import ObjectId
import json

class TestDocuments:
    def test_get_documents_pagination(self, client, mongo):
        # Insert test documents
        for i in range(15):
            mongo.db.documents.insert_one({
                "title": f"Book {i}",
                "author": "Author",
                "type": "book",
                "available": True
            })

        # Test first page
        response = client.get('/api/documents/?page=1&per_page=10')
        assert response.status_code == 200
        data = response.json
        assert len(data["documents"]) == 10
        assert data["pagination"]["total_pages"] == 2

    def test_create_document(self, client, mongo):
        document_data = {
            "title": "Test Book",
            "author": "Test Author",
            "type": "book",
            "isbn": "1234567890",
            "publication_year": 2023
        }
        
        response = client.post('/api/documents',
                             data=json.dumps(document_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        # Verify document was created
        document = mongo.db.documents.find_one({"title": "Test Book"})
        assert document is not None
        assert document["available"] is True

    def test_update_document(self, client, mongo):
        # Insert test document
        doc_id = mongo.db.documents.insert_one({
            "title": "Old Title",
            "author": "Old Author",
            "type": "book",
            "available": True
        }).inserted_id

        update_data = {
            "title": "New Title",
            "author": "New Author"
        }

        response = client.put(f'/api/documents/{str(doc_id)}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        assert response.status_code == 200

        # Verify update
        updated = mongo.db.documents.find_one({"_id": doc_id})
        assert updated["title"] == "New Title"

    def test_delete_document(self, client, mongo):
        # Insert test document
        doc_id = mongo.db.documents.insert_one({
            "title": "Delete Me",
            "author": "Author",
            "type": "book",
            "available": True
        }).inserted_id

        response = client.delete(f'/api/documents/{str(doc_id)}')
        assert response.status_code == 200

        # Verify deletion
        assert mongo.db.documents.find_one({"_id": doc_id}) is None

    def test_cannot_delete_loaned_document(self, client, mongo):
        # Insert document with active loan
        doc_id = mongo.db.documents.insert_one({
            "title": "Loaned Book",
            "author": "Author",
            "type": "book",
            "available": False
        }).inserted_id

        # Create active loan
        mongo.db.loans.insert_one({
            "document_id": doc_id,
            "status": "active"
        })

        response = client.delete(f'/api/documents/{str(doc_id)}')
        assert response.status_code == 400