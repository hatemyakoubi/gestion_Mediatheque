# app/routes/subscribers.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone
from marshmallow.exceptions import ValidationError
#from app.auth import requires_auth
from app import mongo
from app.schemas import SubscriberSchema

bp = Blueprint('subscribers', __name__)

# Default pagination values
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 10

# Custom error handler for exceptions
@bp.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['GET'])
#@requires_auth
def get_subscribers():
    try:
        page = int(request.args.get('page', DEFAULT_PAGE))
        per_page = int(request.args.get('per_page', DEFAULT_PER_PAGE))
        skip = (page - 1) * per_page

        total = mongo.db.subscribers.count_documents({})
        print(f"Total subscribers: {total}")  # Debug statement
        subscribers = list(mongo.db.subscribers.find().skip(skip).limit(per_page))
        
        # Pagination flags
        has_next = page < (total + per_page - 1) // per_page
        has_prev = page > 1

        return jsonify({
            'data': SubscriberSchema.dump(subscribers, many=True),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'has_next': has_next,
            'has_prev': has_prev
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['GET'])
#@requires_auth
def get_subscriber(id):
    try:
        subscriber = mongo.db.subscribers.find_one({'_id': ObjectId(id)})
        if not subscriber:
            return jsonify({'error': 'Subscriber not found'}), 404
        return jsonify(SubscriberSchema.dump(subscriber))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
#@requires_auth
def create_subscriber():
    try:
        data = SubscriberSchema.load(request.json)
        
        # Add creation timestamp and initialize lists
        data['inscription_date'] = datetime.now(timezone.utc).isoformat()
        data['current_loans'] = []
        data['loan_history'] = []
        
        # Check if email already exists
        if mongo.db.subscribers.find_one({'email': data['email']}):
            return jsonify({'error': 'Email already registered'}), 400
        
        result = mongo.db.subscribers.insert_one(data)
        
        # Get the created subscriber
        subscriber = mongo.db.subscribers.find_one({'_id': result.inserted_id})
        
        return jsonify({
            'message': 'Subscriber created successfully',
            'data': SubscriberSchema.dump(subscriber)
        }), 201
    except ValidationError as err:
        return jsonify({'validation_errors': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['PUT'])
#@requires_auth
def update_subscriber(id):
    try:
        data = SubscriberSchema.load(request.json)
        
        # Check if email already exists for another subscriber
        existing = mongo.db.subscribers.find_one({'email': data['email'], '_id': {'$ne': ObjectId(id)}})
        if existing:
            return jsonify({'error': 'Email already registered to another subscriber'}), 400
        
        result = mongo.db.subscribers.update_one(
            {'_id': ObjectId(id)},
            {'$set': data}
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'Subscriber not found'}), 404
            
        # Get updated subscriber
        subscriber = mongo.db.subscribers.find_one({'_id': ObjectId(id)})
        
        return jsonify({
            'message': 'Subscriber updated successfully',
            'data': SubscriberSchema.dump(subscriber)
        })
    except ValidationError as err:
        return jsonify({'validation_errors': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['DELETE'])
#@requires_auth
def delete_subscriber(id):
    try:
        # Check if subscriber has active loans
        subscriber = mongo.db.subscribers.find_one({'_id': ObjectId(id)})
        if not subscriber:
            return jsonify({'error': 'Subscriber not found'}), 404
            
        if subscriber.get('current_loans', []):
            return jsonify({'error': 'Cannot delete subscriber with active loans'}), 400
        
        result = mongo.db.subscribers.delete_one({'_id': ObjectId(id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Subscriber not found'}), 404
            
        return jsonify({'message': 'Subscriber deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
