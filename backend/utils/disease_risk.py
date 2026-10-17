"""
Disease Risk Prediction — rule-based scoring.
Compares current weather (temp, humidity, rainfall) against the
favorable conditions for each plant disease type.
"""

# Favorable weather profiles by pathogen type
WEATHER_RULES = {
    "Fungal": {
        "temp_min": 15, "temp_max": 28,
        "humidity_min": 70,
        "rainfall_min": 5,
        "description": "Fungal spores germinate best in cool-to-moderate temperatures with high humidity.",
    },
    "Bacterial": {
        "temp_min": 22, "temp_max": 32,
        "humidity_min": 65,
        "rainfall_min": 10,
        "description": "Bacteria spread rapidly through warm, wet conditions and rain splash.",
    },
    "Viral": {
        "temp_min": 20, "temp_max": 35,
        "humidity_min": 40,
        "rainfall_min": 0,
        "description": "Viral diseases spread via insect vectors that thrive in warm weather.",
    },
    "None": {
        "temp_min": 999, "temp_max": 999,
        "humidity_min": 999,
        "rainfall_min": 999,
        "description": "Healthy plant — no disease risk.",
    },
}

# Extra boost for diseases known to love specific extreme conditions
BOOST_KEYWORDS = {
    "late blight": {"min_humidity": 85, "boost": 15},
    "downy mildew": {"min_humidity": 85, "boost": 15},
    "rust": {"boost": 10},
    "bacterial spot": {"min_rain": 30, "boost": 10},
    "greening": {"boost": 20},   # citrus greening — always high if in region
}


def _lookup_boost(disease_name_lower):
    for key, rule in BOOST_KEYWORDS.items():
        if key in disease_name_lower:
            return rule
    return None


def score_disease_risk(disease_info, temp, humidity, rainfall):
    """
    Score a disease's risk (0-100) based on current weather.

    Returns (score, level, reasons_list).
    level is one of: 'Low', 'Medium', 'High', 'Very High', 'None'
    """
    d_type = disease_info.get("type_en", "Fungal")
    d_name_lower = (disease_info.get("display_name_en") or "").lower()

    # Healthy plants have no risk
    if d_type == "None" or "healthy" in d_name_lower:
        return 0, "None", []

    rules = WEATHER_RULES.get(d_type, WEATHER_RULES["Fungal"])
    score = 0
    reasons = []

    # ---- Temperature (max 40) ----
    if rules["temp_min"] <= temp <= rules["temp_max"]:
        score += 40
        reasons.append(f"Temperature {temp:.1f}°C is ideal for {d_type.lower()} pathogens")
    else:
        diff = min(abs(temp - rules["temp_min"]), abs(temp - rules["temp_max"]))
        t_score = max(0, 40 - diff * 3)
        score += t_score

    # ---- Humidity (max 35) ----
    if humidity >= rules["humidity_min"]:
        score += 35
        reasons.append(f"Humidity {humidity:.0f}% promotes spore germination")
    else:
        diff = rules["humidity_min"] - humidity
        h_score = max(0, 35 - diff)
        score += h_score

    # ---- Rainfall (max 25) ----
    if rainfall >= rules["rainfall_min"]:
        score += 25
        if rainfall > 0:
            reasons.append(f"Rainfall {rainfall:.0f}mm causes leaf wetness")
    else:
        r_score = max(0, 25 - (rules["rainfall_min"] - rainfall) * 2)
        score += r_score

    # ---- Disease-specific boost ----
    boost_rule = _lookup_boost(d_name_lower)
    if boost_rule:
        if "min_humidity" in boost_rule and humidity >= boost_rule["min_humidity"]:
            score += boost_rule["boost"]
            reasons.append(f"Extended humid period favors {disease_info.get('display_name_en')}")
        elif "min_rain" in boost_rule and rainfall >= boost_rule["min_rain"]:
            score += boost_rule["boost"]
            reasons.append(f"Heavy rain splash accelerates spread")
        elif "boost" in boost_rule and boost_rule.get("min_humidity") is None and boost_rule.get("min_rain") is None:
            score += boost_rule["boost"]

    score = min(100, round(score, 1))

    # ---- Categorize ----
    if score >= 80:
        level = "Very High"
    elif score >= 60:
        level = "High"
    elif score >= 40:
        level = "Medium"
    else:
        level = "Low"

    return score, level, reasons


def predict_top_risks(disease_info_map, temp, humidity, rainfall,
                     crop_filter=None, top_n=8):
    """
    Iterate over all diseases in disease_info.json, score each,
    and return the top N by risk.

    crop_filter: optional string like 'Tomato' to restrict to one crop.
    """
    results = []
    for class_name, info in disease_info_map.items():
        crop = info.get("crop_en", "")
        if crop_filter and crop_filter.lower() not in crop.lower():
            continue

        score, level, reasons = score_disease_risk(info, temp, humidity, rainfall)
        if score <= 0:
            continue

        results.append({
            "class_name": class_name,
            "display_name": info.get("display_name_en", class_name),
            "crop": crop,
            "type": info.get("type_en", "—"),
            "score": score,
            "level": level,
            "reasons": reasons,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]