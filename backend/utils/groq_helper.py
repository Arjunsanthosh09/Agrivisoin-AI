"""
Groq AI helper for AgriVision AI.
- Crop recommendation narrative
- Farmer chatbot
- Enhanced disease advice
Falls back gracefully if the API is unavailable.
"""
import os
import json
from groq import Groq

from config import Config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not Config.GROQ_API_KEY:
            return None
        _client = Groq(api_key=Config.GROQ_API_KEY)
    return _client


# ============================================================
# A. Crop Recommendation Narrative
# ============================================================
def generate_crop_narrative(location, season, soil_ph, temperature,
                            rainfall, top_crops, language='en'):
    """
    Given the user's farm conditions and the top-5 rule-based crop results,
    ask Groq to write a friendly, personalized advisory paragraph.

    `top_crops` is a list of dicts with at least: name, score, risk, expected_profit
    Returns a string (English or Malayalam) or None on failure.
    """
    client = _get_client()
    if client is None:
        return None

    # Build a compact summary to send to the LLM
    crop_summary = "\n".join([
        f"- {c['name']}: suitability {c['score']}%, "
        f"disease risk {c['risk']}, expected profit ₹{c['expected_profit']}"
        for c in top_crops
    ])

    # ---- Language instruction ----
    if language == 'ml':
        lang_instruction = (
            "Reply ONLY in Malayalam (മലയാളം script). "
            "Do not use English words except for product names or scientific terms."
        )
    else:
        lang_instruction = "Reply ONLY in English."

    prompt = f"""You are an experienced agricultural advisor in India.

A farmer in {location} is planning their {season} season crop.
Their farm conditions:
- Soil pH: {soil_ph}
- Average temperature: {temperature}°C
- Average rainfall: {rainfall} mm

Our crop scoring system ranked these crops highest:
{crop_summary}

Write a short, friendly advisory (3-4 sentences) for the farmer:
1. Recommend the top 1-2 crops and explain why they suit their conditions.
2. Mention any seasonal or disease-risk caution.
3. End with one practical tip.

Keep it simple, no jargon. {lang_instruction}
Do NOT include bullet points or markdown. Just plain sentences."""

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful agricultural advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq narrative error: {e}")
        return None


# ============================================================
# B. Farmer Chatbot
# ============================================================
def answer_farmer_query(user_message, context=None, language='en'):
    """
    Answer a farmer's natural-language farming question.
    """
    client = _get_client()
    if client is None:
        return (
            "AI assistant is currently unavailable. Please try again later."
            if language == 'en'
            else "AI സഹായി ഇപ്പോൾ ലഭ്യമല്ല. അൽപ്പസമയത്തിന് ശേഷം വീണ്ടും ശ്രമിക്കുക."
        )

    # ---- VERY explicit language rules ----
    if language == 'ml':
        system_prompt = (
            "നിങ്ങൾ AgriVision AI ആണ് — ഇന്ത്യൻ കർഷകർക്കുള്ള ഒരു കാർഷിക സഹായി.\n"
            "IMPORTANT: You MUST respond ENTIRELY in Malayalam (മലയാളം script). "
            "Every word, every sentence must be in Malayalam. "
            "Do NOT use English sentences. Only common technical product names "
            "(like 'Mancozeb', 'copper oxychloride') can appear in English.\n"
            "Keep advice short, practical, and farmer-friendly.\n"
            "ഉദാഹരണം (example): 'തക്കാളിയിൽ വൈകി വരുന്ന വാട്ടം ബാധിച്ചാൽ, "
            "രോഗബാധിതമായ ഇലകൾ ഉടനടി നീക്കം ചെയ്ത് കത്തിക്കുക. "
            "കോപ്പർ ഓക്സിക്ലോറൈഡ് 2 ഗ്രാം ഒരു ലിറ്റർ വെള്ളത്തിൽ കലക്കി "
            "ആഴ്ചതോറും സ്പ്രേ ചെയ്യുക.'"
        )
    else:
        system_prompt = (
            "You are AgriVision AI, a helpful agricultural assistant for Indian farmers. "
            "Give concise, practical advice. Avoid jargon. "
            "If unsure, suggest consulting a local agricultural officer. "
            "Reply ONLY in English."
        )

    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.append({
            "role": "system",
            "content": f"Context: {json.dumps(context)}"
        })

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=800,
        )
        reply = response.choices[0].message.content.strip()

        # ---- Post-check: if we asked for ML but got mostly English, translate ----
        if language == 'ml' and reply and _is_mostly_english(reply):
            reply = _force_translate_to_malayalam(client, reply)

        return reply
    except Exception as e:
        print(f"⚠️ Groq chat error: {e}")
        return (
            "Sorry, I couldn't process that right now. Please try again in a moment."
            if language == 'en'
            else "ക്ഷമിക്കണം, ഇപ്പോൾ അത് പ്രോസസ്സ് ചെയ്യാൻ കഴിഞ്ഞില്ല. അൽപ്പസമയത്തിന് ശേഷം വീണ്ടും ശ്രമിക്കുക."
        )


