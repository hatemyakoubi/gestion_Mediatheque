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
    # Get query parameters for pagination (default to page 1 and 10 items per page)
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = int(request.args.get('per_page', 10))  # Default to 10 items per page

    # Calculate the skip value
    skip = (page - 1) * per_page

    # Query documents with pagination
    documents = list(mongo.db.documents.find().skip(skip).limit(per_page))

    # Get the total number of documents
    total_documents = mongo.db.documents.count_documents({})

    # Prepare pagination metadata
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_documents': total_documents
    }

    # Return the documents and pagination metadata
    return jsonify({
        'documents': document_schema.dump(documents, many=True),
        'pagination': pagination
    })


@app.route('/api/documents', methods=['POST'])
def add_document():
    data = document_schema.load(request.json)
    data['available'] = True
    
    result = mongo.db.documents.insert_one(data)
    return jsonify({
        "message": "Document added successfully",
        "id": str(result.inserted_id)
    }), 201

@app.route('/api/loans/', methods=['GET'])
#@requires_auth
def get_loans():
    loans = list(mongo.db.loans.find())
    return jsonify(loan_schema.dump(loans, many=True))

@app.route('/api/loans', methods=['POST'])
#@requires_auth
def create_loan():
    data = loan_schema.load(request.json)
    
    # Verify document availability
    document = mongo.db.documents.find_one({'_id': ObjectId(data['document_id'])})
    if not document or not document.get('available', False):
        return jsonify({"error": "Document not available"}), 400
    
    # Create loan record
    loan_data = {
        'subscriber_id': ObjectId(data['subscriber_id']),
        'document_id': ObjectId(data['document_id']),
        'loan_date': datetime.utcnow(),
        'due_date': datetime.utcnow() + timedelta(days=14),
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
            "message": "Loan created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)