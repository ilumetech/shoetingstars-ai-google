#!/bin/bash

# Fetch metadata values
URL=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/url" -H "Metadata-Flavor: Google")
CAMPAIGN_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/campaign_name" -H "Metadata-Flavor: Google")

# Path to your Python virtual environment

cd /home/leonardo_ignatius/shoetingstars-ai-google

# Activate the virtual environment
source .venv/bin/activate
# Run the Python script with arguments

echo "running python script"
PYTHON_SCRIPT_PATH="main.py" 
python3 $PYTHON_SCRIPT_PATH --url "$URL" --campaign_name "$CAMPAIGN_NAME" 


# Stop the instance after script execution
INSTANCE_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/name" -H "Metadata-Flavor: Google")
ZONE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/zone" -H "Metadata-Flavor: Google" | awk -F/ '{print $NF}')
PROJECT_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")

gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID
