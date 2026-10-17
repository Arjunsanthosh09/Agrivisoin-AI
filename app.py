
import re
import os
import json
import numpy as np
from functools import wraps
from backend.utils.groq_helper import generate_crop_details, generate_crop_narrative, answer_farmer_query
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from mysql.connector import Error as MySQLError

import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model

from backend.utils.weather_api import fetch_weather
from config import Config

from database.db_connection import (
    get_dashboard_stats,
    get_recent_detections,
    get_recent_recommendations,
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    create_user,
    get_db_connection,
    save_detection_record,
    get_disease_info,
    get_crops_by_season,
    get_crop_loss_stats,
    get_crop_disease_risk,
    save_recommendation_record,
    get_user_recommendation_history,
    get_government_schemes,
    # Chatbot
    save_chat_message,
    get_user_chat_history,
    get_last_detection,
    # Dashboard
    get_dashboard_stats,
    get_recent_detections,
    get_recent_recommendations,
    # Detection History
    get_all_detections,
    # Market
    get_crop_price_summary,
    get_price_history,
    get_crop_price_trend,
    get_user_preferences,
    save_user_preferences,
    update_user_profile,
    # Contact
    save_contact_message,
        # Admin
    get_admin_dashboard_stats,
    get_all_users_admin,
    get_user_detail_admin,
    toggle_user_active_admin,
    delete_user_admin,
    get_all_detections_admin,
    get_all_contact_messages,
    mark_message_read,
    delete_message_admin,
    log_admin_action,
    get_recent_admin_logs,
        # Admin Market
    get_admin_market_rows,
    get_market_summary_admin,
    add_market_row_admin,
    update_market_row_admin,
    delete_market_row_admin,
     clear_all_market_prices_admin,
    # Crop Details
    get_all_crops_with_details_flag,
    get_crop_by_id_admin,
    get_crop_details,
    save_crop_details,
    delete_crop_details,
        # Agriculture Stores
    get_stores,
    get_store_by_id,
    get_store_districts,
    # Learning Hub
    get_learning_articles,
    get_learning_article,
    get_learning_categories,
    search_learning_articles,
)



from backend.utils.groq_helper import (
    generate_crop_narrative,
    answer_farmer_query,
    search_government_schemes,
    generate_market_insight,
    generate_disease_risk_alert,
    generate_crop_details,   # ← should already be here
    generate_learning_topic,      # NEW
    summarize_learning_article,   # NEW
)


from backend.utils.disease_risk import predict_top_risks   # NEW

app = Flask(__name__)
app.config.from_object(Config)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH        = os.path.join(BASE_DIR, 'backend', 'ml_models', 'disease_detection', 'model_weights.h5')
CLASS_IDX_PATH    = os.path.join(BASE_DIR, 'backend', 'ml_models', 'disease_detection', 'class_indices.json')
DISEASE_INFO_PATH = os.path.join(BASE_DIR, 'backend', 'ml_models', 'disease_detection', 'disease_info.json')

print("🔬 Loading disease detection model...")
disease_model = load_model(MODEL_PATH)

with open(CLASS_IDX_PATH, encoding='utf-8') as f:
    class_indices = json.load(f)
IDX_TO_CLASS = {v: k for k, v in class_indices.items()}

with open(DISEASE_INFO_PATH, encoding='utf-8') as f:
    DISEASE_INFO = json.load(f)

print(f"✅ Model loaded. {len(IDX_TO_CLASS)} classes available.")

UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
ALLOWED_EXT = {'png', 'jpg', 'jpeg'}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@app.route("/")
def index():
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
                if get_user_by_username(username):
                    errors.append("That username is already taken.")
                if get_user_by_email(email):
                    errors.append("An account with that email already exists.")
            except MySQLError as e:
                errors.append(f"Database error: {e}")

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
            user_id = create_user(
                username=username,
                email=email,
                password_hash=password_hash,
                location=location,
                farming_experience=farming_experience_val,
                preferred_language=preferred_language,
            )

            if user_id:
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for("login"))
            else:
                flash("Could not create account. Please try again.", "error")

        except MySQLError as e:
            flash(f"Could not create account: {e}", "error")
        except Exception as e:
            flash(f"An unexpected error occurred: {e}", "error")
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
            session["role"] = user.get("role", "farmer")
            flash(f"Welcome back, {user['username']}!", "success")

            # Redirect admins straight to the admin panel
            if user.get("role") == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))

        flash("Invalid email/username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as admin.", "error")
            return redirect(url_for("login"))
        # NEW: re-check role from DB every time
        fresh_user = get_user_by_id(session["user_id"])
        if not fresh_user or fresh_user.get("role") != "admin":
            session.clear()
            flash("Admin access revoked.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_user_by_id(session["user_id"])
    stats = get_dashboard_stats(session["user_id"])
    recent_detections = get_recent_detections(session["user_id"], limit=5)
    recent_recommendations = get_recent_recommendations(session["user_id"], limit=5)
    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        recent_detections=recent_detections,
        recent_recommendations=recent_recommendations,
    )


@app.route("/detect", methods=["GET"])
@login_required
def detect_page():
    return render_template("disease_detection.html")


