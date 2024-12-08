from utils import download_file_from_url,extract_and_organize_zip, rename_file, convert_to_underscores, find_number_after_pattern,convert_to_multiplication,upload_to_vercel_blob
import os
import shutil
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR
import re
from numpy import asarray
from pymongo import MongoClient
from datetime import datetime
import argparse
import dotenv

dotenv.load_dotenv()  # This will automatically look for .env in the current directory
folder_path = './data'
file_name_final = 'data.zip'
MONGO_URI = os.getenv("MONGO_URI")
VERCEL_BLOB_TOKEN = os.getenv("VERCEL_BLOB_TOKEN")

def predict_with_paddleocr(image_path, ocr, add_top = 0, add_bottom = 0, whole = False):
    image = Image.open(image_path)
    width, height = (591, 1280)
    image = image.resize((width, height))

    crop_box = (0, height - (260 + add_top), width, height - (150 + add_bottom))  
    bottom_part = image.crop(crop_box).convert("RGB")

    if(whole):
      result = ocr.ocr(asarray(image))
    else:
      result = ocr.ocr(asarray(bottom_part))

    extracted_text = " ".join([line[1][0] for line in result[0]])
    cleaned_text = re.sub(r'\b[a-zA-Z]\b', '', extracted_text)

    cleaned_text = cleaned_text.lower().replace('pinned', ' - ')
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  
    cleaned_text = cleaned_text.replace(' +','')

    return cleaned_text.split(' - ')


def main():
    # Create the parser

    print('parsing')
    parser = argparse.ArgumentParser(description="Process URL and campaign name.")

    # Add arguments
    parser.add_argument("--url", required=True, help="The URL to process")
    parser.add_argument("--campaign_name", required=True, help="The name of the campaign")

    # Parse arguments
    args = parser.parse_args()

    # Access arguments
    url = args.url
    campaign_name = args.campaign_name

    campaign_name_new = convert_to_underscores(campaign_name)

    print('Connect to mongo')

    try:
        client = MongoClient(MONGO_URI)  # Adjust URI if necessary
        print("Connected to MongoDB!")
    except Exception as  e:
        print(f"Connection failed: {e}")
        exit()
    db = client["shoetingstarsai"]  # Replace 'mydatabase' with your database name

    collection = db["results"]  # Replace 'mycollection' with your collection name

    print('Download data')


    os.makedirs(folder_path)
    download_file_from_url(url, file_name_final)
    extract_and_organize_zip(file_name_final,folder_path)


    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=True,use_onnx = False)

    print('Prediction')

    for i in os.listdir(folder_path):
        add_top = 0
        add_bottom = 0
        need_checking = 0
        if i.lower().endswith(".jpeg") or i.lower().endswith(".jpg") or i.lower().endswith(".png"):
            print(f'predicting : {i}')
            result = predict_with_paddleocr('./data/' + i,ocr)
            # print(result)
            print('checking comment')
            while(('comment' in result[0])):
                add_top += 20
                add_bottom += 15
                result = predict_with_paddleocr('./data/' + i,ocr, add_top=add_top, add_bottom=add_bottom)
            print('making the crop more accurate')
            if((' ' in result[0]) and ('comment' not in result[0])):
                add_top -= 10
                result = predict_with_paddleocr('./data/' + i,ocr, add_top=add_top, add_bottom=add_bottom)
            print('Check if only one result')
            if(len(result) == 1):
                result[0] = result[0].replace(' -','')
                result.append('1000')
                need_checking = 1
            
            add_top += 60
            add_bottom += 90
            print('check_shoeting')
            check_shoeting = predict_with_paddleocr('./data/' + i,ocr, add_top=add_top, add_bottom=add_bottom)
            match2 = find_number_after_pattern(check_shoeting[0], ['shoeting.stars', 'shoetingstars.lux', 'shoetingstars.catalog'])
            if(match2):
                word_after2 = match2.group(1)
                final = [result[0], word_after2]
                shoeting_comment = word_after2
            else:
                final = result 
                if not re.search(r'\d', final[1]):
                    need_checking = 1
                    result2 = predict_with_paddleocr('./data/' + i,ocr, whole = True)
                    match = find_number_after_pattern(result2[0], ['shoeting.stars', 'shoetingstars.lux', 'shoetingstars.catalog'])
                    if match:
                        word_after = match.group(1)
                        shoeting_comment = word_after
                    else:
                        word_after = 'giveaway'
                        shoeting_comment = 'None'
                    final = [result[0], word_after]
                else:
                    shoeting_comment = 'None'

            
            response_message = {
                'user_name' : final[0],
                'comment' : result[1],
                'shoeting_comment' : shoeting_comment,
                'transaction_value' : convert_to_multiplication(final[1]),
                'check_flag' : need_checking,
                'image_path' : i,
                "created_at": datetime.now(),  # Store the current UTC time
                "campaign_name" : campaign_name

            }
            to_mongo = response_message.copy()
            print('inserting to mongo')
            result = collection.insert_one(to_mongo)
            print(f"Document inserted with ID: {result.inserted_id}")
            

    print('upload to vercel')
    for i in os.listdir(folder_path):
        if i.lower().endswith(".jpeg") or i.lower().endswith(".jpg") or i.lower().endswith(".png"):
            # new_file_name = folder_path + '/'  + campaign_name_new + '_' + i
            # rename_file(folder_path + '/' + i, new_file_name)
            try:
                result = upload_to_vercel_blob(
                    file_path=folder_path + '/'  +i,
                    blob_token=VERCEL_BLOB_TOKEN,
                )
                print(f"Image uploaded successfully: {result['url']}")
            except Exception as e:
                print(f"Upload failed: {e}")

    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete file
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Delete sub-folder and its contents

        os.rmdir(folder_path)  # Deletes the folder

    # Delete the data.zip file
    if os.path.exists(file_name_final):
        os.remove(file_name_final)  # Delete the file



if __name__ == "__main__":
    main()