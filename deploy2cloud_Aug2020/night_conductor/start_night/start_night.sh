#! /bin/bash

KAFKA_TOPIC="$1"
baseurl="http://metadata.google.internal/computeMetadata/v1"
H="Metadata-Flavor: Google"
PROJECT_ID=$(curl "${baseurl}/project/project-id" -H "${H}")
# PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
brokerdir=/home/broker
mkdir -p ${brokerdir}
bucket="${PROJECT_ID}-broker_files"

#--- Reset Pub/Sub counters
./reset_ps_counters.sh ${PROJECT_ID}

#--- Start the Beam/Dataflow jobs
./start_beam_jobs.sh ${brokerdir} ${bucket}

#--- Start the consumer
# Set consumer VM metadata for the day's topic
# for info on working with custom metadata, see here
# https://cloud.google.com/compute/docs/storing-retrieving-metadata#custom
instancename=ztf-consumer
zone=us-central1-a
PS_TOPIC=ztf_alert_data
gcloud compute instances add-metadata ${instancename} --zone=${zone} \
      --metadata KAFKA_TOPIC=${KAFKA_TOPIC},PS_TOPIC=${PS_TOPIC}
# set the startup script
gcloud compute instances add-metadata ${instancename} --zone ${zone} \
  --metadata startup-script-url=${startupscript}
# start the VM
gcloud compute instances start ${instancename} --zone ${zone}
# this launches a startup script that configures and starts the
# Kafka -> Pub/Sub connector
