#! /bin/bash

# GOOGLE_CLOUD_PROJECT should exist as an environment variable
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
# # Set brokerdir as the parent directory of this script's directory
# brokerdir=$(dirname "$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )")
# # https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself

# Create BigQuery, GCS, Pub/Sub and Logging resources
python3 setup_gcp.py

# Upload some broker files to GCS so the VMs can use them
bucket="${PROJECT_ID}-broker_files"
gsutil -m cp -r ../beam gs://${bucket}
gsutil -m cp -r ../consumer gs://${bucket}
gsutil -m cp -r ../night_conductor gs://${bucket}

# Deploy the Cloud Function

# Create VM instances
./create_vms.sh ${bucket}
# takes about 5 min to complete; waits for VMs to start up
