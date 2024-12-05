from utils import download_file_from_url,extract_and_organize_zip
import os
import shutil
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR
import re
from numpy import asarray
import gc
from pymongo import MongoClient
from datetime import datetime

link = 'https://8owpateh4dv3qu1o.public.blob.vercel-storage.com/tes_live2.zip'
folder_path = './data'
file_path = 'data.zip'
campaign_name = 'test_google'

MONGO_URI = 'mongodb+srv://shoetingstarsai:ym2CRDS6VfIsAk4m@shoetingstarsai.4bnch.mongodb.net/'

try:
    client = MongoClient(MONGO_URI)  # Adjust URI if necessary
    print("Connected to MongoDB!")
except Exception as  e:
    print(f"Connection failed: {e}")
    exit()
db = client["shoetingstarsai"]  # Replace 'mydatabase' with your database name

# Step 3: Choose the collection
collection = db["results"]  # Replace 'mycollection' with your collection name


def convert_to_multiplication(s):
    s = s.replace(' ', '')  
    
    match = re.search(r"(\d+(\.\d+)?)", s)
    
    if match:
        num_str = match.group(1)  
        number = float(num_str)  
        
        
        if number <= 10:
            multiplier = 1000
            result = number * multiplier  # Multiply integer by 1000
        else:
            multiplier = 1000
            result = number * multiplier  # Multiply decimal by 1000
        
        # Return the formatted result as an integer
        return int(result)
    else:
        return "No valid number found in the string"

def predict_with_paddleocr(image_path, ocr):
    # Open the image
    image = Image.open(image_path)
    width, height = image.size

    # Crop the bottom part of the image
    crop_box = (0, height - 250, width, height - 150)  # Adjust these values as needed
    bottom_part = image.crop(crop_box)

    # Convert to grayscale
    gray_image = bottom_part.convert("L")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(1.2)  # Use a smaller enhancement factor

    # Resize image (downscaling to reduce the OCR load)
    small_image = enhanced_image.resize((enhanced_image.width // 2, enhanced_image.height // 2))

    result = ocr.ocr(asarray(small_image))
    # Extract and format text results
    extracted_text = " ".join([line[1][0] for line in result[0]])
    cleaned_text = re.sub(r'\b[a-zA-Z]\b', '', extracted_text)

    cleaned_text = cleaned_text.lower().replace('pinned', ' - ')
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Strip leading/trailing spaces

    # Print the extracted text
    return cleaned_text.split(' - ')


# Delete the folder itself (if desired)
if os.path.exists(folder_path):

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)  # Delete file
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # Delete sub-folder and its contents

    os.rmdir(folder_path)  # Deletes the folder

# Delete the data.zip file
if os.path.exists(file_path):
    os.remove(file_path)  # Delete the file

os.makedirs(folder_path)
download_file_from_url(link, file_path)
extract_and_organize_zip(file_path,folder_path)

ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False,use_onnx = False)

for i in os.listdir(folder_path):
    if i.lower().endswith(".jpeg"):

        print(f'predicting : {i}')
        result = predict_with_paddleocr('./data/' + i,ocr)
        transaction_value = convert_to_multiplication(result[1])

        response_message = {
            'username' : result[0],
            'comment' : result[1],
            'transaction_value' : transaction_value,
            "created_at": datetime.now(),  # Store the current UTC time
            "campaign_name" : campaign_name
        }

        to_mongo = response_message.copy()
        result = collection.insert_one(to_mongo)
        print(f"Document inserted with ID: {result.inserted_id}")
        gc.collect()

