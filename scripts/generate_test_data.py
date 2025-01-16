# generate_test_data.py
from faker import Faker
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import bcrypt
from bson.objectid import ObjectId
# Initialize Faker
fake = Faker()

# Connect to MongoDB
client = MongoClient('mongodb://mongo-db:27017/')

db = client['mediatheque']

def generate_users():
    """Generate 4 fake user accounts"""
    users = [
        {
            "_id": ObjectId(),
            "first_name": "Admin",
            "last_name": "User",
            "email": "admin@mediatheque.com",
            "address": fake.address(),
            "phone": fake.phone_number(),
            "password": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()),
            "role": "admin",
            "inscription_date": datetime.utcnow(),
            "current_loans": [],
            "loan_history": []
        },
        {
            "_id": ObjectId(),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@mediatheque.com",
            "address": fake.address(),
            "phone": fake.phone_number(),
            "password": bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()),
            "role": "user",
            "inscription_date": datetime.utcnow(),
            "current_loans": [],
            "loan_history": []
        },
        {
            "_id": ObjectId(),
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@mediatheque.com",
            "address": fake.address(),
            "phone": fake.phone_number(),
            "password": bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()),
            "role": "user",
            "inscription_date": datetime.utcnow(),
            "current_loans": [],
            "loan_history": []
        },
        {
            "_id": ObjectId(),
            "first_name": "Robert",
            "last_name": "Johnson",
            "email": "robert.johnson@mediatheque.com",
            "address": fake.address(),
            "phone": fake.phone_number(),
            "password": bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()),
            "role": "user",
            "inscription_date": datetime.utcnow(),
            "current_loans": [],
            "loan_history": []
        }
    ]
    
    # Insert users into database
    db.subscribers.insert_many(users)
    print("Created 4 user accounts")
    return users

def generate_books():
    """Generate 100 fake books"""
    genres = ["Fiction", "Non-Fiction", "Science Fiction", "Mystery", "Romance", 
              "Fantasy", "Biography", "History", "Science", "Philosophy",
              "Poetry", "Drama", "Horror", "Adventure", "Thriller"]
    
    publishers = ["Penguin Random House", "HarperCollins", "Simon & Schuster",
                 "Hachette Book Group", "Macmillan Publishers"]
    
    languages = ["French", "English", "Spanish", "German"]
    
    books = []
    
    for _ in range(100):
        publication_date = fake.date_between(start_date='-20y', end_date='today')
        
        book = {
            "title": fake.catch_phrase(),
            "author": fake.name(),
            "type": "book",
            "isbn": fake.isbn13(),
            "publisher": random.choice(publishers),
            "language": random.choice(languages),
            "publication_date": datetime.combine(publication_date, datetime.min.time()),  # Convert to datetime
            "genre": random.choice(genres),
            "description": fake.text(max_nb_chars=200),
            "pages": random.randint(100, 800),
            "available": True,
            "location": f"Section {random.choice('ABCDE')}-{random.randint(1,20)}",
            "added_date": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        books.append(book)
    
    # Insert books into database
    db.documents.insert_many(books)
    print("Created 100 books")
    return books

def main():
    # Clear existing data
    db.subscribers.delete_many({})
    db.documents.delete_many({})
    db.loans.delete_many({})
    
    print("Generating test data...")
    users = generate_users()
    books = generate_books()
    
    # Create some sample loans
    for user in users[1:]:  # Skip admin user
        # Create 2-3 random loans for each user
        num_loans = random.randint(2, 3)
        for _ in range(num_loans):
            available_books = [b for b in books if b['available']]
            if not available_books:
                break
                
            book = random.choice(available_books)
            loan_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            
            loan = {
                "subscriber_id": user['_id'],
                "document_id": book['_id'],
                "loan_date": loan_date,
                "due_date": loan_date + timedelta(days=14),
                "status": "active"
            }
            
            # Update book availability
            db.documents.update_one(
                {'_id': book['_id']},
                {'$set': {'available': False}}
            )
            
            # Add loan to user's current loans
            db.subscribers.update_one(
                {'_id': user['_id']},
                {'$push': {'current_loans': loan}}
            )
            
            # Create loan record
            db.loans.insert_one(loan)
            books.remove(book)  # Remove book from our local list
            
    print("Created sample loans for users")
    print("\nTest data generation complete!")
    print("\nUser credentials:")
    print("Admin - Email: admin@mediatheque.com, Password: admin123")
    print("User1 - Email: john.doe@mediatheque.com, Password: user123")
    print("User2 - Email: jane.smith@mediatheque.com, Password: user123")
    print("User3 - Email: robert.johnson@mediatheque.com, Password: user123")

if __name__ == "__main__":
    main()