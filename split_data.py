import splitfolders

# ⚠️ UPDATE THIS PATH: Point this to your extracted PlantVillage folder
# If your extracted folder has a 'color' subfolder, point it to that one.
# Example: 'C:/Users/YourName/Downloads/PlantVillage/color'
input_folder = "path/to/your/extracted/PlantVillage/color" 

# This will create a 'dataset' folder with 'train' and 'val' inside
output_folder = "dataset"

# Split ratio: 80% training, 20% validation
splitfolders.ratio(input_folder, output=output_folder, seed=1337, ratio=(.8, .2))

print("✅ Dataset successfully split into train and val folders!")