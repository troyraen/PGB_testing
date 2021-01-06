#! /bin/bash

CEserviceaccount=591409139500-compute@developer.gserviceaccount.com
#--- install GCP python and command line tools


#--- create GCP resources, except VMs
python3 setup_gcp.py
bucket="${PROJECT_ID}-broker_files"

# create VM instances
./create_vms.sh ${bucket} ${CEserviceaccount}
# takes about 5 min to complete; waits for VMs to start up