@app.route("/detect", methods=["POST"])
@login_required
def detect_predict():
    if "leaf_image" not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("detect_page"))

    file = request.files["leaf_image"]
    if file.filename == "":
        flash("Please select an image.", "error")
        return redirect(url_for("detect_page"))

    if not allowed_file(file.filename):
        flash("Only PNG, JPG, and JPEG files are allowed.", "error")
        return redirect(url_for("detect_page"))

    filename = secure_filename(f"user{session['user_id']}_{file.filename}")
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    is_leaf, green_ratio = is_likely_leaf(save_path, min_green_ratio=0.15)
    if not is_leaf:
        flash(
            f"This doesn't look like a leaf image (only {green_ratio*100:.1f}% green). "
            "Please upload a close-up photo of a single leaf.",
            "error"
        )
        try:
            os.remove(save_path)
        except Exception:
            pass
        return redirect(url_for("detect_page"))

    img = image.load_img(save_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    preds = disease_model.predict(img_array, verbose=0)
    pred_idx = int(np.argmax(preds[0]))
    confidence = float(np.max(preds[0])) * 100
    class_name = IDX_TO_CLASS[pred_idx]

    if confidence < 70.0:
        flash(
            f"Low confidence ({confidence:.2f}%). This doesn't look like a "
            "clear leaf image. Please upload a close-up photo of a single leaf.",
            "error"
        )
        try:
            os.remove(save_path)
        except Exception:
            pass
        return redirect(url_for("detect_page"))

    info = DISEASE_INFO.get(class_name, {})

    disease_id = None
    try:
        db_disease = get_disease_info(info.get("disease_en", class_name))
        if db_disease:
            disease_id = db_disease["id"]
    except Exception as e:
        print(f"⚠️ disease lookup failed: {e}")

    try:
        save_detection_record(
            user_id=session["user_id"],
            disease_id=disease_id,
            severity=info.get("severity_en", "Unknown"),
            stage=info.get("type_en", "Unknown"),
            confidence=confidence,
            image_path=filename,
        )
    except Exception as e:
        print(f"⚠️ Could not save detection: {e}")

    return render_template(
        "detection_result.html",
        class_name=class_name,
        info=info,
        confidence=round(confidence, 2),
        image_url=url_for('static', filename=f'uploads/{filename}'),
    )

def is_likely_leaf(image_path, min_green_ratio=0.15):
    """
    Heuristic check: is this image likely a leaf?
    Returns (is_leaf: bool, green_ratio: float)
    """
    from PIL import Image
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((128, 128))  # speed
        pixels = list(img.getdata())
        total = len(pixels)

        green_count = 0
        for r, g, b in pixels:
            # Green if G is dominant and pixel isn't too dark or too bright
            if g > r and g > b and g > 40 and not (r > 200 and g > 200 and b > 200):
                green_count += 1

        ratio = green_count / total
        return (ratio >= min_green_ratio, ratio)
    except Exception as e:
        print(f"⚠️ is_likely_leaf error: {e}")
        return (False, 0.0)


def score_crop(crop, user_ph, user_temp, user_rain, season):
    """
    Score a crop from 0-100 based on how well user's conditions match.
    Weights: pH 30, temp 30, rainfall 25, disease-risk 15.
    """
    score = 0
    reasons = []

    # ---- pH match (30) ----
    if crop['ideal_soil_ph_min'] <= user_ph <= crop['ideal_soil_ph_max']:
        score += 30
        reasons.append(
            f"Soil pH {user_ph} is ideal "
            f"(range {crop['ideal_soil_ph_min']}–{crop['ideal_soil_ph_max']})"
        )
    else:
        diff = min(abs(user_ph - crop['ideal_soil_ph_min']),
                   abs(user_ph - crop['ideal_soil_ph_max']))
        ph_score = max(0, 30 - diff * 10)
        score += ph_score
        if ph_score > 15:
            reasons.append(
                f"Soil pH {user_ph} is close to ideal "
                f"({crop['ideal_soil_ph_min']}–{crop['ideal_soil_ph_max']})"
            )
        else:
            reasons.append("Soil pH is not ideal — consider amending soil")

    # ---- Temperature match (30) ----
    if crop['ideal_temperature_min'] <= user_temp <= crop['ideal_temperature_max']:
        score += 30
        reasons.append(f"Temperature {user_temp}°C is ideal")
    else:
        diff = min(abs(user_temp - crop['ideal_temperature_min']),
                   abs(user_temp - crop['ideal_temperature_max']))
        temp_score = max(0, 30 - diff * 3)
        score += temp_score
        reasons.append(
            f"Temperature {user_temp}°C is slightly off "
            f"(ideal {crop['ideal_temperature_min']}–{crop['ideal_temperature_max']}°C)"
        )

    # ---- Rainfall match (25) ----
    if crop['ideal_rainfall_min'] <= user_rain <= crop['ideal_rainfall_max']:
        score += 25
        reasons.append(f"Rainfall {user_rain} mm is ideal")
    else:
        diff = min(abs(user_rain - crop['ideal_rainfall_min']),
                   abs(user_rain - crop['ideal_rainfall_max']))
        rain_score = max(0, 25 - diff * 0.02)
        score += rain_score
        reasons.append(
            f"Rainfall {user_rain} mm is slightly off "
            f"(ideal {crop['ideal_rainfall_min']}–{crop['ideal_rainfall_max']} mm)"
        )

    # ---- Disease risk penalty (15) ----
    risk = get_crop_disease_risk(crop['id'], season)
    risk_penalty = {'low': 0, 'medium': 5, 'high': 10, 'very_high': 15}.get(risk, 5)
    score += (15 - risk_penalty)
    if risk in ('high', 'very_high'):
        reasons.append(f"⚠️ High disease risk in {season} — needs preventive care")
    elif risk == 'medium':
        reasons.append("Moderate disease risk — monitor regularly")

    return round(score, 2), reasons, risk

# ============================================================
# Routes: Crop Recommendation
# ============================================================
@app.route("/recommend", methods=["GET"])
@login_required
def recommend_page():
    return render_template("crop_recommendation.html")


@app.route("/recommend", methods=["POST"])
@login_required
def recommend_predict():
    location = request.form.get("location", "").strip()
    season   = request.form.get("season", "Kharif").strip()
    soil_ph  = request.form.get("soil_ph", "").strip()
    temp     = request.form.get("temperature", "").strip()
    rainfall = request.form.get("rainfall", "").strip()

    # ---- Validation ----
    errors = []
    if not location:
        errors.append("Please enter your location.")

    try:
        soil_ph_f = float(soil_ph)
        if not (0 <= soil_ph_f <= 14):
            errors.append("Soil pH must be between 0 and 14.")
    except ValueError:
        errors.append("Soil pH must be a number.")
        soil_ph_f = 6.5

    try:
        temp_f = float(temp)
    except ValueError:
        errors.append("Temperature must be a number.")
        temp_f = 25.0

    try:
        rain_f = float(rainfall)
    except ValueError:
        errors.append("Rainfall must be a number.")
        rain_f = 700.0

    if errors:
        for err in errors:
            flash(err, "error")
        return render_template("crop_recommendation.html")

    # ---- Get candidate crops ----
    candidates = get_crops_by_season(season)
    if not candidates:
        flash(f"No crops found for season {season}. Try a different season.", "error")
        return render_template("crop_recommendation.html")

    # ---- Score each crop ----
        # ---- Score each crop ----
    results = []
    for crop in candidates:
        score, reasons, risk = score_crop(crop, soil_ph_f, temp_f, rain_f, season)

        # Base yield assumption
        expected_yield_kg_per_acre = 2000

        # ---- Get real price trend from market_prices ----
        trend = get_crop_price_trend(crop['id'], months=6)

        # Determine price basis
        if trend:
            base_price = trend['current']
            # Momentum multiplier: up → optimistic, down → conservative
            if trend['momentum'] == 'up':
                optimistic_mult = 1.10
                conservative_mult = 0.95
            elif trend['momentum'] == 'down':
                optimistic_mult = 0.95
                conservative_mult = 0.85
            else:
                optimistic_mult = 1.05
                conservative_mult = 0.95
        else:
            base_price = float(crop['market_price'])
            optimistic_mult = 1.05
            conservative_mult = 0.95
            trend = {
                'current': base_price,
                'avg_older': base_price,
                'trend_pct': 0.0,
                'momentum': 'flat',
                'history': [base_price] * 6,
            }

        # ---- Profit range ----
        score_factor = score / 100.0
        profit_base         = round(base_price * expected_yield_kg_per_acre * score_factor, 0)
        profit_conservative = round(profit_base * conservative_mult, 0)
        profit_optimistic   = round(profit_base * optimistic_mult, 0)

        loss_stats = get_crop_loss_stats(crop['id'])

        results.append({
            "crop": crop,
            "score": score,
            "reasons": reasons,
            "risk": risk,
            "expected_profit": profit_base,
            "profit_conservative": profit_conservative,
            "profit_optimistic": profit_optimistic,
            "price_trend": trend,
            "historical_loss": round(loss_stats.get("avg_loss") or 0, 2),
        })

        # Save the expected (mid) profit
        try:
            save_recommendation_record(
                user_id=session["user_id"],
                crop_id=crop['id'],
                location=location,
                season=season,
                suitability_score=score,
                profit_estimate=profit_base,
                disease_risk=risk,
            )
        except Exception as e:
            print(f"⚠️ Could not save recommendation: {e}")

    # ---- Top 5 ----
    results.sort(key=lambda r: r["score"], reverse=True)
    top5 = results[:5]
        # ---- Groq AI: generate personalized narrative ----
    ai_narrative = None
    try:
        ai_narrative = generate_crop_narrative(
            location=location,
            season=season,
            soil_ph=soil_ph_f,
            temperature=temp_f,
            rainfall=rain_f,
            top_crops=[
                {
                    "name": r["crop"]["name"],
                    "score": r["score"],
                    "risk": r["risk"],
                    "expected_profit": r["expected_profit"],
                }
                for r in top5
            ],
            language=session.get("preferred_language", "en"),
        )
    except Exception as e:
        print(f"⚠️ AI narrative generation failed: {e}")

    return render_template(
        "recommendation_result.html",
        results=top5,
        location=location,
        season=season,
        soil_ph=soil_ph_f,
        temperature=temp_f,
        rainfall=rain_f,
        ai_narrative=ai_narrative,   # ← new
    )
    
# ============================================================
# Routes: Chatbot
# ============================================================
@app.route("/chatbot", methods=["GET"])
@login_required
def chatbot_page():
    # Load past chat history so the conversation continues
    history = get_user_chat_history(session["user_id"], limit=50)
    return render_template("chatbot.html", history=history)


@app.route("/chatbot/send", methods=["POST"])
@login_required
def chatbot_send():
    """
    AJAX endpoint: receive a user message, call Groq, save both to DB,
    return JSON with the bot reply.
    """
    from flask import jsonify

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # ---- Build context from user's recent activity ----
    context = {}
    try:
        last_det = get_last_detection(session["user_id"])
        if last_det:
            context["last_detection"] = {
                "severity": last_det.get("severity"),
                "type": last_det.get("stage"),
                "confidence": float(last_det.get("confidence") or 0),
            }
        context["username"] = session.get("username")
    except Exception as e:
        print(f"⚠️ context build failed: {e}")

    # ---- Ask Groq ----
        # ---- Pick language: use the one sent from the browser, fall back to session ----
    language = (data.get("language") or "").strip().lower()
    if language not in ("en", "ml"):
        language = session.get("preferred_language", "en")
    try:
        bot_reply = answer_farmer_query(
            user_message=user_message,
            context=context,
            language=language,
        )
    except Exception as e:
        print(f"⚠️ Chatbot error: {e}")
        bot_reply = (
            "Sorry, I couldn't process that right now. Please try again."
            if language == "en"
            else "ക്ഷമിക്കണം, ഇപ്പോൾ അത് പ്രോസസ്സ് ചെയ്യാൻ കഴിഞ്ഞില്ല. വീണ്ടും ശ്രമിക്കുക."
        )

    # ---- Save to DB ----
    try:
        save_chat_message(
            user_id=session["user_id"],
            user_message=user_message,
            bot_response=bot_reply,
            language=language,
        )
    except Exception as e:
        print(f"⚠️ chat save failed: {e}")

    return jsonify({
        "reply": bot_reply,
        "language": language,
    })

# ============================================================
# Routes: Detection History
# ============================================================
@app.route("/history")
@login_required
def history_page():
    detections = get_all_detections(session["user_id"], limit=100)
    return render_template("detection_history.html", detections=detections)
 

# ============================================================
# Routes: Government Schemes
# ============================================================
# ============================================================
# Routes: Government Schemes
# ============================================================
@app.route("/schemes")
@login_required
def schemes_page():
    state_filter = request.args.get("state", "").strip() or None
    schemes = get_government_schemes(state=state_filter)
    return render_template(
        "government_schemes.html",
        schemes=schemes,
        selected_state=state_filter,
    )


@app.route("/schemes/search", methods=["POST"])
@login_required
def schemes_search():
    """
    AJAX endpoint: user types a natural-language query,
    Groq generates matching schemes, returns JSON.
    """
    from flask import jsonify

    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    # Language: use the one sent from browser, fall back to session
    language = (data.get("language") or "").strip().lower()
    if language not in ("en", "ml"):
        language = session.get("preferred_language", "en")

    # Build user context
    user = get_user_by_id(session["user_id"])
    user_context = {
        "location": user.get("location") if user else None,
        "farming_experience": user.get("farming_experience") if user else None,
    }

    schemes = search_government_schemes(
        query=query,
        user_context=user_context,
        language=language,
    )
    return jsonify({"schemes": schemes, "language": language})
    

# ============================================================
# Routes: Market Prices
# ============================================================
# ============================================================
# Routes: Market Prices
# ============================================================
@app.route("/market")
@login_required
def market_page():
    price_summary = get_crop_price_summary()

    ai_insight = None
    try:
        if price_summary:
            ai_insight = generate_market_insight(
                price_summary=price_summary,
                language=session.get("preferred_language", "en"),
            )
    except Exception as e:
        print(f"⚠️ Market insight generation failed: {e}")

    return render_template(
        "market_prices.html",
        prices=price_summary,
        ai_insight=ai_insight,
    )

@app.route("/market/<int:crop_id>")
@login_required
def market_detail(crop_id):
    history_raw = get_price_history(crop_id, months=6)

    conn = get_db_connection()
    crop = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM crops WHERE id = %s", (crop_id,))
            crop = cursor.fetchone()
        finally:
            conn.close()

    if not crop:
        flash("Crop not found.", "error")
        return redirect(url_for("market_page"))

    # ---- Convert Decimal → float for template safety ----
    history = [
        {**h, 'price_per_kg': float(h['price_per_kg'])}
        for h in history_raw
    ]

    max_price = max((h['price_per_kg'] for h in history), default=1.0)
    min_price = min((h['price_per_kg'] for h in history), default=0.0)
    avg_price = (sum(h['price_per_kg'] for h in history) / len(history)) if history else 0.0

    return render_template(
        "market_detail.html",
        crop=crop,
        history=history,
        max_price=round(max_price, 2),
        min_price=round(min_price, 2),
        avg_price=round(avg_price, 2),
    )

# ============================================================
# Routes: User Profile
# ============================================================
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    user = get_user_by_id(session["user_id"])
    prefs = get_user_preferences(session["user_id"]) or {}

    if request.method == "POST":
        location = request.form.get("location", "").strip() or None
        farming_exp = request.form.get("farming_experience", "").strip()
        preferred_language = request.form.get("preferred_language", "en")
        preferred_crops = request.form.get("preferred_crops", "").strip() or None
        soil_type = request.form.get("soil_type", "").strip() or None
        farm_size_raw = request.form.get("farm_size", "").strip()
        irrigation_type = request.form.get("irrigation_type", "").strip() or None

        errors = []
        farming_exp_val = None
        if farming_exp:
            if farming_exp.isdigit():
                farming_exp_val = int(farming_exp)
            else:
                errors.append("Farming experience must be a whole number.")

        farm_size_val = None
        if farm_size_raw:
            try:
                farm_size_val = float(farm_size_raw)
                if farm_size_val < 0:
                    errors.append("Farm size must be positive.")
            except ValueError:
                errors.append("Farm size must be a number.")

        if preferred_language not in ("en", "ml"):
            preferred_language = "en"

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("profile.html", user=user, prefs=prefs)

        # Save to both tables
        ok1 = update_user_profile(
            user_id=session["user_id"],
            location=location,
            farming_experience=farming_exp_val,
            preferred_language=preferred_language,
        )
        ok2 = save_user_preferences(
            user_id=session["user_id"],
            preferred_crops=preferred_crops,
            soil_type=soil_type,
            farm_size=farm_size_val,
            irrigation_type=irrigation_type,
        )

        if ok1 and ok2:
            # Update session language so chatbot/recommendations respect it
            session["preferred_language"] = preferred_language
            flash("Profile updated successfully!", "success")
        else:
            flash("Some fields could not be saved. Please try again.", "error")

        return redirect(url_for("profile_page"))

    return render_template("profile.html", user=user, prefs=prefs)


# ============================================================
# Routes: About & Contact
# ============================================================
@app.route("/about")
def about_page():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    user = None
    if session.get("user_id"):
        user = get_user_by_id(session["user_id"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        errors = []
        if len(name) < 2:
            errors.append("Please enter your name.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email.")
        if len(message) < 10:
            errors.append("Message must be at least 10 characters.")

        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("contact.html", user=user)

        mid = save_contact_message(
            user_id=session.get("user_id"),
            name=name, email=email, subject=subject, message=message,
        )
        if mid:
            flash("Thanks! Your message has been received. We'll get back to you soon.", "success")
        else:
            flash("Could not send your message. Please try again.", "error")
        return redirect(url_for("contact_page"))

    return render_template("contact.html", user=user)

# ============================================================
# Routes: Disease Risk Prediction
# ============================================================
@app.route("/disease-risk", methods=["GET"])
@login_required
def disease_risk_page():
    crops = sorted({
        info.get("crop_en", "")
        for info in DISEASE_INFO.values()
        if info.get("crop_en")
    })
    return render_template("disease_risk.html", crops=crops)


@app.route("/disease-risk", methods=["POST"])
@login_required
def disease_risk_predict():
    location = request.form.get("location", "").strip()
    crop     = request.form.get("crop", "").strip()
    temp_raw = request.form.get("temperature", "").strip()
    hum_raw  = request.form.get("humidity", "").strip()
    rain_raw = request.form.get("rainfall", "").strip()

    errors = []
    if not location:
        errors.append("Please enter your location.")

    try:
        temp = float(temp_raw)
        if not (-10 <= temp <= 55):
            errors.append("Temperature must be between -10 and 55°C.")
    except ValueError:
        errors.append("Temperature must be a number.")
        temp = 25.0

    try:
        humidity = float(hum_raw)
        if not (0 <= humidity <= 100):
            errors.append("Humidity must be between 0 and 100%.")
    except ValueError:
        errors.append("Humidity must be a number.")
        humidity = 70.0

    try:
        rainfall = float(rain_raw)
        if rainfall < 0:
            errors.append("Rainfall cannot be negative.")
    except ValueError:
        errors.append("Rainfall must be a number.")
        rainfall = 0.0

    if errors:
        for e in errors:
            flash(e, "error")
        crops = sorted({
            info.get("crop_en", "")
            for info in DISEASE_INFO.values()
            if info.get("crop_en")
        })
        return render_template("disease_risk.html", crops=crops)

    top_risks = predict_top_risks(
        DISEASE_INFO,
        temp=temp, humidity=humidity, rainfall=rainfall,
        crop_filter=crop if crop else None,
        top_n=8,
    )

    if not top_risks:
        flash("No significant disease risks for these conditions. Great news!", "success")
        return redirect(url_for("disease_risk_page"))

    language = session.get("preferred_language", "en")
    advisory, plan = generate_disease_risk_alert(
        location=location, crop=crop,
        temp=temp, humidity=humidity, rainfall=rainfall,
        top_risks=top_risks, language=language,
    )

    return render_template(
        "disease_risk_result.html",
        location=location,
        crop=crop or "All crops",
        temp=temp, humidity=humidity, rainfall=rainfall,
        risks=top_risks,
        advisory=advisory,
        plan=plan,
    )

# ============================================================
# Routes: Admin Module
# ============================================================
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = get_admin_dashboard_stats()
    logs = get_recent_admin_logs(limit=10)
    return render_template("admin_dashboard.html", stats=stats, logs=logs)


@app.route("/admin/users")
@admin_required
def admin_users():
    search = request.args.get("q", "").strip() or None
    users = get_all_users_admin(search=search)
    return render_template("admin_users.html", users=users, search=search or "")


@app.route("/admin/users/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    user = get_user_detail_admin(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_users"))
    return render_template("admin_user_detail.html", u=user)


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def admin_user_toggle(user_id):
    if user_id == session["user_id"]:
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("admin_users"))
    new_state = request.form.get("active", "0") == "1"
    if toggle_user_active_admin(user_id, new_state):
        log_admin_action(session["user_id"], "toggle_user",
                         "user", user_id, f"active={new_state}")
        flash(f"User {'activated' if new_state else 'deactivated'}.", "success")
    else:
        flash("Could not update user.", "error")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_user_delete(user_id):
    if user_id == session["user_id"]:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin_users"))
    if delete_user_admin(user_id):
        log_admin_action(session["user_id"], "delete_user", "user", user_id, None)
        flash("User deleted.", "success")
    else:
        flash("Could not delete user.", "error")
    return redirect(url_for("admin_users"))


@app.route("/admin/detections")
@admin_required
def admin_detections():
    severity = request.args.get("severity", "").strip() or None
    crop = request.args.get("crop", "").strip() or None
    rows = get_all_detections_admin(limit=200, severity=severity, crop=crop)
    return render_template("admin_detections.html", rows=rows,
                          severity=severity or "", crop=crop or "")


@app.route("/admin/messages")
@admin_required
def admin_messages():
    filt = request.args.get("filter", "all").strip()
    if filt not in ("all", "unread", "read"):
        filt = "all"
    msgs = get_all_contact_messages(filter_read=None if filt == "all" else filt)
    return render_template("admin_messages.html", messages=msgs, filter=filt)


@app.route("/admin/messages/<int:mid>/read", methods=["POST"])
@admin_required
def admin_message_mark_read(mid):
    mark_message_read(mid, 1)
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/<int:mid>/delete", methods=["POST"])
@admin_required
def admin_message_delete(mid):
    if delete_message_admin(mid):
        log_admin_action(session["user_id"], "delete_message", "contact_message", mid, None)
        flash("Message deleted.", "success")
    else:
        flash("Could not delete message.", "error")
    return redirect(url_for("admin_messages"))

# ============================================================
# Routes: Admin — Market Manager
# ============================================================
@app.route("/admin/market")
@admin_required
def admin_market():
    search = request.args.get("q", "").strip() or None
    rows = get_admin_market_rows(search=search, limit=300)
    summary = get_market_summary_admin()

    # Get crop list for the "Add new" form dropdown
    crops = []
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, category FROM crops ORDER BY name")
            crops = cursor.fetchall()
            conn.close()
    except Exception as e:
        print(f"⚠️ Could not load crops: {e}")

    return render_template(
        "admin_market.html",
        rows=rows,
        summary=summary,
        crops=crops,
        search=search or "",
    )


@app.route("/admin/market/add", methods=["POST"])
@admin_required
def admin_market_add():
    from datetime import datetime as dt

    crop_id = request.form.get("crop_id", "").strip()
    location = request.form.get("location", "").strip() or "Kerala"
    market_name = request.form.get("market_name", "").strip() or "Kerala State Mandi"
    price_raw = request.form.get("price_per_kg", "").strip()
    date_raw = request.form.get("date", "").strip()
    demand = request.form.get("demand_level", "Medium")
    trend = request.form.get("price_trend", "Stable")

    errors = []
    try:
        crop_id = int(crop_id)
    except (ValueError, TypeError):
        errors.append("Please select a crop.")

    try:
        price_per_kg = float(price_raw)
        if price_per_kg <= 0:
            errors.append("Price must be a positive number.")
    except ValueError:
        errors.append("Price must be a number.")
        price_per_kg = 0

    date_obj = None
    if date_raw:
        try:
            date_obj = dt.strptime(date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid date format.")
    if not date_obj:
        from datetime import date as _date
        date_obj = _date.today()

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("admin_market"))

    rid = add_market_row_admin(
        crop_id=crop_id, location=location, market_name=market_name,
        price_per_kg=price_per_kg, date_obj=date_obj,
        demand_level=demand, price_trend=trend,
    )
    if rid:
        log_admin_action(session["user_id"], "add_market_row",
                         "market_price", rid, f"crop_id={crop_id} price={price_per_kg}")
        flash("Market price row added.", "success")
    else:
        flash("Could not add row.", "error")
    return redirect(url_for("admin_market"))


@app.route("/admin/market/<int:rid>/update", methods=["POST"])
@admin_required
def admin_market_update(rid):
    price_raw = request.form.get("price_per_kg", "").strip()
    location = request.form.get("location", "").strip() or "Kerala"
    demand = request.form.get("demand_level", "Medium")
    trend = request.form.get("price_trend", "Stable")

    try:
        price_per_kg = float(price_raw)
        if price_per_kg <= 0:
            raise ValueError
    except ValueError:
        flash("Invalid price.", "error")
        return redirect(url_for("admin_market"))

    if update_market_row_admin(rid, price_per_kg, location, demand, trend):
        log_admin_action(session["user_id"], "update_market_row",
                         "market_price", rid, f"new_price={price_per_kg}")
        flash("Market price updated.", "success")
    else:
        flash("Could not update row.", "error")
    return redirect(url_for("admin_market"))


@app.route("/admin/market/<int:rid>/delete", methods=["POST"])
@admin_required
def admin_market_delete(rid):
    if delete_market_row_admin(rid):
        log_admin_action(session["user_id"], "delete_market_row",
                         "market_price", rid, None)
        flash("Row deleted.", "success")
    else:
        flash("Could not delete row.", "error")
    return redirect(url_for("admin_market"))


@app.route("/admin/market/clear", methods=["POST"])
@admin_required
def admin_market_clear():
    confirm = request.form.get("confirm", "").strip()
    if confirm != "DELETE":
        flash("Type DELETE in the box to confirm.", "error")
        return redirect(url_for("admin_market"))

    if clear_all_market_prices_admin():
        log_admin_action(session["user_id"], "clear_market_prices",
                         "market_price", None, "cleared all rows")
        flash("All market price rows cleared. Upload a fresh CSV from /market data source.", "success")
    else:
        flash("Could not clear rows.", "error")
    return redirect(url_for("admin_market"))


@app.route("/admin/market/upload", methods=["POST"])
@admin_required
def admin_market_upload():
    """
    Upload a CSV from Agmarknet, save it to data/datasets/market_prices/kerala_prices.csv,
    then run the existing importer script.
    """
    import subprocess
    import shutil

    if "csv_file" not in request.files:
        flash("No file uploaded.", "error")
        return redirect(url_for("admin_market"))

    f = request.files["csv_file"]
    if not f.filename.lower().endswith(".csv"):
        flash("Please upload a .csv file.", "error")
        return redirect(url_for("admin_market"))

    # Save to the same path the importer expects
    csv_dir = os.path.join(BASE_DIR, 'data', 'datasets', 'market_prices')
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = os.path.join(csv_dir, 'kerala_prices.csv')
    f.save(csv_path)

    # Run the importer as a subprocess
    importer = os.path.join(BASE_DIR, 'backend', 'utils', 'import_agmarknet_csv.py')
    try:
        result = subprocess.run(
            ["python", importer],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            log_admin_action(session["user_id"], "upload_market_csv",
                             "market_price", None, f"file={f.filename}")
            flash("CSV uploaded and imported successfully!", "success")
        else:
            flash(f"Import failed. See server log.", "error")
            print("=== IMPORTER STDERR ===")
            print(result.stderr)
    except Exception as e:
        flash(f"Could not run importer: {e}", "error")

    return redirect(url_for("admin_market"))


@app.route("/weather")
@login_required
def weather_page():
    """Render the weather page — GPS auto-detect handles the rest."""
    return render_template("weather.html")

@app.route("/weather/my-location")
@login_required
def weather_my_location():
    """
    JSON endpoint for the browser to call with GPS coordinates.
    Usage: /weather/my-location?lat=9.59&lon=76.52
    """
    from flask import jsonify

    lat_raw = request.args.get("lat", "").strip()
    lon_raw = request.args.get("lon", "").strip()

    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid coordinates"}), 400

    # Sanity-check ranges
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "Coordinates out of range"}), 400

    # Try to reverse-geocode the location name using Open-Meteo's geocoder
    location_name = f"{lat:.3f}, {lon:.3f}"
    try:
        import requests as _rq
        rev = _rq.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": f"{lat},{lon}", "count": 1, "language": "en", "format": "json"},
            timeout=6,
        )
        # Open-Meteo doesn't reverse-geocode; fallback to nearest-name search via
        # a simple reverse lookup using bigdatacloud free endpoint
        if rev.status_code == 200:
            pass  # keep the default lat,lon label
    except Exception:
        pass

    # Best-effort friendly name
    try:
        import requests as _rq
        r2 = _rq.get(
            "https://api.bigdatacloud.net/data/reverse-geocode-client",
            params={"latitude": lat, "longitude": lon, "localityLanguage": "en"},
            timeout=6,
        )
        if r2.status_code == 200:
            d = r2.json()
            city = d.get("city") or d.get("locality") or d.get("principalSubdivision")
            state = d.get("principalSubdivision")
            country = d.get("countryName")
            parts = [p for p in [city, state, country] if p]
            if parts:
                location_name = ", ".join(parts)
    except Exception as e:
        print(f"⚠️ reverse-geocode skipped: {e}")

    weather = fetch_weather(lat, lon, location_name=location_name)
    if not weather:
        return jsonify({"error": "Could not fetch weather"}), 502

    return jsonify(weather)   

