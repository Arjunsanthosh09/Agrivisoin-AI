import re
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error as MySQLError

from config import Config
from database.db_connection import get_user_by_email, get_user_by_username, get_user_by_id, create_user

app = Flask(__name__)
app.config.from_object(Config)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    # Landing page shows the homepage; Login/Sign Up buttons on it link to /login and /register
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        location = request.form.get("location", "").strip() or None
        farming_experience = request.form.get("farming_experience", "").strip()
        preferred_language = request.form.get("preferred_language", "en")

        # ---- Validation ----
        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if preferred_language not in ("en", "ml"):
            preferred_language = "en"

        farming_experience_val = None
        if farming_experience:
            if farming_experience.isdigit():
                farming_experience_val = int(farming_experience)
            else:
                errors.append("Farming experience must be a whole number of years.")

        if not errors:
            try:
                # Check if user exists
                existing_username = get_user_by_username(username)
                if existing_username:
                    errors.append("That username is already taken.")
                    print(f"⚠️ Username '{username}' already exists: {existing_username}")
                
                existing_email = get_user_by_email(email)
                if existing_email:
                    errors.append("An account with that email already exists.")
                    print(f"⚠️ Email '{email}' already exists: {existing_email}")
                    
            except MySQLError as e:
                errors.append(f"Database error: {e}")
                print(f"❌ Database error checking existing user: {e}")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template(
                "register.html",
                form_data={
                    "username": username,
                    "email": email,
                    "location": location or "",
                    "farming_experience": farming_experience,
                    "preferred_language": preferred_language,
                },
            )

        # ---- Create user ----
        try:
            password_hash = generate_password_hash(password)
            print(f"📝 Attempting to create user: {username}, {email}")
            print(f"   Password hash: {password_hash[:20]}...")
            
            user_id = create_user(
                username=username,
                email=email,
                password_hash=password_hash,
                location=location,
                farming_experience=farming_experience_val,
                preferred_language=preferred_language,
            )
            
            print(f"✅ create_user returned: {user_id}")
            
            if user_id:
                flash("Account created successfully! Please log in.", "success")
                print(f"✅ User created successfully with ID: {user_id}")
                return redirect(url_for("login"))
            else:
                flash("Could not create account. Please try again.", "error")
                print("❌ create_user returned None - user not created")
                
        except MySQLError as e:
            flash(f"Could not create account: {e}", "error")
            print(f"❌ MySQL Error creating user: {e}")
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", "error")
            print(f"❌ Unexpected error creating user: {e}")
            import traceback
            traceback.print_exc()

    return render_template("register.html", form_data={})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        if not identifier or not password:
            flash("Please enter your email/username and password.", "error")
            return render_template("login.html")

        try:
            user = get_user_by_email(identifier) or get_user_by_username(identifier)
        except MySQLError as e:
            flash(f"Database error: {e}", "error")
            return render_template("login.html")

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["preferred_language"] = user.get("preferred_language", "en")
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email/username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_user_by_id(session["user_id"])
    return render_template("dashboard.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)