# app/routes/loans.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timedelta
from app.schemas import LoanSchema
#from app.auth import #@requires_auth
from app import mongo

bp = Blueprint('loans', __name__)

@bp.route('/', methods=['GET'])
#@requires_auth
def get_loans():
    try:
        # Add support for pagination and filtering
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page
        
        # Build filter based on query parameters
        filter_query = {}
        if request.args.get('status'):
            filter_query['status'] = request.args.get('status')
        if request.args.get('subscriber_id'):
            filter_query['subscriber_id'] = ObjectId(request.args.get('subscriber_id'))
            
        # Get total count for pagination
        total = mongo.db.loans.count_documents(filter_query)
        
        # Get loans with pagination and filtering
        loans = list(mongo.db.loans.find(filter_query).skip(skip).limit(per_page))
        
        return jsonify({
            'data': LoanSchema.dump(loans, many=True),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['GET'])
#@requires_auth
def get_loan(id):
    try:
        loan = mongo.db.loans.find_one({'_id': ObjectId(id)})
        if not loan:
            return jsonify({'error': 'Loan not found'}), 404
        return jsonify(LoanSchema.dump(loan))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
#@requires_auth
def create_loan():
    try:
        data = LoanSchema.load(request.json)
        
        # Verify subscriber exists
        subscriber = mongo.db.subscribers.find_one({'_id': ObjectId(data['subscriber_id'])})
        if not subscriber:
            return jsonify({'error': 'Subscriber not found'}), 404
            
        # Verify document exists and is available
        document = mongo.db.documents.find_one({'_id': ObjectId(data['document_id'])})
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        if not document.get('available', False):
            return jsonify({'error': 'Document is not available'}), 400
            
        # Create loan record
        loan_data = {
            'subscriber_id': ObjectId(data['subscriber_id']),
            'document_id': ObjectId(data['document_id']),
            'loan_date': datetime.utcnow(),
            'due_date': datetime.utcnow() + timedelta(days=14),
            'status': 'active'
        }
        
        # Update document availability
        mongo.db.documents.update_one(
            {'_id': ObjectId(data['document_id'])},
            {'$set': {'available': False}}
        )
        
        # Update subscriber's current loans
        mongo.db.subscribers.update_one(
            {'_id': ObjectId(data['subscriber_id'])},
            {'$push': {'current_loans': loan_data}}
        )
        
        # Create loan record
        result = mongo.db.loans.insert_one(loan_data)
        
        # Get the created loan
        loan = mongo.db.loans.find_one({'_id': result.inserted_id})
        
        return jsonify({
            'message': 'Loan created successfully',
            'data': LoanSchema.dump(loan)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>/return', methods=['POST'])
#@requires_auth
def return_loan(id):
    try:
        loan = mongo.db.loans.find_one({'_id': ObjectId(id)})
        if not loan:
            return jsonify({'error': 'Loan not found'}), 404
            
        if loan['status'] != 'active':
            return jsonify({'error': 'Loan is not active'}), 400
            
        # Update loan status
        mongo.db.loans.update_one(
            {'_id': ObjectId(id)},
            {
                '$set': {
                    'status': 'returned',
                    'return_date': datetime.utcnow()
                }
            }
        )
        
        # Update document availability
        mongo.db.documents.update_one(
            {'_id': loan['document_id']},
            {'$set': {'available': True}}
        )
        
        # Update subscriber's loans
        mongo.db.subscribers.update_one(
            {'_id': loan['subscriber_id']},
            {
                '$pull': {'current_loans': {'document_id': loan['document_id']}},
                '$push': {'loan_history': loan}
            }
        )
        
        return jsonify({'message': 'Loan returned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>/extend', methods=['POST'])
#@requires_auth
def extend_loan(id):
    try:
        loan = mongo.db.loans.find_one({'_id': ObjectId(id)})
        if not loan:
            return jsonify({'error': 'Loan not found'}), 404
            
        if loan['status'] != 'active':
            return jsonify({'error': 'Can only extend active loans'}), 400
            
        # Extend due date by 7 days
        new_due_date = loan['due_date'] + timedelta(days=7)
        
        mongo.db.loans.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'due_date': new_due_date}}
        )
        
        return jsonify({'message': 'Loan extended successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}),