# ============================================================
# Routes: Crop Details (AI-powered)
# ============================================================
@app.route("/crops")
@login_required
def crops_list_page():
    """List all 20 crops with search + category filter."""
    crops = get_all_crops_with_details_flag()
    search = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "").strip()

    if search:
        crops = [c for c in crops if search in (c["name"] or "").lower()]
    if category:
        crops = [c for c in crops if (c["category"] or "") == category]

    categories = sorted({c["category"] for c in get_all_crops_with_details_flag() if c.get("category")})

    return render_template(
        "crops_list.html",
        crops=crops,
        search=search,
        selected_category=category,
        categories=categories,
    )


@app.route("/crops/<int:crop_id>")
@login_required
def crop_detail_page(crop_id):
    """Show crop details. Generates with AI on first visit."""
    crop = get_crop_by_id_admin(crop_id)
    if not crop:
        flash("Crop not found.", "error")
        return redirect(url_for("crops_list_page"))

    # Try cache first
    details = get_crop_details(crop_id)

    # Cache miss — generate with AI
    if not details:
        print(f"🤖 Generating crop details for {crop['name']} (first visit)...")
        details = generate_crop_details(
            crop_name=crop["name"],
            category=crop.get("category") or "General",
            season_type=crop.get("season_type") or crop.get("growing_season") or "Kharif",
        )
        if details:
            save_crop_details(crop_id, details, generated_by="ai")
        else:
            flash("Could not generate crop details. Please try again.", "error")

    return render_template(
        "crop_detail.html",
        crop=crop,
        d=details or {},
    )


