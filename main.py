from utils import hit_callback,download_file_from_url,extract_and_organize_zip, rename_file, convert_to_underscores, find_number_after_pattern,convert_to_multiplication,upload_to_vercel_blob,remove_single_char_before_pinned
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
import paddle 
import requests
import numpy as np
import cv2

paddle.utils.run_check()

dotenv.load_dotenv()  # This will automatically look for .env in the current directory
folder_path = './data'
file_name_final = 'data.zip'
MONGO_URI = os.getenv("MONGO_URI")
VERCEL_BLOB_TOKEN = os.getenv("VERCEL_BLOB_TOKEN")



def predict_with_paddleocr(image, ocr, add_top = 0, add_bottom = 0, whole = False):
    width, height = (591, 1280)

    crop_box = (0, height - (250 + add_top), width, height - (160 + add_bottom))  
    bottom_part = image.crop(crop_box)
    bottom_part_array = np.array(bottom_part)

    # Invert colors using OpenCV
    inverted_image = cv2.bitwise_not(bottom_part_array)

    if(whole):
      result = ocr.ocr(asarray(image))
    else:
      result = ocr.ocr(inverted_image)

    try:
        extracted_text = " ".join([line[1][0] for line in result[0]])
    except Exception as e:
        print(e)
        print(result)
        extracted_text = " - "

    cleaned_text = remove_single_char_before_pinned(extracted_text.lower())
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
    db = client["test"]  # Replace 'mydatabase' with your database name

    collection = db["transaction"]  # Replace 'mycollection' with your collection name


    print('delete old files')
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
    print('Download data')
    os.makedirs(folder_path)
    download_file_from_url(url, file_name_final)
    extract_and_organize_zip(file_name_final,folder_path)


    ocr = PaddleOCR(use_angle_cls=True, lang='en', ocr_version='PP-OCRv4', use_space_char=True, use_dilation=True )
    
    print('Prediction')

    for i in os.listdir(folder_path):
        add_top = 0
        add_bottom = 0
        need_checking = False
        if i.lower().endswith(".jpeg") or i.lower().endswith(".jpg") or i.lower().endswith(".png"):
            print(f'predicting : {i}')
            image = Image.open('./data/' + i).convert('L')
            width, height = (591, 1280)
            image = image.resize((width, height))
            result = predict_with_paddleocr(image,ocr)
            # print(result)
            print('checking comment')
            while(('comment' in result[0])):
                add_top += 20
                add_bottom += 15
                result = predict_with_paddleocr(image,ocr, add_top=add_top, add_bottom=add_bottom)
            print('making the crop more accurate')
            if((' ' in result[0]) and ('comment' not in result[0])):
                add_top -= 10
                result = predict_with_paddleocr(image,ocr, add_top=add_top, add_bottom=add_bottom)
            print('Check if only one result')
            if(len(result) == 1):
                result[0] = result[0].replace(' -','')
                result.append('1000')
                need_checking = True
            
            add_top += 60
            add_bottom += 90
            print('check_shoeting')
            check_shoeting = predict_with_paddleocr(image,ocr, add_top=add_top, add_bottom=add_bottom)
            match2 = find_number_after_pattern(check_shoeting[0], ['shoeting.stars', 'shoetingstars.lux', 'shoetingstars.catalog'])
            if(match2):
                word_after2 = match2.group(1)
                final = [result[0], word_after2]
                shoeting_comment = word_after2

            else:
                final = result 
                if not re.search(r'\d', final[1]):
                    result2 = predict_with_paddleocr(image,ocr, whole = True)
                    match = find_number_after_pattern(result2[0], ['shoeting.stars', 'shoetingstars.lux', 'shoetingstars.catalog'])
                    if match:
                        word_after = match.group(1)
                        shoeting_comment = word_after
                    else:
                        word_after = 'giveaway'
                        shoeting_comment = 'None'
                        need_checking = True
                    final = [result[0], word_after]
                else:
                    shoeting_comment = 'None'

            transaction_value = convert_to_multiplication(final[1])
            if(transaction_value >= 10000000):
                need_checking = True

            if('/' in result[1]):
                need_checking = True

            if('.' in result[1]):
                need_checking = True

            if(' ' in result[0]):
                need_checking = True

            if(result[0] == ' '):
                need_checking = True
            
            if final[0] in {'tootimetootime', 'tootimetootime_', 'tootimetootime__', 'tootimetootime___'}:
                user_name_final = "tootimetootime____"
            elif(final[0] == 'faiah_muh79'):
                user_name_final = "falah_muh79"
            else:
                user_name_final = final[0]

            if(shoeting_comment != 'None'):
                need_checking = True

            response_message = {
                'userName' : user_name_final,
                'comment' : result[1],
                'shoetingComment' : shoeting_comment,
                'transactionValue' : transaction_value,
                'checkFlag' : need_checking,
                'imagePath' : i,
                "createdAt": datetime.now(),  # Store the current UTC time
                "campaignName" : campaign_name,
                "isManuallyAdjusted" : False
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
                # print(f"Image uploaded successfully: {result['url']}")
            except Exception as e:
                print(f"Upload failed: {e}")

    hit_callback(campaign_name, "success")





if __name__ == "__main__":
    main()