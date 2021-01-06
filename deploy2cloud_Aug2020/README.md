# Setup the Broker

1. installs requirements
2. creates GCP resources [setup-gcp.py] (buckets, PS topics/subs, BQ datasets)
3. sets up the Kafka consumer VM
4.

- [Running startup scripts](https://cloud.google.com/compute/docs/startupscript)

```bash
# virtual env
export GOOGLE_CLOUD_PROJECT=ardent-cycling-243415
export CEserviceaccount=591409139500-compute@developer.gserviceaccount.com
zone=us-central1-a
# clone repo
cd deploy2cloud_Aug2020/setup_broker
./setup_broker.sh
```

This sets up a consumer VM called `ztf-consumer` which will require two auth files to connect to the ZTF stream.
_These must be uploaded manually to the following locations:_
1. `krb5.conf`, which should be at `/etc/krb5.conf`
2. `pitt-reader.user.keytab`, which should be at `/home/ztf_consumer/pitt-reader.user.keytab`
You can use the `gcloud compute scp` command for this:
```bash
gcloud compute scp /path/to/local/file ztf-consumer:/path/to/vm/file --zone=us-central1-a
```


# Run Daily Broker

1. set consumer VM metadata
2. reset the Pub/Sub counters

```bash
# start the night-conductor vm
# then log in to the ztf-consumer vm
# and manually start the connector
KAFKA_TOPIC=ztf_20210105_programid1

cd deploy2cloud_Aug2020/start_night
./start_night.sh ${KAFKA_TOPIC}
```

- [Storing and retrieving instance metadata](https://cloud.google.com/compute/docs/storing-retrieving-metadata)
    - [Setting custom metadata](https://cloud.google.com/compute/docs/storing-retrieving-metadata#custom)
- [Scheduling compute instances with Cloud Scheduler](https://cloud.google.com/scheduler/docs/start-and-stop-compute-engine-instances-on-a-schedule)

- [ ]  set an instance metadata key with the topic to subscribe to
- [ ]  create/run startup script that
    - [ ]  copies the topic into the `ps-connector.properties` file
    - [ ]  starts the consumer

<!-- fe Automate consumer VM start/stop -->