@app.route("/crops/<int:crop_id>/regenerate", methods=["POST"])
@admin_required
def crop_detail_regenerate(crop_id):
    """Admin: force regenerate the AI details."""
    crop = get_crop_by_id_admin(crop_id)
    if not crop:
        flash("Crop not found.", "error")
        return redirect(url_for("crops_list_page"))

    delete_crop_details(crop_id)
    details = generate_crop_details(
        crop_name=crop["name"],
        category=crop.get("category") or "General",
        season_type=crop.get("season_type") or crop.get("growing_season") or "Kharif",
    )
    if details:
        save_crop_details(crop_id, details, generated_by="ai")
        log_admin_action(session["user_id"], "regenerate_crop_details",
                         "crop", crop_id, crop["name"])
        flash(f"Regenerated details for {crop['name']}.", "success")
    else:
        flash("Could not regenerate details.", "error")

    return redirect(url_for("crop_detail_page", crop_id=crop_id))

# ============================================================
# Routes: Agriculture Stores
# ============================================================
@app.route("/stores")
@login_required
def stores_page():
    district = request.args.get("district", "").strip() or None
    store_type = request.args.get("type", "").strip() or None

    stores = get_stores(district=district, store_type=store_type)
    districts = get_store_districts()

    return render_template(
        "stores.html",
        stores=stores,
        districts=districts,
        selected_district=district or "",
        selected_type=store_type or "",
    )


