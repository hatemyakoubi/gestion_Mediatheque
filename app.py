# app.py
from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from flask_cors import CORS
from app.schemas import SubscriberSchema, DocumentSchema, LoanSchema, init_db
#from app.auth import requires_auth, create_token, bcrypt
from app.error_handlers import register_error_handlers
from bson import ObjectId
from datetime import datetime, timedelta
from pymongo import MongoClient
from flask import request, jsonify

app = Flask(__name__)
CORS(app)
#app.config["MONGO_URI"] = "mongodb://mongo-db:27017/mediatheque"
app.config["MONGO_URI"] = "mongodb://mongo-db:27017/mediatheque"
mongo = PyMongo(app)

client = MongoClient("mongodb://mongo-db:27017/")
db = client.mediatheque

# Initialize database with indexes
init_db(mongo)

# Initialize schemas
subscriber_schema = SubscriberSchema()
document_schema = DocumentSchema()
loan_schema = LoanSchema()

# Register error handlers
register_error_handlers(app)

# Frontend routes
@app.route('/')
def index():
    return render_template('index.html')

def convert_objectid(obj):
    """Recursively convert ObjectId to string in nested documents."""
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

@app.route('/api/subscribers/', methods=['GET'])
def get_subscribers():
    try:
        # Fetch all subscribers from MongoDB
        subscribers = list(mongo.db.subscribers.find())
        
        # Convert any ObjectId instances to strings
        subscribers = [convert_objectid(subscriber) for subscriber in subscribers]
        
        # Serialize the data using SubscriberSchema
        serialized_subscribers = SubscriberSchema(many=True).dump(subscribers)
        
        # Return serialized data as JSON response
        return jsonify(serialized_subscribers)
    except Exception as e:
        print(f"Error in get_subscribers: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route('/api/subscribers', methods=['POST'])
def add_subscriber():
    try:
        data = request.json
        data['inscription_date'] = datetime.utcnow()
        data['current_loans'] = []
        data['loan_history'] = []
        
        result = mongo.db.subscribers.insert_one(data)
        return jsonify({
            "message": "Subscriber added successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"message": "Failed to add subscriber", "error": str(e)}), 400

@app.route('/api/subscribers/<subscriber_id>', methods=['DELETE'])
def delete_subscriber(subscriber_id):
    try:
        result = mongo.db.subscribers.delete_one({"_id": ObjectId(subscriber_id)})
        if result.deleted_count == 1:
            return jsonify({"message": "Subscriber deleted successfully"}), 200
        else:
            return jsonify({"message": "Subscriber not found"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to delete subscriber", "message": str(e)}), 400

@app.route('/api/subscribers/<subscriber_id>', methods=['PUT'])
def update_subscriber(subscriber_id):
    try:
        data = request.json
        mongo.db.subscribers.update_one(
            {"_id": ObjectId(subscriber_id)},
            {"$set": {
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "email": data.get("email"),
                "address": data.get("address"),
                "phone": data.get("phone")
            }}
        )
        return jsonify({"message": "Subscriber updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to update subscriber", "error": str(e)}), 400

@app.route('/api/subscribers/<subscriber_id>', methods=['GET'])
def get_subscriber(subscriber_id):
    try:
        subscriber = mongo.db.subscribers.find_one({"_id": ObjectId(subscriber_id)})
        if not subscriber:
            return jsonify({"message": "Subscriber not found"}), 404
        
        # Convert ObjectId to string
        subscriber = convert_objectid(subscriber)
        
        return jsonify(subscriber), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch subscriber", "error": str(e)}), 400

@app.route('/api/documents/', methods=['GET'])
def get_documents():
    try:
        # Get query parameters for pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Get total documents
        total_documents = mongo.db.documents.count_documents({})
        total_pages = max(1, (total_documents + per_page - 1) // per_page)

        # Calculate skip
        skip = (page - 1) * per_page

        # Query documents with sorting (newest first)
        documents = list(mongo.db.documents.find().sort('_id', -1).skip(skip).limit(per_page))

        # Convert ObjectIds to strings in documents
        for doc in documents:
            doc['_id'] = str(doc['_id'])

        return jsonify({
            "documents": documents,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_documents": total_documents,
                "total_pages": total_pages
            }
        })

    except Exception as e:
        print(f"Error in get_documents: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
    
@app.route('/api/documents/<document_id>', methods=['PUT'])
def update_document(document_id):
    try:
        data = request.json
        result = mongo.db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {
                "title": data.get("title"),
                "author": data.get("author"),
                "type": data.get("type"),
                "isbn": data.get("isbn"),
                "genre": data.get("genre"),
                "publication_date": data.get("publication_date"),
                "available": data.get("available", True)
            }}
        )
        if result.modified_count == 0:
            return jsonify({"message": "Document not found"}), 404
        return jsonify({"message": "Document updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to update document", "error": str(e)}), 400

@app.route('/api/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    try:
        # Check if document is currently loaned
        loan = mongo.db.loans.find_one({
            "document_id": ObjectId(document_id),
            "status": "active"
        })
        if loan:
            return jsonify({"message": "Cannot delete document that is currently loaned"}), 400
        
        result = mongo.db.documents.delete_one({"_id": ObjectId(document_id)})
        if result.deleted_count == 0:
            return jsonify({"message": "Document not found"}), 404
        return jsonify({"message": "Document deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to delete document", "error": str(e)}), 400

@app.route('/api/documents', methods=['POST'])
def create_document():
    try:
        data = request.json
        data['available'] = True  # New documents are always available
        result = mongo.db.documents.insert_one(data)
        return jsonify({
            "message": "Document created successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"message": "Failed to create document", "error": str(e)}), 400

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    try:
        document = mongo.db.documents.find_one({"_id": ObjectId(document_id)})
        if not document:
            return jsonify({"message": "Document not found"}), 404

        # Convert ObjectId to string
        document['_id'] = str(document['_id'])
        
        return jsonify(document), 200
    except Exception as e:
        print(f"Error in get_document: {e}")
        return jsonify({"message": "Failed to fetch document", "error": str(e)}), 400


@app.route('/api/loans/', methods=['GET'])
def get_loans():
    try:
        # Use aggregation to join with subscribers and documents collections
        pipeline = [
            {
                '$lookup': {
                    'from': 'subscribers',
                    'localField': 'subscriber_id',
                    'foreignField': '_id',
                    'as': 'subscriber'
                }
            },
            {
                '$lookup': {
                    'from': 'documents',
                    'localField': 'document_id',
                    'foreignField': '_id',
                    'as': 'document'
                }
            },
            {
                '$unwind': '$subscriber'
            },
            {
                '$unwind': '$document'
            },
            {
                '$project': {
                    '_id': 1,
                    'loan_date': 1,
                    'due_date': 1,
                    'status': 1,
                    'subscriber_name': {
                        '$concat': ['$subscriber.first_name', ' ', '$subscriber.last_name']
                    },
                    'document_title': '$document.title'
                }
            }
        ]

        loans = list(mongo.db.loans.aggregate(pipeline))

        # Convert ObjectId to string
        for loan in loans:
            loan['_id'] = str(loan['_id'])

        return jsonify(loans)
    except Exception as e:
        print(f"Error fetching loans: {e}")
        return jsonify({"error": "Failed to fetch loans"}), 500



@app.route('/api/loans', methods=['POST'])
def create_loan():
    try:
        data = request.json
        
        # Verify document availability
        document = mongo.db.documents.find_one({'_id': ObjectId(data['document_id'])})
        if not document or not document.get('available', False):
            return jsonify({"error": "Document not available"}), 400
        
        # Parse dates
        loan_date = datetime.strptime(data['loan_date'], '%Y-%m-%d')
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        
        # Validate dates
        if loan_date > due_date:
            return jsonify({"error": "Return date must be after loan date"}), 400
        
        # Create loan record
        loan_data = {
            'subscriber_id': ObjectId(data['subscriber_id']),
            'document_id': ObjectId(data['document_id']),
            'loan_date': loan_date,
            'due_date': due_date,
            'status': 'active'
        }
        
        # Update document availability and subscriber's current loans
        try:
            mongo.db.documents.update_one(
                {'_id': ObjectId(data['document_id'])},
                {'$set': {'available': False}}
            )
            
            mongo.db.subscribers.update_one(
                {'_id': ObjectId(data['subscriber_id'])},
                {'$push': {'current_loans': loan_data}}
            )
            
            result = mongo.db.loans.insert_one(loan_data)
            return jsonify({
                "message": "Loan created successfully",
                "id": str(result.inserted_id)
            }), 201
            
        except Exception as e:
            # Rollback document availability if loan creation fails
            mongo.db.documents.update_one(
                {'_id': ObjectId(data['document_id'])},
                {'$set': {'available': True}}
            )
            raise e
            
    except ValueError as e:
        return jsonify({"error": "Invalid date format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/loans/<loan_id>', methods=['GET'])
def get_loan(loan_id):
    try:
        loan = mongo.db.loans.find_one({"_id": ObjectId(loan_id)})
        if not loan:
            return jsonify({"message": "Loan not found"}), 404
        return jsonify(loan_schema.dump(loan)), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch loan", "error": str(e)}), 400

@app.route('/api/loans/<loan_id>', methods=['PUT'])
def update_loan(loan_id):
    try:
        data = request.json
        loan = mongo.db.loans.find_one({"_id": ObjectId(loan_id)})
        if not loan:
            return jsonify({"message": "Loan not found"}), 404

        # Update loan status
        update_data = {
            "status": data.get("status", loan["status"])
        }
        
        # If returning the document (status changed to 'returned')
        if data.get("status") == "returned" and loan["status"] == "active":
            # Update document availability
            mongo.db.documents.update_one(
                {"_id": loan["document_id"]},
                {"$set": {"available": True}}
            )
            
            # Update subscriber's current loans
            mongo.db.subscribers.update_one(
                {"_id": loan["subscriber_id"]},
                {"$pull": {"current_loans": {"document_id": loan["document_id"]}}}
            )
            
            # Set return date
            update_data["return_date"] = datetime.utcnow()

        result = mongo.db.loans.update_one(
            {"_id": ObjectId(loan_id)},
            {"$set": update_data}
        )
        
        return jsonify({"message": "Loan updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to update loan", "error": str(e)}), 400

@app.route('/api/loans/<loan_id>', methods=['DELETE'])
def delete_loan(loan_id):
    try:
        loan = mongo.db.loans.find_one({"_id": ObjectId(loan_id)})
        if not loan:
            return jsonify({"message": "Loan not found"}), 404
            
        # Can only delete returned loans
        if loan["status"] == "active":
            return jsonify({"message": "Cannot delete active loan"}), 400
            
        result = mongo.db.loans.delete_one({"_id": ObjectId(loan_id)})
        return jsonify({"message": "Loan deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to delete loan", "error": str(e)}), 400

@app.route('/api/loans/subscriber/<subscriber_id>', methods=['GET'])
def get_subscriber_loans(subscriber_id):
    try:
        loans = list(mongo.db.loans.find({
            "subscriber_id": ObjectId(subscriber_id)
        }).sort("loan_date", -1))
        return jsonify(loan_schema.dump(loans, many=True)), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch subscriber loans", "error": str(e)}), 400

@app.route('/api/loans/document/<document_id>', methods=['GET'])
def get_document_loans(document_id):
    try:
        loans = list(mongo.db.loans.find({
            "document_id": ObjectId(document_id)
        }).sort("loan_date", -1))
        return jsonify(loan_schema.dump(loans, many=True)), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch document loans", "error": str(e)}), 400
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)