day=${1}
month=${2}
monthname=${3}
year=${4}

# stop and delete the VM
instance="consume-ztf-${monthname}${day}"
gcloud compute instances stop ${instance} --zone us-central1-a
gcloud compute instances delete ${instance} --zone us-central1-a --quiet
gcloud logging write troy-manual-ops "VM instance ${instance} has been stopped and deleted." --severity NOTICE

# load the day's alerts into BQ
topic="ztf_${year}${month}${day}_programid1_*"
echo "Loading avro -> BQ for topic ${topic}"
python manual_GCS2BQ.py ${topic}
