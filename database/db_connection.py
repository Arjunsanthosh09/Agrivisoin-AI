import mysql.connector
from mysql.connector import Error as MySQLError
from config import Config
import datetime
import json          

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


# ============================================================
# Detection History helpers
# ============================================================

def get_all_detections(user_id, limit=50):
    """Return all detections for a user, newest first."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, disease_id, severity, stage, confidence,
                      image_path, detection_date
               FROM detection_history
               WHERE user_id = %s
               ORDER BY detection_date DESC LIMIT %s""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching detections: {e}")
        return []
    finally:
        conn.close()
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
    
# ============================================================
# Crop Recommendation helpers
# ============================================================

def get_crops_by_season(season):
    """Return crops that grow in the given season."""
    conn = get_db_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM crops WHERE growing_season LIKE %s ORDER BY name",
            (f"%{season}%",)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching crops by season: {e}")
        return []
    finally:
        conn.close()


def get_crop_loss_stats(crop_id):
    """Return average loss % for a crop."""
    conn = get_db_connection()
    if conn is None: return {"avg_loss": 0, "records": 0}
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT AVG(loss_percentage) AS avg_loss, COUNT(*) AS records "
            "FROM crop_loss_records WHERE crop_id = %s",
            (crop_id,)
        )
        return cursor.fetchone() or {"avg_loss": 0, "records": 0}
    except MySQLError as e:
        print(f"Error fetching crop loss stats: {e}")
        return {"avg_loss": 0, "records": 0}
    finally:
        conn.close()


def get_crop_disease_risk(crop_id, season):
    """Return highest risk level for a crop in a season."""
    conn = get_db_connection()
    if conn is None: return "low"
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT risk_level FROM crop_disease_susceptibility "
            "WHERE crop_id = %s AND season LIKE %s "
            "ORDER BY FIELD(risk_level,'very_high','high','medium','low') LIMIT 1",
            (crop_id, f"%{season}%")
        )
        row = cursor.fetchone()
        return row['risk_level'] if row else "low"
    except MySQLError as e:
        print(f"Error fetching crop disease risk: {e}")
        return "low"
    finally:
        conn.close()


def save_recommendation_record(user_id, crop_id, location, season,
                                suitability_score, profit_estimate, disease_risk):
    """Save a recommendation into recommendation_history."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO recommendation_history
               (user_id, crop_id, location, season, suitability_score,
                profit_estimate, disease_risk, recommendation_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, crop_id, location, season, suitability_score,
             profit_estimate, disease_risk, datetime.datetime.now())
        )
        conn.commit()
        return cursor.lastrowid
    except MySQLError as e:
        print(f"Error saving recommendation: {e}")
        return None
    finally:
        conn.close()


def get_user_recommendation_history(user_id, limit=20):
    """Get past recommendations for a user."""
    conn = get_db_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT r.*, c.name AS crop_name
               FROM recommendation_history r
               JOIN crops c ON c.id = r.crop_id
               WHERE r.user_id = %s
               ORDER BY r.recommendation_date DESC LIMIT %s""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching recommendation history: {e}")
        return []
    finally:
        conn.close()
        
# ============================================================
# Chatbot helpers
# ============================================================

def save_chat_message(user_id, user_message, bot_response, language='en'):
    """Save a chat exchange to chat_history."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO chat_history
               (user_id, user_message, bot_response, language, timestamp)
               VALUES (%s, %s, %s, %s, %s)""",
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
    """Get last N chat messages for a user."""
    conn = get_db_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT user_message, bot_response, language, timestamp
               FROM chat_history
               WHERE user_id = %s
               ORDER BY timestamp ASC LIMIT %s""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching chat history: {e}")
        return []
    finally:
        conn.close()


def get_last_detection(user_id):
    """Get the most recent detection for context."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT severity, stage, confidence, detection_date
               FROM detection_history
               WHERE user_id = %s
               ORDER BY detection_date DESC LIMIT 1""",
            (user_id,)
        )
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching last detection: {e}")
        return None
    finally:
        conn.close()

