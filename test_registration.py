# test_registration.py
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Testing User Registration")
print("=" * 60)

from config import Config
from database.db_connection import (
    get_db_connection,
    create_user,
    get_user_by_email,
    get_user_by_username
)
from werkzeug.security import generate_password_hash

def test_connection():
    """Test database connection"""
    print("\n1. Testing database connection...")
    conn = get_db_connection()
    if conn:
        print("   ✅ Database connection successful!")
        
        # Check if users table exists
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'users'")
        table_exists = cursor.fetchone()
        if table_exists:
            print("   ✅ Users table exists")
        else:
            print("   ❌ Users table does NOT exist!")
            print("   Please run the schema.sql file first.")
        cursor.close()
        conn.close()
        return True
    else:
        print("   ❌ Database connection failed!")
        print("   Please check your MySQL credentials in config.py")
        return False

def test_create_user():
    """Test creating a user"""
    print("\n2. Testing user creation...")
    
    test_username = "testuser_" + str(os.urandom(4).hex())
    test_email = f"{test_username}@test.com"
    test_password = "TestPassword123"
    
    print(f"   Creating user: {test_username}")
    print(f"   Email: {test_email}")
    
    # Check if user already exists
    existing = get_user_by_username(test_username)
    if existing:
        print(f"   ⚠️ User '{test_username}' already exists, skipping test")
        return True
    
    # Create the user
    password_hash = generate_password_hash(test_password)
    user_id = create_user(
        username=test_username,
        email=test_email,
        password_hash=password_hash,
        location="Test Location",
        farming_experience=5,
        preferred_language="en"
    )
    
    if user_id:
        print(f"   ✅ User created with ID: {user_id}")
        
        # Verify the user was created
        user = get_user_by_id(user_id)
        if user:
            print(f"   ✅ User found in database: {user['username']}")
            print(f"      Email: {user['email']}")
            print(f"      Location: {user['location']}")
            return True
        else:
            print("   ❌ User not found in database after creation!")
            return False
    else:
        print("   ❌ create_user returned None")
        return False

def test_get_user_functions():
    """Test get_user functions"""
    print("\n3. Testing get_user functions...")
    
    # Try to get a user by email
    test_email = "test@example.com"
    user = get_user_by_email(test_email)
    print(f"   get_user_by_email('{test_email}'): {'Found' if user else 'Not found'}")
    
    # Try to get a user by username
    test_username = "testuser"
    user = get_user_by_username(test_username)
    print(f"   get_user_by_username('{test_username}'): {'Found' if user else 'Not found'}")

if __name__ == "__main__":
    print(f"Config: DB_HOST={Config.DB_HOST}, DB_NAME={Config.DB_NAME}")
    
    if test_connection():
        test_get_user_functions()
        test_create_user()
    else:
        print("\n❌ Cannot proceed without database connection!")
    
    print("\n" + "=" * 60)
    print("Test complete!")