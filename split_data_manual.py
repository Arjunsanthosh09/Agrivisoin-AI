import os
import shutil
import random

# ⚠️ UPDATE THESE PATHS
SOURCE_DIR = "path/to/your/extracted/PlantVillage/color" # The folder containing disease subfolders
TRAIN_DIR = "dataset/train"
VAL_DIR = "dataset/val"
SPLIT_RATIO = 0.8  # 80% train, 20% validation

# Create destination folders
os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(VAL_DIR, exist_ok=True)

# Get all disease class folders
classes = [d for d in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, d))]
print(f"Found {len(classes)} disease classes.")

for cls in classes:
    cls_path = os.path.join(SOURCE_DIR, cls)
    images = os.listdir(cls_path)
    random.shuffle(images) # Shuffle to ensure random split
    
    split_index = int(len(images) * SPLIT_RATIO)
    train_images = images[:split_index]
    val_images = images[split_index:]
    
    # Create class subfolders in train and val
    os.makedirs(os.path.join(TRAIN_DIR, cls), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, cls), exist_ok=True)
    
    # Copy images
    for img in train_images:
        shutil.copy(os.path.join(cls_path, img), os.path.join(TRAIN_DIR, cls, img))
    for img in val_images:
        shutil.copy(os.path.join(cls_path, img), os.path.join(VAL_DIR, cls, img))
        
    print(f"Processed {cls}: {len(train_images)} train, {len(val_images)} val")

print("✅ Dataset splitting complete! Check the 'dataset' folder.")