# ============================================================
# Dashboard helpers
# ============================================================

def get_dashboard_stats(user_id):
    """Return stats for the dashboard cards."""
    conn = get_db_connection()
    if conn is None:
        return {"total_detections": 0, "total_recommendations": 0,
                "common_disease": "—", "avg_confidence": 0}
    try:
        cursor = conn.cursor(dictionary=True)

        # Total detections
        cursor.execute(
            "SELECT COUNT(*) AS c FROM detection_history WHERE user_id = %s",
            (user_id,)
        )
        total_detections = cursor.fetchone()["c"]

        # Total recommendations
        cursor.execute(
            "SELECT COUNT(*) AS c FROM recommendation_history WHERE user_id = %s",
            (user_id,)
        )
        total_recommendations = cursor.fetchone()["c"]

        # Average confidence
        cursor.execute(
            "SELECT AVG(confidence) AS a FROM detection_history WHERE user_id = %s",
            (user_id,)
        )
        avg_conf_row = cursor.fetchone()
        avg_confidence = round(float(avg_conf_row["a"] or 0), 1)

        # Most common disease (based on `stage` field, which stores disease type)
        cursor.execute(
            """SELECT stage, COUNT(*) AS c
               FROM detection_history
               WHERE user_id = %s AND stage IS NOT NULL AND stage != ''
               GROUP BY stage
               ORDER BY c DESC LIMIT 1""",
            (user_id,)
        )
        common_row = cursor.fetchone()
        common_disease = common_row["stage"] if common_row else "—"

        return {
            "total_detections": total_detections,
            "total_recommendations": total_recommendations,
            "common_disease": common_disease,
            "avg_confidence": avg_confidence,
        }
    except MySQLError as e:
        print(f"Error fetching dashboard stats: {e}")
        return {"total_detections": 0, "total_recommendations": 0,
                "common_disease": "—", "avg_confidence": 0}
    finally:
        conn.close()


def get_recent_detections(user_id, limit=5):
    """Return the user's most recent disease detections."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, severity, stage, confidence, image_path, detection_date
               FROM detection_history
               WHERE user_id = %s
               ORDER BY detection_date DESC LIMIT %s""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching recent detections: {e}")
        return []
    finally:
        conn.close()


def get_recent_recommendations(user_id, limit=5):
    """Return the user's most recent crop recommendations."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT r.id, r.season, r.suitability_score, r.profit_estimate,
                      r.disease_risk, r.recommendation_date,
                      c.name AS crop_name, c.category AS crop_category
               FROM recommendation_history r
               JOIN crops c ON c.id = r.crop_id
               WHERE r.user_id = %s
               ORDER BY r.recommendation_date DESC LIMIT %s""",
            (user_id, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching recent recommendations: {e}")
        return []
    finally:
        conn.close()
        
# ============================================================
# Market Prices helpers
# ============================================================

def get_crop_price_summary():
    """
    Return each crop's base price + latest market price + trend.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, name, category, market_price FROM crops ORDER BY name")
        crops = cursor.fetchall()

        results = []
        for crop in crops:
            # Latest price
            cursor.execute(
                """SELECT price_per_kg, date
                   FROM market_prices
                   WHERE crop_id = %s
                   ORDER BY date DESC LIMIT 1""",
                (crop['id'],)
            )
            latest = cursor.fetchone()

            # Average of previous 5 months
            cursor.execute(
                """SELECT AVG(price_per_kg) AS avg_old
                   FROM (
                     SELECT price_per_kg FROM market_prices
                     WHERE crop_id = %s
                     ORDER BY date DESC LIMIT 5 OFFSET 1
                   ) AS older""",
                (crop['id'],)
            )
            old_row = cursor.fetchone()
            avg_old = float(old_row['avg_old'] or crop['market_price'])

            current = float(latest['price_per_kg']) if latest else float(crop['market_price'])

            if avg_old > 0:
                change_pct = ((current - avg_old) / avg_old) * 100
            else:
                change_pct = 0

            if change_pct > 2:
                trend = "Increasing"
            elif change_pct < -2:
                trend = "Decreasing"
            else:
                trend = "Stable"

            results.append({
                "crop_id": crop['id'],
                "crop_name": crop['name'],
                "category": crop['category'],
                "base_price": float(crop['market_price']),
                "current_price": round(current, 2),
                "change_pct": round(change_pct, 1),
                "trend": trend,
                "latest_date": latest['date'] if latest else None,
            })

        return results
    except MySQLError as e:
        print(f"Error fetching crop price summary: {e}")
        return []
    finally:
        conn.close()


