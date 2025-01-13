# app/error_handlers.py
from flask import jsonify, request
from marshmallow import ValidationError
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError, PyMongoError
from app.auth import AuthError  # Importing AuthError from auth.py

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle Marshmallow validation errors"""
        return jsonify({
            'error': 'Validation error',
            'messages': error.messages
        }), 400

    @app.errorhandler(InvalidId)
    def handle_invalid_object_id(error):
        """Handle invalid MongoDB ObjectID format"""
        return jsonify({
            'error': 'Invalid ID format',
            'message': 'The provided ID is not in the correct format'
        }), 400

    @app.errorhandler(DuplicateKeyError)
    def handle_duplicate_key_error(error):
        """Handle MongoDB duplicate key errors"""
        return jsonify({
            'error': 'Duplicate entry',
            'message': 'A record with this unique field already exists'
        }), 409

    @app.errorhandler(PyMongoError)
    def handle_mongo_error(error):
        """Handle general MongoDB errors"""
        return jsonify({
            'error': 'Database error',
            'message': 'An error occurred while accessing the database'
        }), 500

    @app.errorhandler(404)
    def handle_not_found_error(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return jsonify({
            'error': 'Method not allowed',
            'message': f'The {request.method} method is not allowed for this endpoint'
        }), 405

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle any unhandled exceptions"""
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    # Custom error handler for authentication errors
    @app.errorhandler(AuthError)
    def handle_auth_error(error):
        """Handle authentication errors"""
        return jsonify(error.error), error.status_code

    # Custom error for resource conflicts
    class ResourceConflictError(Exception):
        pass

    @app.errorhandler(ResourceConflictError)
    def handle_resource_conflict(error):
        """Handle resource conflicts"""
        return jsonify({
            'error': 'Resource conflict',
            'message': str(error)
        }), 409

    # Custom error for business logic violations
    class BusinessLogicError(Exception):
        def __init__(self, message):
            self.message = message

    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(error):
        """Handle business logic errors"""
        return jsonify({
            'error': 'Business logic error',
            'message': error.message
        }), 422

    # Custom error for resource unavailability
    class ResourceUnavailableError(Exception):
        pass

    @app.errorhandler(ResourceUnavailableError)
    def handle_resource_unavailable(error):
        """Handle resource unavailability"""
        return jsonify({
            'error': 'Resource unavailable',
            'message': str(error)
        }), 423

    return app