@app.route("/stores/<int:store_id>")
@login_required
def store_detail_page(store_id):
    store = get_store_by_id(store_id)
    if not store:
        flash("Store not found.", "error")
        return redirect(url_for("stores_page"))
    return render_template("store_detail.html", store=store)


# ============================================================
# Routes: Learning Hub
# ============================================================
@app.route("/learning")
@login_required
def learning_hub_page():
    category = request.args.get("category", "").strip() or None
    articles = get_learning_articles(category=category)
    categories = get_learning_categories()
    return render_template(
        "learning_hub.html",
        articles=articles,
        categories=categories,
        selected_category=category or "",
    )


@app.route("/learning/article/<int:article_id>")
@login_required
def learning_article_page(article_id):
    article = get_learning_article(article_id)
    if not article:
        flash("Article not found.", "error")
        return redirect(url_for("learning_hub_page"))
    return render_template("learning_article.html", article=article)


@app.route("/learning/search", methods=["POST"])
@login_required
def learning_search():
    """AJAX: search existing articles + generate AI article if none match."""
    from flask import jsonify

    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    language = (data.get("language") or "").strip().lower()
    if language not in ("en", "ml"):
        language = session.get("preferred_language", "en")

    # Search curated DB first
    matches = search_learning_articles(query, limit=10)
    if matches:
        return jsonify({
            "source": "curated",
            "articles": [
                {
                    "id": a["id"],
                    "title": a["title_ml"] if language == "ml" and a.get("title_ml") else a["title_en"],
                    "summary": a["summary_ml"] if language == "ml" and a.get("summary_ml") else a.get("summary_en", ""),
                    "category": a.get("category"),
                    "read_minutes": a.get("read_minutes", 4),
                }
                for a in matches
            ],
        })

    # No match — generate AI article on the fly (not saved)
    ai_article = generate_learning_topic(query, language=language)
    if ai_article:
        return jsonify({
            "source": "ai",
            "articles": [{
                "id": None,
                "title": ai_article.get("title"),
                "summary": ai_article.get("summary"),
                "content": ai_article.get("content"),
                "category": ai_article.get("category"),
                "tags": ai_article.get("tags"),
                "read_minutes": ai_article.get("read_minutes", 4),
            }],
        })

    return jsonify({"source": "none", "articles": []})
      
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)