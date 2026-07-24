CREATE DATABASE IF NOT EXISTS agrivision_ai;
USE agrivision_ai;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    location VARCHAR(100),
    farming_experience INT,
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diseases table
CREATE TABLE IF NOT EXISTS diseases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(100),
    category VARCHAR(50),
    symptoms TEXT,
    causes TEXT,
    affected_crops TEXT,
    prevention_tips TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Disease remedies table
CREATE TABLE IF NOT EXISTS disease_remedies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    disease_id INT,
    remedy_type ENUM('organic', 'chemical', 'preventive', 'cultural'),
    description TEXT,
    application_method TEXT,
    effectiveness_rating FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

-- Crops table
CREATE TABLE IF NOT EXISTS crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    ideal_soil_ph_min FLOAT,
    ideal_soil_ph_max FLOAT,
    ideal_temperature_min FLOAT,
    ideal_temperature_max FLOAT,
    ideal_rainfall_min FLOAT,
    ideal_rainfall_max FLOAT,
    growing_season VARCHAR(100),
    harvest_days INT,
    market_price FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crop susceptibility table (disease risks)
CREATE TABLE IF NOT EXISTS crop_disease_susceptibility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    disease_id INT,
    risk_level ENUM('low', 'medium', 'high', 'very_high'),
    season VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES crops(id),
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

-- Crop weather data
CREATE TABLE IF NOT EXISTS crop_weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    season VARCHAR(50),
    year INT,
    state VARCHAR(100),
    district VARCHAR(100),
    temperature_avg FLOAT,
    rainfall_avg FLOAT,
    humidity_avg FLOAT,
    yield_kg_per_hectare FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES crops(id)
);

-- Crop loss records
CREATE TABLE IF NOT EXISTS crop_loss_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    year INT,
    state VARCHAR(100),
    district VARCHAR(100),
    loss_percentage FLOAT,
    cause VARCHAR(100),
    estimated_loss_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES crops(id)
);

-- Detection history
CREATE TABLE IF NOT EXISTS detection_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    disease_id INT,
    severity VARCHAR(20),
    stage VARCHAR(50),
    confidence FLOAT,
    image_path VARCHAR(255),
    detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (disease_id) REFERENCES diseases(id)
);

-- Recommendation history
CREATE TABLE IF NOT EXISTS recommendation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    crop_id INT,
    location VARCHAR(100),
    season VARCHAR(50),
    suitability_score FLOAT,
    profit_estimate DECIMAL(15,2),
    disease_risk VARCHAR(20),
    recommendation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (crop_id) REFERENCES crops(id)
);

-- Chat history
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    user_message TEXT,
    bot_response TEXT,
    language VARCHAR(10) DEFAULT 'en',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Government schemes
CREATE TABLE IF NOT EXISTS government_schemes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scheme_name VARCHAR(255) NOT NULL,
    scheme_type VARCHAR(100),
    description TEXT,
    eligibility_criteria TEXT,
    benefits TEXT,
    application_deadline DATE,
    state VARCHAR(100),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User preferences (for personalization)
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    preferred_crops TEXT,
    soil_type VARCHAR(50),
    farm_size DECIMAL(10,2),
    irrigation_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX idx_crop_name ON crops(name);
CREATE INDEX idx_disease_name ON diseases(name);
CREATE INDEX idx_detection_date ON detection_history(detection_date);
CREATE INDEX idx_recommendation_date ON recommendation_history(recommendation_date);
CREATE INDEX idx_chat_timestamp ON chat_history(timestamp);