# test_imports.py
print("=" * 50)
print("Testing Imports for AgriVision AI")
print("=" * 50)

print("\n1. Testing config import...")
try:
    from config import Config
    print("✓ Config imported successfully")
    print(f"   DB_HOST: {Config.DB_HOST}")
    print(f"   DB_USER: {Config.DB_USER}")
    print(f"   DB_NAME: {Config.DB_NAME}")
except Exception as e:
    print(f"✗ Config import failed: {e}")
    exit(1)

print("\n2. Testing db_connection import...")
try:
    from database.db_connection import (
        get_user_by_email,
        get_user_by_username,
        get_user_by_id,
        create_user,
        get_db_connection
    )
    print("✓ db_connection imported successfully")
    print(f"   - get_user_by_email: {get_user_by_email}")
    print(f"   - get_user_by_username: {get_user_by_username}")
    print(f"   - get_user_by_id: {get_user_by_id}")
    print(f"   - create_user: {create_user}")
    print(f"   - get_db_connection: {get_db_connection}")
except Exception as e:
    print(f"✗ db_connection import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n3. Testing database connection...")
try:
    conn = get_db_connection()
    if conn:
        print("✓ Database connection successful!")
        conn.close()
    else:
        print("✗ Database connection failed!")
        print("   Please check your MySQL credentials in config.py")
except Exception as e:
    print(f"✗ Error connecting to database: {e}")

print("\n4. Testing app import...")
try:
    from app import app
    print("✓ App imported successfully")
    print(f"   App name: {app.name}")
    print(f"   Debug mode: {app.debug}")
except Exception as e:
    print(f"✗ App import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Import test complete!")