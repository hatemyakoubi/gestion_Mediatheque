# setup.py
import os
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure"""
    directories = [
        'app',
        'static/css',
        'static/js',
        'templates',
        'scripts'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    print("✓ Created directory structure")

def create_init_files():
    """Create __init__.py files where needed"""
    init_locations = ['app']
    
    for location in init_locations:
        Path(f'{location}/__init__.py').touch()
    
    print("✓ Created initialization files")

def main():
    print("Setting up Médiathèque project...")
    
    # Create directory structure
    create_directory_structure()
    create_init_files()
    
    print("\nProject setup complete!")
    print("\nNext steps:")
    print("1. Copy all application files to their respective directories")
    print("2. Run 'docker-compose up --build -d' to start the application")
    print("3. Run the test data generation script")
    print("\nAccess the application at:")
    print("- Web Application: http://localhost:5000")
    print("- MongoDB Admin: http://localhost:8081")

if __name__ == "__main__":
    main()