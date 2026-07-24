import mysql.connector
from mysql.connector import Error as MySQLError
from config import Config
import datetime

def get_db_connection():
    """
    Opens and returns a new MySQL connection using settings from Config.
    Caller is responsible for closing the connection (use try/finally).
    """
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
        )
        return connection
    except MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_user_by_email(email):
    """Get user by email"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching user by email: {e}")
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    """Get user by username"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching user by username: {e}")
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching user by ID: {e}")
        return None
    finally:
        conn.close()

def create_user(username, email, password_hash, location=None, farming_experience=None, preferred_language='en'):
    """Create a new user"""
    print(f"🔍 create_user called with: username={username}, email={email}")
    
    conn = get_db_connection()
    if conn is None:
        print("❌ Database connection failed in create_user")
        return None
    
    try:
        cursor = conn.cursor()
        print("📝 Executing INSERT query...")
        
        # Print the SQL query for debugging
        query = """
            INSERT INTO users 
            (username, email, password_hash, location, farming_experience, preferred_language) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (username, email, password_hash, location, farming_experience, preferred_language)
        print(f"   Query: {query}")
        print(f"   Params: {params}")
        
        cursor.execute(query, params)
        conn.commit()
        
        user_id = cursor.lastrowid
        cursor.close()
        print(f"✅ User created with ID: {user_id}")
        
        # Verify the user was actually inserted
        verify_cursor = conn.cursor(dictionary=True)
        verify_cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = verify_cursor.fetchone()
        verify_cursor.close()
        
        if user:
            print(f"✅ Verification successful: {user}")
        else:
            print("⚠️ User was not found after insertion!")
        
        return user_id
        
    except MySQLError as e:
        print(f"❌ MySQL Error creating user: {e}")
        print(f"   Error code: {e.errno}")
        print(f"   SQL State: {e.sqlstate}")
        print(f"   Message: {e.msg}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in create_user: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn.is_connected():
            conn.close()
            print("🔒 Database connection closed")
            

def authenticate_user(username_or_email, password):
    """Authenticate user by username/email and password"""
    from werkzeug.security import check_password_hash
    
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        # Check if input is email or username
        if '@' in username_or_email:
            query = "SELECT * FROM users WHERE email = %s"
        else:
            query = "SELECT * FROM users WHERE username = %s"
        
        cursor.execute(query, (username_or_email,))
        user = cursor.fetchone()
        return user
    except MySQLError as e:
        print(f"Error authenticating user: {e}")
        return None
    finally:
        conn.close()

# Disease-related functions
def get_disease_info(disease_name):
    """Get disease information by name"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM diseases WHERE name = %s", (disease_name,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching disease info: {e}")
        return None
    finally:
        conn.close()

def get_disease_remedies(disease_id):
    """Get remedies for a disease"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM disease_remedies WHERE disease_id = %s", (disease_id,))
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching disease remedies: {e}")
        return []
    finally:
        conn.close()

def save_detection_record(user_id, disease_id, severity, stage, confidence, image_path):
    """Save disease detection record"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO detection_history 
            (user_id, disease_id, severity, stage, confidence, image_path, detection_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, disease_id, severity, stage, confidence, image_path, datetime.datetime.now())
        )
        conn.commit()
        return cursor.lastrowid
    except MySQLError as e:
        print(f"Error saving detection record: {e}")
        return None
    finally:
        conn.close()

# Crop-related functions
def get_crop_info(crop_name):
    """Get crop information by name"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crops WHERE name = %s", (crop_name,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching crop info: {e}")
        return None
    finally:
        conn.close()

def get_all_crops():
    """Get all crops"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crops ORDER BY name")
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching crops: {e}")
        return []
    finally:
        conn.close()

def get_crops_by_season(season):
    """Get crops suitable for a specific season"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crops WHERE growing_season LIKE %s", (f'%{season}%',))
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching crops by season: {e}")
        return []
    finally:
        conn.close()

def get_crop_disease_risk(crop_id, season):
    """Get disease risk for a crop in a specific season"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM crop_disease_susceptibility WHERE crop_id = %s AND season LIKE %s",
            (crop_id, f'%{season}%')
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching crop disease risk: {e}")
        return []
    finally:
        conn.close()

def save_recommendation_record(user_id, crop_id, location, season, suitability_score, profit_estimate, disease_risk):
    """Save crop recommendation record"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO recommendation_history 
            (user_id, crop_id, location, season, suitability_score, profit_estimate, disease_risk, recommendation_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, crop_id, location, season, suitability_score, profit_estimate, disease_risk, datetime.datetime.now())
        )
        conn.commit()
        return cursor.lastrowid
    except MySQLError as e:
        print(f"Error saving recommendation record: {e}")
        return None
    finally:
        conn.close()

# Chat-related functions
def save_chat_message(user_id, user_message, bot_response, language='en'):
    """Save chat history"""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_history 
            (user_id, user_message, bot_response, language, timestamp) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, user_message, bot_response, language, datetime.datetime.now())
        )
        conn.commit()
        return cursor.lastrowid
    except MySQLError as e:
        print(f"Error saving chat message: {e}")
        return None
    finally:
        conn.close()

def get_user_chat_history(user_id, limit=50):
    """Get chat history for a user"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
            (user_id, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching chat history: {e}")
        return []
    finally:
        conn.close()

# Government schemes
def get_government_schemes(state=None, category=None):
    """Get government schemes with optional filters"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM government_schemes WHERE 1=1"
        params = []
        
        if state:
            query += " AND state = %s"
            params.append(state)
        if category:
            query += " AND category = %s"
            params.append(category)
        
        query += " ORDER BY scheme_name"
        
        cursor.execute(query, tuple(params) if params else None)
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching government schemes: {e}")
        return []
    finally:
        conn.close()

# Initialize database
def initialize_database():
    """Initialize database with schema"""
    try:
        # First connect without database to create it if needed
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT,
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
        cursor.execute(f"USE {Config.DB_NAME}")
        
        # Read and execute schema.sql
        try:
            with open('database/schema.sql', 'r', encoding='utf-8') as f:
                schema = f.read()
                # Split by semicolon and execute each statement
                statements = schema.split(';')
                for statement in statements:
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except MySQLError as e:
                            print(f"Error executing schema statement: {e}")
                conn.commit()
                print("Database schema created successfully")
        except FileNotFoundError:
            print("schema.sql file not found. Please create it first.")
        except Exception as e:
            print(f"Error reading schema.sql: {e}")
        
        cursor.close()
        conn.close()
    except MySQLError as e:
        print(f"Error initializing database: {e}")

# Test function
if __name__ == "__main__":
    print("Testing database connection...")
    conn = get_db_connection()
    if conn:
        print("✓ Database connection successful!")
        conn.close()
    else:
        print("✗ Database connection failed!")
    
    print("\nInitializing database...")
    initialize_database()