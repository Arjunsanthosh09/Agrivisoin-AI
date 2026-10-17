import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODEL_PATH = os.path.join(BASE_DIR, 'backend', 'ml_models', 'disease_detection', 'model_weights.h5')
CLASS_INDICES_PATH = os.path.join(BASE_DIR, 'backend', 'ml_models', 'disease_detection', 'class_indices.json')

# ----------------------------
# Load Model and Class Indices
# ----------------------------
print("Loading model...")
model = load_model(MODEL_PATH)

with open(CLASS_INDICES_PATH, 'r') as f:
    class_indices = json.load(f)

# Invert the dictionary so we can map index -> class name
# e.g., {0: 'Apple___Apple_scab', 1: 'Apple___Black_rot', ...}
idx_to_class = {v: k for k, v in class_indices.items()}

# ----------------------------
# Prediction Function
# ----------------------------
def predict_disease(img_path):
    # 1. Load and preprocess the image
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) # Add batch dimension
    img_array = img_array / 255.0 # Normalize exactly like training

    # 2. Make prediction
    predictions = model.predict(img_array)
    predicted_class_idx = np.argmax(predictions[0])
    confidence = np.max(predictions[0]) * 100

    # 3. Get class name
    predicted_class_name = idx_to_class[predicted_class_idx]

    return predicted_class_name, confidence

# ----------------------------
# Test the script
# ----------------------------
if __name__ == "__main__":
    # CHANGE THIS PATH to an actual image in your dataset to test!
    # For example, pick one from: data/datasets/disease_dataset/color/Tomato___Early_blight/
    test_image_path = os.path.join(BASE_DIR, 'data', 'datasets', 'disease_dataset', 'color', 'Tomato___Early_blight', '0a2726e0-3358-4a46-b6dc-563a5a9f2bdf___RS_Erly.B 7860.JPG')
    
    if os.path.exists(test_image_path):
        print(f"\nTesting image: {test_image_path}")
        disease, conf = predict_disease(test_image_path)
        print(f"\n✅ Prediction: {disease}")
        print(f"✅ Confidence: {conf:.2f}%")
    else:
        print(f"\n❌ Error: Image not found at {test_image_path}")
        print("Please open 'predict.py' and change 'YOUR_IMAGE_NAME.jpg' to an actual image in your dataset.")