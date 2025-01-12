# schemas.py
from marshmallow import Schema, fields, validate

class SubscriberSchema(Schema):
    _id = fields.Str(dump_only=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=2))
    last_name = fields.Str(required=True, validate=validate.Length(min=2))
    email = fields.Email(required=True)
    address = fields.Str(required=True)
    phone = fields.Str(required=True, validate=validate.Length(min=8))
    inscription_date = fields.DateTime(dump_only=True)
    current_loans = fields.List(fields.Dict(), dump_only=True)
    loan_history = fields.List(fields.Dict(), dump_only=True)

class DocumentSchema(Schema):
    _id = fields.Str(dump_only=True)
    title = fields.Str(required=True)
    type = fields.Str(required=True, validate=validate.OneOf(['book', 'magazine', 'dvd']))
    author = fields.Str(required=True)
    publication_date = fields.Date(required=True)
    available = fields.Bool(dump_only=True)
    genre = fields.Str(required=True)
    isbn = fields.Str()

class LoanSchema(Schema):
    _id = fields.Str(dump_only=True)
    subscriber_id = fields.Str(required=True)
    document_id = fields.Str(required=True)
    loan_date = fields.DateTime(dump_only=True)
    due_date = fields.DateTime(dump_only=True)
    return_date = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True)

# MongoDB collection initialization
def init_db(mongo):
    # Create indexes
    mongo.db.subscribers.create_index('email', unique=True)
    mongo.db.documents.create_index('isbn', unique=True, sparse=True)
    mongo.db.loans.create_index([('subscriber_id', 1), ('document_id', 1)])