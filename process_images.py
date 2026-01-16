import os
from PIL import Image
import glob

TARGET_SIZE = (1920, 1080)
TARGET_DIR = r"c:\Users\hamcoding\Desktop\codding\public\assets"
SOURCE_ROOT = r"c:\Users\hamcoding\Desktop\codding\전달사진"

def resize_and_crop(img, target_size):
    target_ratio = target_size[0] / target_size[1]
    img_ratio = img.width / img.height

    if img_ratio > target_ratio:
        # Image is wider than target
        new_height = target_size[1]
        new_width = int(new_height * img_ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Crop center
        left = (new_width - target_size[0]) // 2
        img = img.crop((left, 0, left + target_size[0], target_size[1]))
    else:
        # Image is taller than target
        new_width = target_size[0]
        new_height = int(new_width / img_ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Crop center
        top = (new_height - target_size[1]) // 2
        img = img.crop((0, top, target_size[0], top + target_size[1]))
    
    return img

def process_category(source_path, prefix, recursive=True):
    print(f"Processing {prefix} from {source_path}...")
    files = []
    if recursive:
        for root, dirs, filenames in os.walk(source_path):
            for filename in filenames:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    files.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(source_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                files.append(os.path.join(source_path, filename))
    
    files.sort() # Ensure consistent order
    
    for i, file_path in enumerate(files):
        try:
            with Image.open(file_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                processed_img = resize_and_crop(img, TARGET_SIZE)
                
                output_filename = f"{prefix}{i+1}.jpg"
                output_path = os.path.join(TARGET_DIR, output_filename)
                
                processed_img.save(output_path, "JPEG", quality=90)
                print(f"Saved {output_filename}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

# 1. Auditorium (Main)
process_category(os.path.join(SOURCE_ROOT, "본관- 대강당"), "auditorium_real_")

# 2. Medium Conference (Main)
process_category(os.path.join(SOURCE_ROOT, "본관-중회의실"), "medium_conf_real_")

# 3. Video Conference (Main)
process_category(os.path.join(SOURCE_ROOT, "본관-화상회의실"), "video_conf_real_", recursive=False)

print("Processing complete.")
