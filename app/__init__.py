# app/__init__.py
from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
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
    
    # Register blueprints
    from .routes.subscribers import bp as subscribers_bp
    from .routes.documents import bp as documents_bp
    from .routes.loans import bp as loans_bp
    
    app.register_blueprint(subscribers_bp, url_prefix='/api/subscribers')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(loans_bp, url_prefix='/api/loans')
    
    # Register error handlers
    from .error_handlers import register_error_handlers
    register_error_handlers(app)
    
    return app
