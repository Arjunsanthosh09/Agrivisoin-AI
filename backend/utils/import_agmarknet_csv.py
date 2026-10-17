"""
Import Agmarknet "Marketwise Price & Arrival Report" CSV into market_prices table.

Handles this format:
  Commodity Group, Commodity, MSP (Rs./Quintal) 2026-27,
  Price on 13 Oct, 2026, Price on 12 Oct, 2026, Price on 11 Oct, 2026,
  Arrival on 13 Oct, 2026, ...

Usage: python backend/utils/import_agmarknet_csv.py
"""
import csv
import os
import re
import sys
from datetime import datetime, date

# --- Add project root to sys.path so `config` and `database` can be imported ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import mysql.connector
from config import Config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'datasets', 'market_prices', 'kerala_prices.csv')

# ---- Aliases: Agmarknet name (lowercased) → your crops.name (lowercased) ----
CROP_ALIASES = {
    'paddy(common)': 'rice',
    'paddy': 'rice',
    'rice': 'rice',
    'bajra(pearl millet/cumbu)': 'bajra',
    'bajra': 'bajra',
    'jowar(sorghum)': 'jowar',
    'jowar': 'jowar',
    'maize': 'maize',
    'wheat': 'wheat',
    'cotton': 'cotton',
    'groundnut': 'groundnut',
    'mustard': 'mustard',
    'soyabean': 'soybean',
    'soybean': 'soybean',
    'sunflower/sunflower seed': 'sunflower',
    'sunflower': 'sunflower',
    'bengal gram(gram)(whole)': 'gram',
    'gram': 'gram',
    'lentil(masur)(whole)': 'lentil',
    'lentil': 'lentil',
    'onion': 'onion',
    'potato': 'potato',
    'tomato': 'tomato',
    'brinjal': 'brinjal',
    'sugarcane': 'sugarcane',
    'banana': 'banana',
    'mango': 'mango',
    'papaya': 'papaya',
}


def get_db():
    return mysql.connector.connect(
        host=Config.DB_HOST, user=Config.DB_USER,
        password=Config.DB_PASSWORD, database=Config.DB_NAME, port=Config.DB_PORT,
    )


def normalize_crop_name(raw):
    """Lowercase, strip extra spaces, then check alias map."""
    key = re.sub(r'\s+', ' ', (raw or '').strip().lower())
    if key in CROP_ALIASES:
        return CROP_ALIASES[key]
    # Try matching just the part before the first "("
    base = key.split('(')[0].strip()
    if base in CROP_ALIASES:
        return CROP_ALIASES[base]
    return None


def parse_price(val):
    """Convert '2,333.93' or '' or '-' to float Rs./quintal. Returns None on failure."""
    if val is None:
        return None
    s = str(val).strip().replace(',', '')
    if s in ('', '-', 'NA', 'N/A'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def extract_date_from_header(header):
    """'Price on 13 Oct, 2026' → date(2026, 10, 13). Returns None on fail."""
    m = re.search(r'(\d{1,2})\s+(\w{3}),?\s+(\d{4})', header or '')
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", '%d %b %Y').date()
    except ValueError:
        return None


def import_csv():
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found: {CSV_PATH}")
        print("   Place the file there and re-run.")
        return

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Crop name → id map
    cursor.execute("SELECT id, name FROM crops")
    crop_map = {row['name'].lower(): row['id'] for row in cursor.fetchall()}
    print(f"📋 Available crops in DB: {sorted(crop_map.keys())}\n")

    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # --- Skip the first 3 title rows; find the header row ---
    header_idx = None
    for i, row in enumerate(rows):
        if any('Commodity' in (c or '') for c in row):
            header_idx = i
            break

    if header_idx is None:
        print("❌ Could not locate header row. Is this an Agmarknet report?")
        return

    header = rows[header_idx]
    print(f"📄 Header: {header}\n")

    # ---- Identify column indexes ----
    commodity_idx = None
    for i, h in enumerate(header):
        if h.strip().lower() == 'commodity':
            commodity_idx = i
            break

    # Find all "Price on ..." columns and sort them newest → oldest
    price_cols = []  # list of (idx, date)
    for i, h in enumerate(header):
        if h.strip().lower().startswith('price on'):
            d = extract_date_from_header(h)
            if d:
                price_cols.append((i, d))
    price_cols.sort(key=lambda x: x[1], reverse=True)  # newest first

    if commodity_idx is None or not price_cols:
        print("❌ Missing 'Commodity' column or 'Price on ...' columns.")
        return

    print(f"📅 Price columns found (newest first):")
    for idx, d in price_cols:
        print(f"   col {idx}: {d.isoformat()}")
    print()

    # ---- Clear old market data so we start clean ----
    print("🧹 Clearing old market_prices rows...")
    cursor.execute("DELETE FROM market_prices")
    conn.commit()

    inserted = 0
    skipped = 0
    for row in rows[header_idx + 1:]:
        if not row or len(row) <= commodity_idx:
            continue

        raw_commodity = row[commodity_idx].strip()
        if not raw_commodity or raw_commodity.lower() == 'commodity':
            continue

        crop_name = normalize_crop_name(raw_commodity)
        if not crop_name:
            print(f"⏭️  Skipped (no match): {raw_commodity}")
            skipped += 1
            continue

        crop_id = crop_map.get(crop_name)
        if not crop_id:
            print(f"⏭️  Skipped (crop not in DB): {raw_commodity} → {crop_name}")
            skipped += 1
            continue

        # Try each price column (newest first) until we find a valid number
        inserted_this_crop = 0
        for idx, dt in price_cols:
            if idx >= len(row):
                continue
            price_quintal = parse_price(row[idx])
            if price_quintal is None:
                continue

            price_per_kg = round(price_quintal / 100.0, 2)

            try:
                cursor.execute(
                    """INSERT INTO market_prices
                       (crop_id, location, market_name, price_per_kg, date,
                        demand_level, price_trend)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (crop_id, 'Kerala', 'Kerala State Mandi',
                     price_per_kg, dt, 'Medium', 'Stable')
                )
                inserted += 1
                inserted_this_crop += 1
            except Exception as e:
                print(f"⚠️ Insert failed for {raw_commodity} on {dt}: {e}")

        if inserted_this_crop:
            print(f"✅ {raw_commodity} → {crop_name}: {inserted_this_crop} rows")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n📊 Summary:")
    print(f"   Inserted:  {inserted}")
    print(f"   Skipped:   {skipped}")


if __name__ == "__main__":
    import_csv()