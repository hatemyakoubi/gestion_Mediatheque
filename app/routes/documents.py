# app/routes/documents.py
from flask import Blueprint, request, jsonify
from bson import ObjectId
from app.schemas import DocumentSchema
#from app.auth import requires_auth
from app import mongo

bp = Blueprint('documents', __name__)

@bp.route('/', methods=['GET'])
#@requires_auth
def get_documents():
    try:
        # Add support for pagination and filtering
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page
        
        # Build filter based on query parameters
        filter_query = {}
        if request.args.get('type'):
            filter_query['type'] = request.args.get('type')
        if request.args.get('available') is not None:
            filter_query['available'] = request.args.get('available').lower() == 'true'
            
        # Get total count for pagination
        total = mongo.db.documents.count_documents(filter_query)
        
        # Get documents with pagination and filtering
        documents = list(mongo.db.documents.find(filter_query).skip(skip).limit(per_page))
        
        return jsonify({
            'data': DocumentSchema.dump(documents, many=True),
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['GET'])
#@requires_auth
def get_document(id):
    try:
        document = mongo.db.documents.find_one({'_id': ObjectId(id)})
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        return jsonify(DocumentSchema.dump(document))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['POST'])
#@requires_auth
def create_document():
    try:
        data = DocumentSchema.load(request.json)
        
        # Set initial availability
        data['available'] = True
        
        # Check if ISBN already exists (if provided)
        if data.get('isbn'):
            if mongo.db.documents.find_one({'isbn': data['isbn']}):
                return jsonify({'error': 'ISBN already exists'}), 400
        
        result = mongo.db.documents.insert_one(data)
        
        # Get the created document
        document = mongo.db.documents.find_one({'_id': result.inserted_id})
        
        return jsonify({
            'message': 'Document created successfully',
            'data': DocumentSchema.dump(document)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['PUT'])
#@requires_auth
def update_document(id):
    try:
        data = DocumentSchema.load(request.json)
        
        # Check if ISBN already exists for another document
        if data.get('isbn'):
            existing = mongo.db.documents.find_one({'isbn': data['isbn'], '_id': {'$ne': ObjectId(id)}})
            if existing:
                return jsonify({'error': 'ISBN already exists for another document'}), 400
        
        result = mongo.db.documents.update_one(
            {'_id': ObjectId(id)},
            {'$set': data}
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'Document not found'}), 404
            
        # Get updated document
        document = mongo.db.documents.find_one({'_id': ObjectId(id)})
        
        return jsonify({
            'message': 'Document updated successfully',
            'data': DocumentSchema.dump(document)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<id>', methods=['DELETE'])
#@requires_auth
def delete_document(id):
    try:
        # Check if document is currently loaned
        document = mongo.db.documents.find_one({'_id': ObjectId(id)})
        if not document:
            return jsonify({'error': 'Document not found'}), 404
            
        if not document.get('available', True):
            return jsonify({'error': 'Cannot delete document that is currently loaned'}), 400
        
        result = mongo.db.documents.delete_one({'_id': ObjectId(id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Document not found'}), 404
            
        return jsonify({'message': 'Document deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500