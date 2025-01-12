# app/routes/subscribers.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from app.auth import requires_auth
from app import mongo
from app.schemas import SubscriberSchema

bp = Blueprint('subscribers', __name__)

@bp.route('/', methods=['GET'])
@requires_auth
def get_subscribers():
    try:
        # Add support for pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page

        # Get total count for pagination
        total = mongo.db.subscribers.count_documents({})
        
        # Get subscribers with pagination
        subscribers = list(mongo.db.subscribers.find().skip(skip).limit(per_page))
        
        return jsonify({
            'data': SubscriberSchema.dump(subscribers, many=True),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['GET'])
@requires_auth
def get_subscriber(id):
    try:
        subscriber = mongo.db.subscribers.find_one({'_id': ObjectId(id)})
        if not subscriber:
            return jsonify({'error': 'Subscriber not found'}), 404
        return jsonify(SubscriberSchema.dump(subscriber))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
@requires_auth
def create_subscriber():
    try:
        data = SubscriberSchema.load(request.json)
        
        # Add creation timestamp and initialize lists
        data['inscription_date'] = datetime.utcnow()
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['PUT'])
@requires_auth
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['DELETE'])
@requires_auth
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
