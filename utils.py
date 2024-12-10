import os
import requests
import json
import zipfile
import shutil
import re
import mimetypes

def download_file_from_url(url, destination_path):
    try:
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            with open(destination_path, "wb") as file:
                # Write the entire content to the file
                file.write(response.content)
            print(f"File downloaded successfully and saved to {destination_path}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def extract_and_organize_zip(zip_path, output_folder):
    """
    Extract files from a ZIP archive and reorganize them into a specified folder.
    
    Args:
    zip_path (str): Path to the ZIP file
    output_folder (str): Path to the destination folder where files will be organized
    
    Returns:
    bool: True if extraction and organization is successful, False otherwise
    """
    try:
        # Create the output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Open the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract all files to a temporary directory
            temp_extract_path = os.path.join(output_folder, 'temp_extract')
            zip_ref.extractall(temp_extract_path)
            
            # Move files from temp directory to the output folder
            for root, _, files in os.walk(temp_extract_path):
                for file in files:
                    # Get the full path of the current file
                    current_file_path = os.path.join(root, file)
                    
                    # Destination path in the output folder
                    dest_path = os.path.join(output_folder, file)
                    
                    # Move the file
                    shutil.copy2(current_file_path, dest_path)
                    os.remove(current_file_path)
            
            # Remove the temporary extraction directory
            shutil.rmtree(temp_extract_path)
        
        return True
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def remove_spaces_between_numbers(s):
    # Replace whitespace between numbers
    s = re.sub(r'(\d)\s+(\d)', r'\1\2', s)
    return s

def convert_to_multiplication(s):
    s = remove_spaces_between_numbers(s)  
    s = s.replace('.', '')  

    try_match = re.search(r"try\s+(\d+(\.\d+)?)", s)
    if try_match:
        # Get the number after "try"
        num_str = try_match.group(1)
    else:
        # Fallback to the first number in the string
        first_match = re.search(r"(\d+(\.\d+)?)", s)
        if first_match:
            num_str = first_match.group(1)
        else:
            # If no numbers and the string is "giveaway", return 0
            if s.strip().lower() == 'giveaway':
                return 0
            else:
                return None  # Or any default value when no number is found

    number = float(num_str)

    if number <= 10:
        multiplier = 1000
        result = number * multiplier  # Multiply integer by 1000
    else:
        multiplier = 1000
        result = number * multiplier  # Multiply decimal by 1000
        
    # Return the formatted result as an integer
    return int(result)

def find_number_after_pattern(input_string, patterns):
    for pattern in patterns:
        regex = rf'\b{re.escape(pattern)}\b\s+([\d.]+)'
        match = re.search(regex, input_string)
        if match:
            return match
    return None

def convert_to_underscores(text):
    # Replace all non-alphanumeric characters with a single underscore
    text = re.sub(r'[^A-Za-z0-9]+', '_', text)
    return text

def rename_file(old_name, new_name):
    """
    Rename a file from old_name to new_name.

    Args:
        old_name (str): The current name of the file.
        new_name (str): The new name for the file.

    Returns:
        None
    """
    try:
        os.rename(old_name, new_name)
        print(f"File renamed from {old_name} to {new_name}")
    except FileNotFoundError:
        print(f"The file {old_name} does not exist.")
    except FileExistsError:
        print(f"A file named {new_name} already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")



def get_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def upload_to_vercel_blob(
    file_path, 
    blob_token, 
    api_version='2023-07-22',
    cache_control_max_age=86400
):
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in allowed_extensions:
        raise ValueError(f"Unsupported file type: {file_ext}")

    filename =  os.path.basename(file_path)

    with open(file_path, 'rb') as file:
        file_content = file.read()

    headers = {
        "access": "public",
        "Authorization": f'Bearer {blob_token}',
        "x-api-version": api_version,
        "x-content-type": get_mime_type(filename),
        "x-cache-control-max-age": str(cache_control_max_age),
        "x-add-random-suffix" : "0"
    }

    upload_url = f'https://blob.vercel-storage.com/{filename}'

    response = requests.put(
        upload_url, 
        headers=headers, 
        data=file_content
    )

    if response.status_code not in {200, 201}:
        raise Exception(f"Upload failed: {response.text}")

    upload_result = response.json()
    return {
        'url': upload_result.get('url'),
        'pathname': upload_result.get('pathname'),
        'downloadUrl': upload_result.get('downloadUrl')
    }

def hit_callback(campaign_name, status):
    url = "https://your-api-endpoint.com/api/live-photo/callback"  # Replace with your actual URL

    payload = {
        "status":status,
        "campaign_name": campaign_name
    }

    headers = {
        "Content-Type": "application/json"  
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Request successful:", response.json())  # Parse the JSON response
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