def _is_mostly_english(text):
    """Return True if the text is mostly ASCII (i.e., no Malayalam script)."""
    if not text:
        return False
    # Malayalam Unicode range: U+0D00 to U+0D7F
    malayalam_chars = sum(1 for ch in text if '\u0D00' <= ch <= '\u0D7F')
    return malayalam_chars < 5   # fewer than 5 Malayalam chars → treat as English


def _force_translate_to_malayalam(client, english_text):
    """Second pass: ask the model to translate the English reply to Malayalam."""
    try:
        r = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content":
                    "You are a translator. Translate the user's text into Malayalam "
                    "(മലയാളം script). Output ONLY the Malayalam translation. "
                    "Keep product names like 'Mancozeb' in English."},
                {"role": "user", "content": english_text}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Translation fallback failed: {e}")
        return english_text

# ============================================================
# C. Enhanced Disease Explanation (optional)
# ============================================================
def enhance_disease_advice(crop, disease, symptoms, language='en'):
    """
    Generate extra, India-specific treatment advice for a detected disease.
    """
    client = _get_client()
    if client is None:
        return None

    if language == 'ml':
        lang_instruction = (
            "Reply ONLY in Malayalam (മലയാളം script). "
            "Do not use English words except for product names or scientific terms."
        )
    else:
        lang_instruction = "Reply ONLY in English."

    prompt = f"""A farmer's crop has been diagnosed with:
- Crop: {crop}
- Disease: {disease}
- Symptoms: {symptoms}

Give 2-3 specific, practical treatment steps that a small-scale Indian farmer
can take this week. Mention commonly available products (organic preferred).
Keep it under 100 words. {lang_instruction}"""

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq disease advice error: {e}")
        return None
    
# ============================================================
# D. AI Government Scheme Search
# ============================================================
def search_government_schemes(query, user_context=None, language='en'):
    """
    Ask Groq to suggest relevant Indian government agricultural schemes
    based on the user's natural-language query.

    Returns a list of dicts (may be empty on failure).
    Each dict: scheme_name, scheme_type, description,
               eligibility_criteria, benefits, state, category
    """
    client = _get_client()
    if client is None:
        return []

    # ---- Language instruction ----
    if language == 'ml':
        lang_instruction = (
            "Write descriptions and benefits in Malayalam (മലയാളം script). "
            "Keep official scheme names in English (as they appear on government sites)."
        )
    else:
        lang_instruction = "Write everything in English."

    context_str = ""
    if user_context:
        parts = []
        if user_context.get("location"):
            parts.append(f"farmer is in {user_context['location']}")
        if user_context.get("farming_experience") is not None:
            parts.append(f"has {user_context['farming_experience']} years experience")
        if parts:
            context_str = "\nUser context: " + ", ".join(parts) + "."

    prompt = f"""You are an expert on Indian government agricultural schemes.

User's query: "{query}"{context_str}

Suggest up to 5 RELEVANT and REAL government agricultural schemes for Indian farmers
that match this query. Prefer schemes from the central government and Kerala state.

For each scheme, provide these exact keys:
- "scheme_name": official name (string)
- "scheme_type": short category like "Subsidy", "Insurance", "Credit" (string)
- "description": 1-2 sentence summary (string)
- "eligibility_criteria": 1-2 sentence who can apply (string)
- "benefits": 1-2 sentence what the farmer gets (string)
- "state": "All India" or a specific state (string)
- "category": one of "Financial", "Insurance", "Credit", "Irrigation", "Marketing", "Organic", "Welfare", "Development" (string)

RULES:
- Output MUST be a valid JSON array of objects.
- Only include schemes that actually exist in India.
- Do not invent scheme names.
- Do NOT wrap output in markdown fences.
- {lang_instruction}"""

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a JSON API. You return only valid JSON arrays."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if the model ignored instructions
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        schemes = json.loads(raw)
        if isinstance(schemes, list):
            # Keep only entries with a scheme_name
            schemes = [s for s in schemes if isinstance(s, dict) and s.get("scheme_name")]
            return schemes[:5]
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️ Scheme JSON parse error: {e}")
        return []
    except Exception as e:
        print(f"⚠️ Scheme search error: {e}")
        return []
    