def get_price_history(crop_id, months=6):
    """Return the last N months of price history for a crop."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT price_per_kg, date, market_name, demand_level, price_trend
               FROM market_prices
               WHERE crop_id = %s
               ORDER BY date ASC LIMIT %s""",
            (crop_id, months)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching price history: {e}")
        return []
    finally:
        conn.close()

# ============================================================
# User Profile helpers
# ============================================================

def get_user_preferences(user_id):
    """Return the preferences row for a user, or None."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching user preferences: {e}")
        return None
    finally:
        conn.close()


def save_user_preferences(user_id, preferred_crops=None, soil_type=None,
                          farm_size=None, irrigation_type=None):
    """Insert or update user preferences (UPSERT)."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO user_preferences
               (user_id, preferred_crops, soil_type, farm_size, irrigation_type)
               VALUES (%s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                 preferred_crops = VALUES(preferred_crops),
                 soil_type = VALUES(soil_type),
                 farm_size = VALUES(farm_size),
                 irrigation_type = VALUES(irrigation_type)""",
            (user_id, preferred_crops, soil_type, farm_size, irrigation_type)
        )
        conn.commit()
        return True
    except MySQLError as e:
        print(f"Error saving user preferences: {e}")
        return False
    finally:
        conn.close()


def update_user_profile(user_id, location=None, farming_experience=None,
                        preferred_language='en'):
    """Update basic profile fields in the users table."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE users
               SET location = %s,
                   farming_experience = %s,
                   preferred_language = %s
               WHERE id = %s""",
            (location, farming_experience, preferred_language, user_id)
        )
        conn.commit()
        return True
    except MySQLError as e:
        print(f"Error updating user profile: {e}")
        return False
    finally:
        conn.close()


# ============================================================
# Contact helpers
# ============================================================

def save_contact_message(user_id, name, email, subject, message):
    """Insert a contact message."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO contact_messages
               (user_id, name, email, subject, message)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, name, email, subject, message)
        )
        conn.commit()
        return cursor.lastrowid
    except MySQLError as e:
        print(f"Error saving contact message: {e}")
        return None
    finally:
        conn.close()
        
# ============================================================
# Profit Estimation helpers
# ============================================================

