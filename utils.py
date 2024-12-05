import os
import requests
import zipfile
import shutil

def download_file_from_url(url, destination_path):
    try:
        # Send a GET request to the URL
        response = requests.get(url, stream=True)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            with open(destination_path, "wb") as file:
                # Download the file in chunks to handle large files
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
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
                    shutil.move(current_file_path, dest_path)
            
            # Remove the temporary extraction directory
            shutil.rmtree(temp_extract_path)
        
        return True
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