# ============================================================
# E. Market Price Insight
# ============================================================
def generate_market_insight(price_summary, language='en'):
    """
    Ask Groq to write a 2-3 sentence market insight for a farmer
    based on the crop price summary.
    """
    client = _get_client()
    if client is None:
        return None

    # Compact summary of the data
    top_gainers = sorted(
        [c for c in price_summary if c['change_pct'] > 0],
        key=lambda x: x['change_pct'], reverse=True
    )[:3]
    top_losers = sorted(
        [c for c in price_summary if c['change_pct'] < 0],
        key=lambda x: x['change_pct']
    )[:3]

    gain_str = ", ".join(
        [f"{c['crop_name']} (+{c['change_pct']}% → ₹{c['current_price']}/kg)" for c in top_gainers]
    ) or "None"
    loss_str = ", ".join(
        [f"{c['crop_name']} ({c['change_pct']}% → ₹{c['current_price']}/kg)" for c in top_losers]
    ) or "None"

    if language == 'ml':
        lang_instruction = (
            "Reply ONLY in Malayalam (മലയാളം script). "
            "Keep crop names in English."
        )
    else:
        lang_instruction = "Reply ONLY in English."

    prompt = f"""You are a market analyst advising Indian farmers.

Current price data (vs. 5-month average):
Top gainers: {gain_str}
Top losers: {loss_str}

Write a 3-sentence market insight for a farmer:
1. Which 1-2 crops are worth selling now (price up).
2. Which crops to hold if possible (price down).
3. One practical tip about timing or storage.

Keep it simple and farmer-friendly. {lang_instruction}"""

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a market analyst for farmers."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq market insight error: {e}")
        return None


# ============================================================
# F. Disease Risk Alert
# ============================================================
def generate_disease_risk_alert(location, crop, temp, humidity, rainfall,
                               top_risks, language='en'):
    """
    Write a 3-4 sentence preventive advisory + a 7-day action plan.
    top_risks: list of dicts {display_name, score, level}
    """
    client = _get_client()
    if client is None:
        return None, None

    if language == 'ml':
        lang_instr = (
            "Reply ONLY in Malayalam (മലയാളം script). "
            "Keep product names in English. Use a warm, practical tone."
        )
    else:
        lang_instr = "Reply in English. Use a warm, practical tone."

    risk_lines = "\n".join([
        f"- {r['display_name']}: {r['level']} risk ({r['score']}%)"
        for r in top_risks[:5]
    ])

    crop_str = crop if crop else "mixed crops"

    advisory_prompt = f"""You are an agricultural advisor in India.

Farmer's location: {location}
Crop: {crop_str}
Current weather: {temp}°C, {humidity}% humidity, {rainfall}mm rainfall

Our system flagged these disease risks:
{risk_lines}

Write a short preventive advisory (3-4 sentences):
1. State the single highest risk by name and why the weather favors it.
2. Give 1-2 immediate preventive actions (organic preferred).
3. End with what to monitor this week.

{lang_instr}
Do NOT use bullet points or markdown. Just plain sentences."""

    plan_prompt = f"""Based on these disease risks for a {crop_str} farm in {location}:
{risk_lines}

Weather: {temp}°C, {humidity}% humidity, {rainfall}mm rain.

Write a simple 7-day preventive action plan. Use this exact JSON format:
[
  {{"day": "Day 1", "action": "..."}},
  {{"day": "Day 2", "action": "..."}},
  {{"day": "Day 3", "action": "..."}},
  {{"day": "Day 4", "action": "..."}},
  {{"day": "Day 5", "action": "..."}},
  {{"day": "Day 6", "action": "..."}},
  {{"day": "Day 7", "action": "..."}}
]

Return ONLY the JSON array. No markdown fences. Each action must be under 15 words.
{lang_instr}"""

    try:
        # Advisory
        r1 = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful agricultural advisor."},
                {"role": "user", "content": advisory_prompt},
            ],
            temperature=0.5, max_tokens=500,
        )
        advisory = r1.choices[0].message.content.strip()

        # 7-day plan
        r2 = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You return only valid JSON."},
                {"role": "user", "content": plan_prompt},
            ],
            temperature=0.4, max_tokens=700,
        )
        raw = r2.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        plan = json.loads(raw)
        if not isinstance(plan, list):
            plan = None

        return advisory, plan
    except Exception as e:
        print(f"⚠️ Groq disease risk error: {e}")
        return None, None
    
