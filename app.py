from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_cors import CORS
from app.auth import requires_auth, create_token, bcrypt
from app.error_handlers import register_error_handlers
from app.routes.subscribers import bp as subscribers_bp
from app.routes.loans import bp as loans_bp
from app.routes.documents import bp as documents_bp
from app.schemas import init_db, SubscriberSchema, DocumentSchema, LoanSchema
from app.auth import AuthError
from app.error_handlers import DuplicateKeyError
import os

# Initialize Flask extensions
mongo = PyMongo()
cors = CORS()

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure the app
    app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://mongo-db:27017/mediatheque")
    app.config["DEBUG"] = True
    
    # Initialize extensions
    mongo.init_app(app)
    cors.init_app(app)
    
    # Initialize database
    init_db(mongo)
    
    # Register blueprints
    app.register_blueprint(subscribers_bp, url_prefix='/api/subscribers')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(loans_bp, url_prefix='/api/loans')
    
    # Register error handlers
    register_error_handlers(app)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)