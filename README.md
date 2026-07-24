<div align="center">

# 🌾 AgriVision AI

**Intelligent Crop Disease Detection and Smart Seasonal Crop Recommendation System**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

[Features](#-features) • [Tech Stack](#-tech-stack) • [Installation](#-installation) • [Usage](#-usage) • [Screenshots](#-screenshots) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Datasets Used](#-datasets-used)
- [Screenshots](#-screenshots)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License](#-license)
- [Team](#-team)
- [Contact](#-contact)
- [Citation](#-citation)

---

## 🌟 Overview

**AgriVision AI** is an intelligent agriculture support system that combines artificial intelligence, machine learning, computer vision, historical agricultural data, and weather analysis to help farmers make better farming decisions. Farmers can capture an image of a crop leaf using a mobile device, detect diseases early, and receive personalized crop recommendations based on multiple parameters.

### 🎯 Key Highlights

- **Early Disease Detection** — 95%+ accuracy in identifying crop diseases
- **Smart Recommendations** — AI-powered crop suggestions based on soil, weather, and market trends
- **Multilingual Support** — Available in 10+ Indian languages
- **Real-time Analysis** — Instant disease diagnosis and treatment suggestions
- **Profit Estimation** — Market-based profitability predictions
- **User-friendly Interface** — Simple, mobile-first design built for farmers

---

## 🚨 Problem Statement

Agriculture is one of the most important sectors of the economy and the primary source of livelihood for millions of farmers. Crop productivity is greatly affected by:

- Plant diseases that are often identified only after visible damage
- Unpredictable weather conditions
- Unsuitable crop selection
- Fluctuating market prices
- A lack of integrated platforms for decision support

AgriVision AI addresses these challenges with a single, comprehensive, data-driven platform.

---

## ✨ Features

### 1. 🔬 AI-Based Disease Detection
- Upload leaf images for instant disease diagnosis
- High-accuracy deep learning model (95%+ accuracy)
- Detailed disease information — name, symptoms, and causes
- Severity and stage prediction

### 2. 🌱 Smart Crop Recommendation
Personalized suggestions based on:
- Soil parameters (pH, NPK values)
- Weather conditions (temperature, rainfall, humidity)
- Seasonal patterns
- Historical crop performance
- Profitability estimation using market trends
- Disease risk prediction for recommended crops

### 3. 🤖 AI Chatbot Assistant
- 24/7 agricultural support
- Instant answers to farming queries
- Multilingual support
- Preventive advisory before disease outbreaks

### 4. 📊 Historical Analysis
- Crop loss analysis
- Yield prediction
- Seasonal crop performance
- Government schemes information

### 5. 🌍 Multilingual Support
English · हिंदी (Hindi) · தமிழ் (Tamil) · తెలుగు (Telugu) · ಕನ್ನಡ (Kannada) · മലയാളം (Malayalam) · मराठी (Marathi) · ગુજરાતી (Gujarati)

---

## 🛠 Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.8+ | Core programming language |
| Flask | 2.3.3 | Web framework |
| MySQL | 8.0 | Database management |
| TensorFlow | 2.13.0 | Deep learning for disease detection |
| scikit-learn | 1.3.0 | Machine learning for recommendations |
| OpenCV | 4.8.0 | Image processing |
| Pandas | 2.0.3 | Data manipulation |
| NumPy | 1.24.3 | Numerical computing |

### Frontend

| Technology | Purpose |
|---|---|
| HTML5 | Structure |
| CSS3 | Styling |
| JavaScript | Interactivity |
| Jinja2 | Templating engine |

### Database
- MySQL for structured data storage
- Optimized indexes for performance
- Transaction support for data integrity

### Authentication & Security
- Werkzeug security (password hashing)
- Session-based authentication
- CSRF protection
- Secure file upload handling

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (HTML/CSS/JavaScript)                     │
└─────────────────────┬──────────────────────────────────────┘
                       │
┌─────────────────────▼──────────────────────────────────────┐
│                    Flask Backend                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Routes (app.py)                    │   │
│  │  • Authentication      • Disease Detection             │   │
│  │  • Crop Recommendations • Chatbot                      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Core Modules (modules/)                │   │
│  │  • disease_detection/  • crop_recommendation/          │   │
│  │  • chatbot/             • utils/                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Database Layer (database/)                │   │
│  │  • db_connection.py    • schema.sql                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬──────────────────────────────────────┘
                       │
┌─────────────────────▼──────────────────────────────────────┐
│                      MySQL Database                          │
│  • Users   • Diseases   • Crops   • Detection History        │
│  • Recommendations   • Chat History   • Government Schemes   │
└───────────────────────────────────────────────────────────────┘
```

### Project Structure

```
AgriVision_AI/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
│
├── static/                         # Static files
│   ├── css/                        # Stylesheets
│   ├── js/                         # JavaScript files
│   ├── images/                     # Images and icons
│   └── uploads/                    # Uploaded leaf images
│
├── templates/                      # HTML templates
│   ├── base.html                   # Base template
│   ├── index.html                  # Homepage
│   ├── disease_detection.html      # Disease detection page
│   ├── crop_recommendation.html    # Crop recommendation page
│   ├── chatbot.html                # AI chatbot interface
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   └── dashboard.html              # User dashboard
│
├── database/                       # Database files
│   ├── __init__.py
│   ├── db_connection.py            # Database operations
│   └── schema.sql                  # Database schema
│
├── modules/                        # Core functionality
│   ├── disease_detection/          # Disease detection module
│   ├── crop_recommendation/        # Crop recommendation module
│   ├── chatbot/                    # Chatbot module
│   └── utils/                      # Utility functions
│
├── ml_models/                      # Trained ML models
├── data/                           # Datasets
├── scripts/                        # Utility scripts
└── README.md                       # Documentation
```

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- Git
- Virtual environment (recommended)

### Step-by-Step Installation

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/AgriVision_AI.git
cd AgriVision_AI
```

**2. Create a virtual environment**
```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure the database**

Update `config.py` with your MySQL credentials:
```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "your_password"  # Change this
DB_NAME = "agrivision_ai"
```

**5. Create the database**
```bash
mysql -u root -p < database/schema.sql
```
Or manually:
```sql
CREATE DATABASE agrivision_ai;
USE agrivision_ai;
-- Run the schema.sql file
```

**6. Initialize database tables**
```bash
python -c "from database.db_connection import initialize_database; initialize_database()"
```

**7. Run the application**
```bash
python app.py
```

The application will be available at **http://127.0.0.1:5000**

### Docker Installation (Optional)
```bash
# Build the image
docker build -t agrivision-ai .

# Run the container
docker run -p 5000:5000 agrivision-ai
```

---

## 🚀 Usage

### 1. User Registration & Login
- Navigate to `http://127.0.0.1:5000/register`
- Create an account with username, email, and password
- Log in at `http://127.0.0.1:5000/login`

### 2. Disease Detection
- Click **Disease Detection** in the navigation
- Upload a leaf image (JPG, PNG, or GIF)
- Click **Detect Disease**
- View results including:
  - Disease name and confidence score
  - Severity level
  - Symptoms and causes
  - Organic and chemical remedies
  - Preventive measures

### 3. Crop Recommendation
- Click **Crop Recommendation**
- Enter soil parameters (pH, NPK values)
- Provide weather information (temperature, rainfall, humidity)
- Select the season (Kharif, Rabi, or Summer)
- View recommended crops with:
  - Suitability score
  - Profit estimate
  - Disease risk level
  - Reasoning for the recommendation

### 4. AI Chatbot
- Click **AI Assistant**
- Type your query in the chat interface
- Select your preferred language
- Receive instant AI-powered responses

### 5. Dashboard
- View your detection history
- Check saved recommendations
- Access personalized insights

---

## 📊 Datasets Used

| Module | Dataset | Source |
|---|---|---|
| Disease Detection | PlantVillage | Kaggle |
| Stage Prediction | Rice Sheath Blight Severity | Mendeley |
| Remedy Knowledge | LeafMD | Hugging Face |
| Crop Recommendation | Crop Recommendation Dataset | Kaggle |
| Seasonal Calendar | ICAR Crop Weather Calendars | ICAR |
| Yield Data | Crop Production Statistics India | GitHub |
| Crop Loss Data | Harvest & Post-Harvest Losses | Dataful |
| Government Schemes | MyScheme India | Kaggle |

---

## 📸 Screenshots

| | |
|---|---|
| **Homepage** ![Homepage](static/images/screenshots/homepage.png) | **Disease Detection** ![Disease Detection](static/images/screenshots/disease_detection.png) |
| **Detection Results** ![Detection Results](static/images/screenshots/detection_result.png) | **Crop Recommendation** ![Crop Recommendation](static/images/screenshots/crop_recommendation.png) |
| **AI Chatbot** ![AI Chatbot](static/images/screenshots/chatbot.png) | **Dashboard** ![Dashboard](static/images/screenshots/dashboard.png) |

> Replace the paths above with the actual location of your screenshots once they're added to the repo.

---

## 🔮 Future Enhancements

- [ ] Mobile application (Android/iOS)
- [ ] Real-time weather API integration
- [ ] IoT device integration for automated monitoring
- [ ] Blockchain-based traceability
- [ ] Voice-based interaction
- [ ] Augmented reality (AR) disease visualization
- [ ] Fertilizer recommendation system
- [ ] Pest detection module
- [ ] Community farming forum
- [ ] Integration with e-commerce platforms

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit your changes
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. Push to the branch
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open a Pull Request

### Contribution Guidelines
- Follow the PEP 8 style guide
- Write meaningful commit messages
- Add documentation for new features
- Include tests for new functionality
- Update the README if needed

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

| Role | Name | GitHub |
|---|---|---|
| Member 1 | Your Name | [@Gowtham-thulasi](https://github.com/Gowtham-thulasi) |

---

## 🙏 Acknowledgments

- PlantVillage dataset contributors
- Kaggle community for datasets
- ICAR for crop calendar data
- All open-source libraries used
- Agricultural experts and farmers for feedback

---

## 📞 Contact

**Project Maintainer:** Your Name

- 📧 Email: your.email@example.com
- 📱 Phone: +91 12345 67890
- 🌐 Website: [agrivision-ai.com](https://agrivision-ai.com)
- 🐦 Twitter: [@agrivision_ai](https://twitter.com/agrivision_ai)

---

## 📖 Citation

If you use this project in your research, please cite:

```bibtex
@software{agrivision_ai_2024,
  author = {Your Name and Team Members},
  title = {AgriVision AI: Intelligent Crop Disease Detection and Smart Seasonal Crop Recommendation System},
  year = {2024},
  url = {https://github.com/yourusername/AgriVision_AI}
}
```

<div align="center">

### 🌟 Made with ❤️ for Farmers 🌟

[⬆ Back to Top](#-agrivision-ai)

</div>