# ============================================================
# G. Crop Cultivation Details (AI-generated, cached)
# ============================================================
def generate_crop_details(crop_name, category, season_type):
    """
    Ask Groq to generate comprehensive cultivation details for a crop,
    specific to Kerala. Returns a dict with bilingual (EN + ML) content,
    or None on failure.
    """
    client = _get_client()
    if client is None:
        return None

    prompt = f"""You are a senior agricultural scientist in Kerala, India.

Generate comprehensive cultivation details for **{crop_name}** ({category}, {season_type} crop) for Kerala farmers.

Return ONLY a valid JSON object with these exact keys:
{{
  "season_en": "Which seasons this crop grows in Kerala",
  "season_ml": "Malayalam version",
  "planting_months_en": "Best months to plant (e.g., 'June–July')",
  "planting_months_ml": "Malayalam",
  "soil_en": "Soil type requirements",
  "soil_ml": "Malayalam",
  "ph_range_en": "Ideal pH range (e.g., '6.0 – 7.0')",
  "ph_range_ml": "Malayalam",
  "climate_en": "Temperature and humidity needs",
  "climate_ml": "Malayalam",
  "land_prep_en": "Land preparation steps",
  "land_prep_ml": "Malayalam",
  "seed_rate_en": "Seed rate per acre",
  "seed_rate_ml": "Malayalam",
  "spacing_en": "Plant spacing (row × plant)",
  "spacing_ml": "Malayalam",
  "fertilizer_en": "Fertilizer schedule (NPK, organic)",
  "fertilizer_ml": "Malayalam",
  "irrigation_en": "Irrigation method and frequency",
  "irrigation_ml": "Malayalam",
  "pest_en": "Common pests and control",
  "pest_ml": "Malayalam",
  "disease_en": "Common diseases and management",
  "disease_ml": "Malayalam",
  "harvest_en": "When and how to harvest",
  "harvest_ml": "Malayalam",
  "yield_en": "Expected yield per acre",
  "yield_ml": "Malayalam",
  "storage_en": "Post-harvest storage tips",
  "storage_ml": "Malayalam",
  "tips_en": "2-3 expert tips for Kerala farmers",
  "tips_ml": "Malayalam"
}}

Rules:
- Each value must be 1-3 short sentences.
- Be specific to Kerala's tropical climate and soil.
- Use MALAYALAM SCRIPT (മലയാളം) for all _ml fields.
- Keep technical terms (NPK, kg, urea) in English even in Malayalam fields.
- Do NOT wrap the output in markdown fences.
- Return ONLY the JSON object, no commentary."""

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a JSON API. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2500,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        details = json.loads(raw)
        if isinstance(details, dict) and "season_en" in details:
            return details
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Crop details JSON error: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Crop details error: {e}")
        return None

# ============================================================
# H. Learning Hub AI Helpers
# ============================================================
def generate_learning_topic(topic, language='en'):
    """
    Generate a learning article from a topic query.
    Returns dict {title, summary, content, category, tags, read_minutes} or None.
    """
    client = _get_client()
    if client is None:
        return None

    if language == 'ml':
        lang_instr = (
            "Write the title, summary, and content in Malayalam (മലയാളം script). "
            "Keep technical terms in English."
        )
    else:
        lang_instr = "Write everything in English."

    prompt = f"""You are an agricultural educator writing for Kerala farmers.

Topic: "{topic}"

Write a concise educational article. Return ONLY a valid JSON object:
{{
  "title": "Clear, specific title",
  "summary": "One-sentence summary (under 20 words)",
  "content": "4-6 paragraphs of practical content. Each paragraph 2-4 sentences. Use plain language, no jargon. Include specific numbers (kg/acre, days, temperatures).",
  "category": "One of: Crops, Diseases, Techniques, Schemes, Market",
  "tags": "comma-separated keywords",
  "read_minutes": 4
}}

Rules:
- Content must be practical and specific to Kerala's climate/soil.
- {lang_instr}
- Return ONLY the JSON, no markdown fences.
- Do NOT invent government scheme names or product brands."""

    try:
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a JSON API. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=1500,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        article = json.loads(raw)
        if isinstance(article, dict) and "title" in article and "content" in article:
            return article
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Learning topic JSON error: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Learning topic error: {e}")
        return None


def summarize_learning_article(title, content, language='en'):
    """Generate a short summary for an existing article."""
    client = _get_client()
    if client is None:
        return None

    if language == 'ml':
        lang_instr = "Reply ONLY in Malayalam (മലയാളം script)."
    else:
        lang_instr = "Reply ONLY in English."

    prompt = f"""Summarize this agricultural article for a farmer in 2 sentences.

Title: {title}
Content: {content[:2000]}

{lang_instr}
No bullet points. Just plain sentences."""

    try:
        r = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=200,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Summarize error: {e}")
        return None