def get_crop_price_trend(crop_id, months=6):
    """
    Return a trend dict for a crop:
      {
        'current': latest price/kg,
        'avg_3m': average of last 3 months,
        'trend_pct': % change (current vs older average),
        'momentum': 'up' | 'down' | 'flat',
        'history': [list of monthly prices, oldest → newest]
      }
    Returns None if no price data.
    """
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT price_per_kg, date
               FROM market_prices
               WHERE crop_id = %s
               ORDER BY date DESC LIMIT %s""",
            (crop_id, months)
        )
        rows = cursor.fetchall()
        if not rows:
            return None

        prices = [float(r['price_per_kg']) for r in rows]  # newest first
        current = prices[0]
        older = prices[1:] if len(prices) > 1 else prices
        avg_older = sum(older) / len(older) if older else current

        if avg_older > 0:
            trend_pct = ((current - avg_older) / avg_older) * 100
        else:
            trend_pct = 0.0

        if trend_pct > 2:
            momentum = 'up'
        elif trend_pct < -2:
            momentum = 'down'
        else:
            momentum = 'flat'

        return {
            'current': round(current, 2),
            'avg_older': round(avg_older, 2),
            'trend_pct': round(trend_pct, 1),
            'momentum': momentum,
            'history': list(reversed(prices)),  # oldest → newest for chart
        }
    except MySQLError as e:
        print(f"Error fetching crop price trend: {e}")
        return None
    finally:
        conn.close()

# ============================================================
# Admin module helpers
# ============================================================

def get_admin_dashboard_stats():
    """Return system-wide metrics for the admin dashboard."""
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}

        # Counts
        cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role='farmer'")
        stats['total_farmers'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) AS c FROM detection_history")
        stats['total_detections'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) AS c FROM recommendation_history")
        stats['total_recommendations'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) AS c FROM chat_history")
        stats['total_chat_msgs'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) AS c FROM contact_messages WHERE is_read=0 OR is_read IS NULL")
        stats['unread_messages'] = cursor.fetchone()['c']

        cursor.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM detection_history "
            "WHERE detection_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        )
        stats['active_users_week'] = cursor.fetchone()['c']

        # Detections per day (last 7 days)
        cursor.execute(
            """SELECT DATE(detection_date) AS d, COUNT(*) AS c
               FROM detection_history
               WHERE detection_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
               GROUP BY DATE(detection_date)
               ORDER BY d"""
        )
        stats['detections_by_day'] = cursor.fetchall()

        # Top diseases
        cursor.execute(
            """SELECT stage AS name, COUNT(*) AS c
               FROM detection_history
               WHERE stage IS NOT NULL AND stage != ''
               GROUP BY stage
               ORDER BY c DESC LIMIT 5"""
        )
        stats['top_diseases'] = cursor.fetchall()

        # Top recommended crops
        cursor.execute(
            """SELECT c.name AS name, COUNT(*) AS c
               FROM recommendation_history r
               JOIN crops c ON c.id = r.crop_id
               GROUP BY c.name
               ORDER BY c DESC LIMIT 5"""
        )
        stats['top_crops'] = cursor.fetchall()

        return stats
    except MySQLError as e:
        print(f"Error fetching admin stats: {e}")
        return {}
    finally:
        conn.close()


def get_all_users_admin(search=None, limit=100):
    """Return all users for admin user management."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT u.id, u.username, u.email, u.location,
                          u.farming_experience, u.preferred_language,
                          u.role, u.created_at, u.last_login,
                          (SELECT COUNT(*) FROM detection_history d WHERE d.user_id=u.id) AS detection_count,
                          (SELECT COUNT(*) FROM recommendation_history r WHERE r.user_id=u.id) AS rec_count
                   FROM users u
                   WHERE u.username LIKE %s OR u.email LIKE %s OR u.location LIKE %s
                   ORDER BY u.created_at DESC LIMIT %s""",
                (like, like, like, limit)
            )
        else:
            cursor.execute(
                """SELECT u.id, u.username, u.email, u.location,
                          u.farming_experience, u.preferred_language,
                          u.role, u.created_at, u.last_login,
                          (SELECT COUNT(*) FROM detection_history d WHERE d.user_id=u.id) AS detection_count,
                          (SELECT COUNT(*) FROM recommendation_history r WHERE r.user_id=u.id) AS rec_count
                   FROM users u
                   ORDER BY u.created_at DESC LIMIT %s""",
                (limit,)
            )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching users: {e}")
        return []
    finally:
        conn.close()


def get_user_detail_admin(user_id):
    """Return a single user with aggregated stats."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return None

        cursor.execute("SELECT COUNT(*) AS c FROM detection_history WHERE user_id=%s", (user_id,))
        user['detection_count'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) AS c FROM recommendation_history WHERE user_id=%s", (user_id,))
        user['rec_count'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(*) AS c FROM chat_history WHERE user_id=%s", (user_id,))
        user['chat_count'] = cursor.fetchone()['c']

        return user
    except MySQLError as e:
        print(f"Error fetching user detail: {e}")
        return None
    finally:
        conn.close()


def toggle_user_active_admin(user_id, active):
    """Enable/disable a user account."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active=%s WHERE id=%s", (active, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except MySQLError as e:
        print(f"Error toggling user: {e}")
        return False
    finally:
        conn.close()


def delete_user_admin(user_id):
    """Delete a user (cascades to related rows)."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    except MySQLError as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        conn.close()


def get_all_detections_admin(limit=200, severity=None, crop=None):
    """Return all detections across all users, with filters."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """SELECT d.id, d.severity, d.stage, d.confidence,
                          d.image_path, d.detection_date,
                          u.username, u.id AS user_id
                   FROM detection_history d
                   JOIN users u ON u.id = d.user_id
                   WHERE 1=1"""
        params = []
        if severity:
            query += " AND d.severity = %s"
            params.append(severity)
        if crop:
            query += " AND d.stage LIKE %s"
            params.append(f"%{crop}%")
        query += " ORDER BY d.detection_date DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching detections: {e}")
        return []
    finally:
        conn.close()


def get_all_contact_messages(filter_read=None, limit=200):
    """Return contact messages with optional unread filter."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """SELECT cm.*, u.username
                   FROM contact_messages cm
                   LEFT JOIN users u ON u.id = cm.user_id"""
        if filter_read == 'unread':
            query += " WHERE cm.is_read = 0 OR cm.is_read IS NULL"
        elif filter_read == 'read':
            query += " WHERE cm.is_read = 1"
        query += " ORDER BY cm.created_at DESC LIMIT %s"
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching contact messages: {e}")
        return []
    finally:
        conn.close()


def mark_message_read(message_id, is_read=1):
    conn = get_db_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE contact_messages SET is_read=%s WHERE id=%s", (is_read, message_id))
        conn.commit()
        return cursor.rowcount > 0
    except MySQLError as e:
        print(f"Error marking message: {e}")
        return False
    finally:
        conn.close()


def delete_message_admin(message_id):
    conn = get_db_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contact_messages WHERE id=%s", (message_id,))
        conn.commit()
        return cursor.rowcount > 0
    except MySQLError as e:
        print(f"Error deleting message: {e}")
        return False
    finally:
        conn.close()


def log_admin_action(admin_id, action, target_type=None, target_id=None, details=None):
    conn = get_db_connection()
    if conn is None: return
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO admin_logs (admin_id, action, target_type, target_id, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (admin_id, action, target_type, target_id, details)
        )
        conn.commit()
    except MySQLError as e:
        print(f"Error logging admin action: {e}")
    finally:
        conn.close()


def get_recent_admin_logs(limit=20):
    conn = get_db_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT al.*, u.username AS admin_name
               FROM admin_logs al
               JOIN users u ON u.id = al.admin_id
               ORDER BY al.created_at DESC LIMIT %s""",
            (limit,)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching admin logs: {e}")
        return []
    finally:
        conn.close()
        
# ============================================================
# Admin Market Manager helpers
# ============================================================

def get_admin_market_rows(search=None, limit=300):
    """Return all market_prices rows with crop names, for admin table."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if search:
            like = f"%{search}%"
            cursor.execute(
                """SELECT mp.id, mp.crop_id, mp.location, mp.market_name,
                          mp.price_per_kg, mp.date, mp.demand_level, mp.price_trend,
                          c.name AS crop_name, c.category AS crop_category
                   FROM market_prices mp
                   JOIN crops c ON c.id = mp.crop_id
                   WHERE c.name LIKE %s OR mp.location LIKE %s
                   ORDER BY mp.date DESC, c.name
                   LIMIT %s""",
                (like, like, limit)
            )
        else:
            cursor.execute(
                """SELECT mp.id, mp.crop_id, mp.location, mp.market_name,
                          mp.price_per_kg, mp.date, mp.demand_level, mp.price_trend,
                          c.name AS crop_name, c.category AS crop_category
                   FROM market_prices mp
                   JOIN crops c ON c.id = mp.crop_id
                   ORDER BY mp.date DESC, c.name
                   LIMIT %s""",
                (limit,)
            )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching market rows: {e}")
        return []
    finally:
        conn.close()


def get_market_summary_admin():
    """Quick stats for the admin market page."""
    conn = get_db_connection()
    if conn is None:
        return {}
    try:
        cursor = conn.cursor(dictionary=True)
        s = {}

        cursor.execute("SELECT COUNT(*) AS c FROM market_prices")
        s['total_rows'] = cursor.fetchone()['c']

        cursor.execute("SELECT COUNT(DISTINCT crop_id) AS c FROM market_prices")
        s['crops_tracked'] = cursor.fetchone()['c']

        cursor.execute("SELECT MAX(date) AS d FROM market_prices")
        row = cursor.fetchone()
        s['last_date'] = row['d'] if row else None

        cursor.execute("SELECT COUNT(*) AS c FROM crops")
        s['total_crops'] = cursor.fetchone()['c']

        return s
    except MySQLError as e:
        print(f"Error fetching market summary: {e}")
        return {}
    finally:
        conn.close()


def add_market_row_admin(crop_id, location, market_name, price_per_kg,
                        date_obj, demand_level='Medium', price_trend='Stable'):
    """Insert a single market price row."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO market_prices
               (crop_id, location, market_name, price_per_kg, date,
                demand_level, price_trend)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (crop_id, location, market_name, price_per_kg, date_obj,
             demand_level, price_trend)
        )
        conn.commit()
        return cursor.lastrowid
    except MySQLError as e:
        print(f"Error adding market row: {e}")
        return None
    finally:
        conn.close()


