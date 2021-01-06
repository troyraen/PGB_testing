#! /bin/bash
# Creates the GCP VM instances needed by the broker

bucket=$1
CEserviceaccount=$2

#--- Create and configure the Kafka Consumer VM
instancename=ztf-consumer
installscript="gs://${bucket}/consumer/vm_install.sh"
startupscript="gs://${bucket}/consumer/vm_startup.sh"
machinetype=e2-standard-2
zone=us-central1-a
# create the instance
gcloud compute instances create ${instancename} \
    --zone=${zone} \
    --machine-type=${machinetype} \
    --service-account=${CEserviceaccount} \
    --scopes=cloud-platform \
    --metadata=google-logging-enabled=true,startup-script-url=${installscript} \
    --tags=kafka-server # for the firewall rule
# give the vm time to start the install before switching the script
sleep 2m
# set the startup script
gcloud compute instances add-metadata ${instancename} --zone ${zone} \
    --metadata startup-script-url=${startupscript}

#--- Create and configure the Night Conductor VM
instancename=night-conductor
installscript="gs://${bucket}/night_conductor/vm_install.sh"
startupscript="gs://${bucket}/night_conductor/vm_startup.sh"
machinetype=e2-standard-2
gcloud compute instances create ${instancename} \
    --zone=${zone} \
    --machine-type=${machinetype} \
    --service-account=${CEserviceaccount} \
    --scopes=cloud-platform \
    --metadata=google-logging-enabled=true,startup-script-url=${installscript}
# give the vm time to start the install before switching the script
sleep 2m
# set the startup script
gcloud compute instances add-metadata ${instancename} --zone ${zone} \
    --metadata startup-script-url=${startupscript}
