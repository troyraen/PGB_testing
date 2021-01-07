# Broker Architecture
<!-- fs -->
In short:

There are 4 main components:
- The __consumer__ ingests the ZTF Kafka stream and republishes it as a Pub/Sub stream.
- The __data storage__ (x2) and __processing__ (x1) components ingest the consumer's Pub/Sub stream and proceed with their function. These components store their output data to Cloud Storage and/or BigQuery, and publish it to a dedicated Pub/Sub topic/stream.

In addition, there is a "__night conductor__" (running on a VM) that
orchestrates the broker, starting and stoping resources/jobs
on a daily schedule.
Some of it's functions still need to be triggered manually.

Details:

1. __ZTF Alert Stream Consumer__ (ZTF Alert: Kafka -> Pub/Sub)
    - __Compute Engine VM:__  [`ztf-consumer`](https://console.cloud.google.com/compute/instancesMonitoringDetail/zones/us-central1-a/instances/ztf-consumer?project=ardent-cycling-243415&tab=monitoring&duration=PT1H)
    - __Running__  Kafka Connect [`CloudPubSubConnector`](https://github.com/GoogleCloudPlatform/pubsub/tree/master/kafka-connector)
    - __Publishes to__ Pub/Sub topic:  [`ztf_alert_data`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_alert_data?project=ardent-cycling-243415)

2. __Avro File Storage__ (ZTF Alert -> Fix Schema -> GCS bucket)
    - __Cloud Function:__
 [`upload_ztf_bytes_to_bucket`](https://console.cloud.google.com/functions/details/us-central1/upload_ztf_bytes_to_bucket?project=ardent-cycling-243415&pageState=(%22functionsDetailsCharts%22:(%22groupValue%22:%22P1D%22,%22customValue%22:null)))
    - __Listens to__ PS topic: [`ztf_alert_data`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_alert_data?project=ardent-cycling-243415)
    - __Stores in__ GCS bucket: [`ztf_alert_avro_bucket`](https://console.cloud.google.com/storage/browser/ardent-cycling-243415_ztf_alert_avro_bucket;tab=objects?forceOnBucketsSortingFiltering=false&project=ardent-cycling-243415&prefix=&forceOnObjectsSortingFiltering=false)
    - __GCS bucket triggers__ Pub/Sub topic: [`ztf_alert_avro_bucket`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_alert_avro_bucket?project=ardent-cycling-243415)

3. __BigQuery Database Storage__ (ZTF Alert -> BigQuery)
    - __Dataflow job:__ [`production-ztf-ps-bq`](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
    - __Listens to__ PS topic: [`ztf_alert_data`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_alert_data?project=ardent-cycling-243415)
    - __Stores in__ BQ table: [`ztf_alerts.alerts`](https://console.cloud.google.com/bigquery?project=ardent-cycling-243415) (ZTF alert data)

4. __Data Processing (value-added products)__ (ZTF Alert -> Extragalactic Transients Filter -> Salt2 Fit)
    - __Dataflow job:__ [`production-ztf-ps-exgal-salt2`](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
    - __Listens to__ PS topic: [`ztf_alert_data`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_alert_data?project=ardent-cycling-243415)
    - __Stores in__ BQ table: [`ztf_alerts.salt2`](https://console.cloud.google.com/bigquery?project=ardent-cycling-243415) (Salt2 fit params)
    - __Stores in__ GCS bucket: [`ztf-sncosmo/salt2/plot_lc`](https://console.cloud.google.com/storage/browser/ardent-cycling-243415_ztf-sncosmo/salt2/plot_lc?pageState=%28%22StorageObjectListTable%22:%28%22f%22:%22%255B%255D%22%29%29&project=ardent-cycling-243415&prefix=&forceOnObjectsSortingFiltering=false) (lightcurve + Salt2 fit, png)
    - __Publishes to__ PS topics:
        - [ `ztf_exgalac_trans`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_exgalac_trans?project=ardent-cycling-243415) (alerts passing `extragalactic transient` filter)
        - [`ztf_salt2`](https://console.cloud.google.com/cloudpubsub/topic/detail/ztf_salt2?project=ardent-cycling-243415) (Salt2 fit params)

5. __Night Conductor__ (orchestrates GCP resources and jobs to run the broker each night)
    - __Compute Engine VM:__  [`night-conductor`](https://console.cloud.google.com/compute/instancesMonitoringDetail/zones/us-central1-a/instances/night-conductor?project=ardent-cycling-243415&tab=monitoring&duration=PT1H&pageState=(%22duration%22:(%22groupValue%22:%22P1D%22)))

<!-- fe Broker Architecture -->

# Setup the Broker for the First Time
<!-- fs -->

1. Setup and configure a new Google Cloud Platform (GCP) project.
    - [Instructions in our current docs](https://pitt-broker.readthedocs.io/en/latest/installation_setup/installation.html). We would need to follow pieces of the "Installation" and "Defining Environmental Variables" sections. Our project is already setup, so leaving out most of the details for now.
    - [ToDo] Update this section.

2. Install GCP tools:
    - [Google Cloud SDK](https://cloud.google.com/sdk/docs/install): Follow the instructions at the link. (This installs `gcloud`, `gsutil` and `bq` command line tools)
    - [Cloud Client Libraries for Python](https://cloud.google.com/python/docs/reference): Each service requires a different library; the ones we need are (I hope) all listed in the `requirements.txt` in this directory. Install them with (e.g., ) `pip install -r requirements.txt`.

3. Clone the repo and run the broker's setup script.
The script will:
    1. Create GCP resources (BigQuery, GCS, Pub/Sub and Logging)
    2. Upload some broker files to a Cloud Storage bucket. The VMs will fetch a new copy of these files before running the relevant process. This provides us with the flexibility to update individual broker processes/components by simply uploading a new version of the relevant file(s) to the bucket, avoiding the need to re-deploy the broker or VM to make an update.
    3. [PrePR] Deploy the cloud function.
    4. Create and configure the Compute Engine instances (`night-conductor` and `ztf-consumer`)

```bash
# If you used a virtual environment to complete the previous setup steps,
# activate it.

# GOOGLE_CLOUD_PROJECT env variable should have been defined/set in step 1.
# Set it now if needed:
export GOOGLE_CLOUD_PROJECT=ardent-cycling-243415
# The Compute Engine VMs (instances) must be assigned to a specific zone.
# We use the same zone for all instances:
export CE_zone=us-central1-a
# CEserviceaccount=591409139500-compute@developer.gserviceaccount.com

# Clone the broker repo
git clone https://github.com/mwvgroup/Pitt-Google-Broker

# Run the broker's setup script
cd Pitt-Google-Broker/setup_broker
# cd deploy2cloud_Aug2020/setup_broker
./setup_broker.sh
```

4. The `ztf-consumer` VM (created in `setup_broker.sh`) requires two auth files to connect to the ZTF stream.
_These must be uploaded manually and stored at the following locations:_
    1. `krb5.conf`, at VM path `/etc/krb5.conf`
    2. `pitt-reader.user.keytab`, at VM path `/home/broker/consumer/pitt-reader.user.keytab`
You can use the `gcloud compute scp` command for this:
```bash
gcloud compute scp \
    /path/to/local/file \
    ztf-consumer:/path/to/vm/file \
    --zone=${CE_zone}
```

<!-- fe Setup the Broker -->

# Run Daily Broker
<!-- fs -->
1. set consumer VM metadata
2. reset the Pub/Sub counters

```bash
# start the night-conductor vm
# then log in to the ztf-consumer vm
# and manually start the connector

cd deploy2cloud_Aug2020/night_conductor/start_night
# ./start_night.sh ${KAFKA_TOPIC}

PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
KAFKA_TOPIC=ztf_20210107_programid1
brokerdir=brokerdir
bucket="${PROJECT_ID}-broker_files"

./reset_ps_counters.sh ${PROJECT_ID}
./start_beam_jobs.sh ${PROJECT_ID} ${brokerdir} ${bucket}
./start_consumer.sh ${KAFKA_TOPIC}

```

- [Storing and retrieving instance metadata](https://cloud.google.com/compute/docs/storing-retrieving-metadata)
    - [Setting custom metadata](https://cloud.google.com/compute/docs/storing-retrieving-metadata#custom)
- [Scheduling compute instances with Cloud Scheduler](https://cloud.google.com/scheduler/docs/start-and-stop-compute-engine-instances-on-a-schedule)

- [ ]  set an instance metadata key with the topic to subscribe to
- [ ]  create/run startup script that
    - [ ]  copies the topic into the `ps-connector.properties` file
    - [ ]  starts the consumer

<!-- fe Run Daily Broker -->