def update_market_row_admin(row_id, price_per_kg, location,
                            demand_level, price_trend):
    """Update an existing market_prices row."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE market_prices
               SET price_per_kg=%s, location=%s, demand_level=%s, price_trend=%s
               WHERE id=%s""",
            (price_per_kg, location, demand_level, price_trend, row_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except MySQLError as e:
        print(f"Error updating market row: {e}")
        return False
    finally:
        conn.close()


def delete_market_row_admin(row_id):
    """Delete one market_prices row."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM market_prices WHERE id=%s", (row_id,))
        conn.commit()
        return cursor.rowcount > 0
    except MySQLError as e:
        print(f"Error deleting market row: {e}")
        return False
    finally:
        conn.close()


def clear_all_market_prices_admin():
    """Delete all market_prices rows (admin-only, used before CSV upload)."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM market_prices")
        conn.commit()
        return True
    except MySQLError as e:
        print(f"Error clearing market rows: {e}")
        return False
    finally:
        conn.close()
        
# ============================================================
# Crop Details helpers
# ============================================================

def get_all_crops_with_details_flag():
    """Return all crops with a boolean: has AI details cached?"""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.id, c.name, c.category, c.growing_season,
                      c.market_price, c.harvest_days,
                      (cd.id IS NOT NULL) AS has_details
               FROM crops c
               LEFT JOIN crop_details cd ON cd.crop_id = c.id
               ORDER BY c.name"""
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching crops list: {e}")
        return []
    finally:
        conn.close()
        
        
def get_crop_by_id_admin(crop_id):
    """Return one crop row."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crops WHERE id = %s", (crop_id,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching crop: {e}")
        return None
    finally:
        conn.close()


def get_crop_details(crop_id):
    """Return the cached details JSON dict for a crop, or None."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT details_json, generated_by, updated_at FROM crop_details WHERE crop_id = %s",
            (crop_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        details = json.loads(row["details_json"]) if isinstance(row["details_json"], str) else row["details_json"]
        details["_meta"] = {
            "generated_by": row.get("generated_by"),
            "updated_at": row.get("updated_at"),
        }
        return details
    except MySQLError as e:
        print(f"Error fetching crop details: {e}")
        return None
    except json.JSONDecodeError:
        return None
    finally:
        conn.close()


def save_crop_details(crop_id, details_dict, generated_by='ai'):
    """Upsert crop details."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        payload = json.dumps(details_dict, ensure_ascii=False)
        cursor.execute(
            """INSERT INTO crop_details (crop_id, details_json, generated_by)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE
                 details_json = VALUES(details_json),
                 generated_by = VALUES(generated_by),
                 updated_at = CURRENT_TIMESTAMP""",
            (crop_id, payload, generated_by)
        )
        conn.commit()
        return True
    except MySQLError as e:
        print(f"Error saving crop details: {e}")
        return False
    finally:
        conn.close()


def delete_crop_details(crop_id):
    """Remove cached details (for regeneration)."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM crop_details WHERE crop_id = %s", (crop_id,))
        conn.commit()
        return True
    except MySQLError as e:
        print(f"Error deleting crop details: {e}")
        return False
    finally:
        conn.close()

# ============================================================
# Agriculture Stores helpers
# ============================================================

def get_stores(district=None, store_type=None, limit=200):
    """Return agriculture stores with optional district/type filters."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM agriculture_stores WHERE 1=1"
        params = []
        if district:
            query += " AND district = %s"
            params.append(district)
        if store_type:
            query += " AND store_type = %s"
            params.append(store_type)
        query += " ORDER BY rating DESC, name LIMIT %s"
        params.append(limit)
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching stores: {e}")
        return []
    finally:
        conn.close()


def get_store_by_id(store_id):
    """Return one store by ID."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM agriculture_stores WHERE id = %s", (store_id,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching store: {e}")
        return None
    finally:
        conn.close()


def get_store_districts():
    """Return unique district list for filter dropdown."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT DISTINCT district FROM agriculture_stores "
            "WHERE district IS NOT NULL ORDER BY district"
        )
        return [r["district"] for r in cursor.fetchall()]
    except MySQLError as e:
        print(f"Error fetching districts: {e}")
        return []
    finally:
        conn.close()

