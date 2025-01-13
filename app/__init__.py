# app/__init__.py
from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
import os

# Initialize Flask extensions
mongo = PyMongo()
cors = CORS()