# ============================================================
# Learning Hub helpers
# ============================================================

def get_learning_articles(category=None, limit=100):
    """Return learning articles, optionally filtered by category."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if category:
            cursor.execute(
                """SELECT id, title_en, title_ml, category, summary_en, summary_ml,
                          tags, read_minutes, is_ai_generated, created_at
                   FROM learning_articles
                   WHERE category = %s
                   ORDER BY created_at DESC LIMIT %s""",
                (category, limit)
            )
        else:
            cursor.execute(
                """SELECT id, title_en, title_ml, category, summary_en, summary_ml,
                          tags, read_minutes, is_ai_generated, created_at
                   FROM learning_articles
                   ORDER BY created_at DESC LIMIT %s""",
                (limit,)
            )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching learning articles: {e}")
        return []
    finally:
        conn.close()


def get_learning_article(article_id):
    """Return one article with full content."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM learning_articles WHERE id = %s", (article_id,))
        return cursor.fetchone()
    except MySQLError as e:
        print(f"Error fetching article: {e}")
        return None
    finally:
        conn.close()


def get_learning_categories():
    """Return distinct categories with article counts."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT category, COUNT(*) AS c
               FROM learning_articles
               WHERE category IS NOT NULL
               GROUP BY category
               ORDER BY category"""
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error fetching categories: {e}")
        return []
    finally:
        conn.close()


def search_learning_articles(query, limit=20):
    """Simple keyword search over titles, summaries, tags."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        like = f"%{query}%"
        cursor.execute(
            """SELECT id, title_en, title_ml, category, summary_en, summary_ml,
                      tags, read_minutes, is_ai_generated, created_at
               FROM learning_articles
               WHERE title_en LIKE %s OR title_ml LIKE %s
                     OR summary_en LIKE %s OR tags LIKE %s
               ORDER BY created_at DESC LIMIT %s""",
            (like, like, like, like, limit)
        )
        return cursor.fetchall()
    except MySQLError as e:
        print(f"Error searching articles: {e}")
        return []
    finally:
        conn.close()