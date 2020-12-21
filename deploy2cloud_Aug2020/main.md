- [Dashboard `consume-ztf`](https://console.cloud.google.com/monitoring/dashboards/builder/3a371dcb-42d1-4ea0-add8-141d025924f6?project=ardent-cycling-243415&dashboardBuilderState=%257B%2522editModeEnabled%2522:false%257D&timeDomain=1h)
- [VM Instances](https://console.cloud.google.com/compute/instances?project=ardent-cycling-243415&instancessize=50)
- [Monitoring dashboard (project)](https://console.cloud.google.com/monitoring?project=ardent-cycling-243415)
- [Monitor `consume-ztf` VM group](https://console.cloud.google.com/monitoring/groups/1832876284279888595?project=ardent-cycling-243415)
- [Log: troy-manual-ops](https://console.cloud.google.com/logs/query;query=logName%3D%22projects%2Fardent-cycling-243415%2Flogs%2Ftroy-manual-ops%22?project=ardent-cycling-243415&query=%0A)
---
- [confluent_kafka API](https://docs.confluent.io/current/clients/confluent-kafka-python/#pythonclient-consumer)
- [Kafka Python Client](https://docs.confluent.io/current/clients/python.html#)
---
- [ZTF Alert Distribution System Status](https://monitor.alerts.ztf.uw.edu/) 
- [ZTF Alert Archive - public](https://ztf.uw.edu/alerts/public/)
---

# Daily todo

__Deploy today's broker__
```bash
monthday=dec15
gcloud compute instances create-with-container consume-ztf-${monthday} --zone=us-central1-a --machine-type=n1-standard-1 --image-project=cos-cloud --container-image=gcr.io/ardent-cycling-243415/consume_ztf_today:tag1117a --labels=env=consume-ztf --image-family=cos-stable --service-account=591409139500-compute@developer.gserviceaccount.com --scopes=cloud-platform
```

Check [Dashboard `consume-ztf`](https://console.cloud.google.com/monitoring/dashboards/builder/3a371dcb-42d1-4ea0-add8-141d025924f6?project=ardent-cycling-243415&dashboardBuilderState=%257B%2522editModeEnabled%2522:false%257D&timeDomain=1h)
- Today's broker is receiving alerts
- Old brokers logging 'msg is None'

__Old brokers done consuming: stop VM and load alerts -> BQ__
```bash
gcloud auth login
pgbenv
cd ~/PGB_testing/deploy2cloud_Aug2020

day='08'
month='12'
monthname='dec'
year='2020'

./stopConsumer_loadBQ.sh ${day} ${month} ${monthname} ${year}
```

# ToC
- [Pre-meeting To do list](#pretodo)
- [To do list](#todo)
- [Status check](#status)
    - [Set up environment](#envsetup)
- [Deploying the Broker](#deploybroker)
    - [Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb](#testkafkaconnection)
- [Helpful GCP tasks](#gcptasks)
    - [Error Logging](#logging)
    - [View VM logs](#viewlogs)
    - [Manually stop, delete instance](#stopvm)
    - [Manual load GCS -> BQ](#manualGCS2BQ)
    - [Download an alert from GCS bucket](#dld-from-gcs)
    - [Manually trigger startInstancePubSub](#triggervm)
- [Fixing issues](#fix) (Kafka consumer ingestion is buggy)
    - [x]  [Docker login](#dockerlogin)
    - [x]  [Cloud Shell](#envsetup)
    - [x]  fixed paths (copy auth files) in Dockerfile
    - [x]  [fixed IAM permissions (Service Account Credentials)](#svccreds)
    - [x]  [SASL error](#sasl)
    - [x]  `msg = self.consume(num_messages=1, timeout=5)[0]` `"IndexError: list index out of range`. Solution: ZTF reset Kafka ofsets + we now use `self.poll()` instead of `self.consume()`
        - [Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb](#testkafkaconnection)
    - [ ]  [broker VM instance runs once but does not restart](#startinstance). May be related to Node.js 8 error in to-do list above.
    - [x]  Changed VM machine type to `g1-small` because resources were over-utilized
    - [ ]  [Consumer ingests for awhile, then just stops](#ingestionstops)
        - [ ]  [Restting Kafka consumer offsets](#offsets)
    - [ ]  `GCS_to_BQ` streaming rate limit exceeded ([quotas](https://cloud.google.com/bigquery/quotas#streaming_inserts), [table limits](https://cloud.google.com/bigquery/quotas#standard_tables))
    - [ ]  [Install Kafka directly (_not_ using Conda)](#kafka-direct-install)


<a name="pretodo"></a>
# Pre-meeting To do list
- [ ]  in `_avro2BQ`, see Not yet done section
- [ ]  are readthedocs up to date?
    - [ ]  alert_ingestion.rst
- [ ]  pull request conflict file `broker/alert_ingestion/GCS_to_BQ/main.py`


<a name="todo"></a>
# To do list
- [ ]  [install kafka directly (without conda)](https://docs.confluent.io/current/installation/installing_cp/deb-ubuntu.html#systemd-ubuntu-debian-install)
    - [-]  alternately, consider [using PyKafka](#pykafka) (recommended by Rubin for their stream)... Will not work because does not have SASL support
- [ ]  [set env variables from file](https://cloud.google.com/compute/docs/containers/configuring-options-to-run-containers#setting_environment_variables)
- [ ]  WARNING: The Node.js 8 runtime is deprecated on Cloud Functions. Please migrate to Node.js 10 (--runtime=nodejs10). See https://cloud.google.com/functions/docs/migrating/nodejs-runtimes
- [ ]  add GCS2BQ cloud fnc deployment to scheduleinstance.py
- [ ]  change Dockerfile to use master branch
- [ ]  fix publish_pubsub import to GCS2BQ cloud fnc (right now I've just copied the relevant function into the module.)
- [ ]  switch to Dataflow job
    - [ReadFromKafka](https://beam.apache.org/releases/pydoc/2.13.0/apache_beam.io.external.kafka.html#apache_beam.io.external.kafka.ReadFromKafka)
    - [example](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/examples/kafkataxi/kafka_taxi.py)

---
# Nov 5th meeting:
need to be able to query Antares and have them query us
2 bq tables:
    - one we can just do stuff with
    - one that is complete for ~year (get all these in a bucket first - Daniel will do this)
front end:
    - look at other broker websites. what do i like/not like
focus on manually running a bunch of stuff. can connect things later.

By time we write proposal
Should have set of alerts + history
    - classifications run on them
        - cloud fnc, query BQ, fit Salt2, push output to new BQ table
            - make db table queryable, not editable by public
    - way to query output and display a table (Daniel)
Xmatch with Vizier

---
<a name="status"></a>
# Status check
<!-- fs -->
1. Recommendation: "Switch VM resources with high CPU or memory usage to a recommended machine type." [here](https://console.cloud.google.com/home/recommendations?project=ardent-cycling-243415)
2. VM logs No module named `broker.consumer` from `consume_ztf.py`
3. environment variables not found

Deleting all GCP resources and trying to deploy the broker from scratch.
<!-- fe # Status check -->

<a name="envsetup"></a>
## Set up environment
<!-- fs -->
```bash
# pgbenv
# cd /Users/troyraen/Documents/PGB/repo/docker_files

# copy credential files to cloudshell
gcloud alpha cloud-shell scp localhost:/Users/troyraen/Documents/PGB/repo/krb5.conf cloudshell:~/Pitt-Google-Broker/.
gcloud alpha cloud-shell scp localhost:/Users/troyraen/Documents/PGB/repo/pitt-reader.user.keytab cloudshell:~/Pitt-Google-Broker/.

# log into Cloud Shell
gcloud alpha cloud-shell ssh
gcloud auth login

# create Conda env if necessary. use _env-setup/main.md
conda activate pgb
```
<!-- fe ## Set up environment -->

---
<a name="deploybroker"></a>
# Deploy broker
<!-- fs -->

Image `consume_ztf_today:tag1117a` will start a consumer connected to current day's topic. Start an instanced named `consume-ztf-${monthday}` by running the following on cloud shell:
```bash
cd ~/Pitt-Google-Broker/broker/cloud_functions
./scheduleinstance_today.sh
```

---
To create a new image and start a VM instance using it (e.g., to consume a day other than today), do the following:

__Create and push the Docker image__
~[Install Docker on a Mac](https://runnable.com/docker/install-docker-on-macos)~

Use Google Cloud Shell, `docker` is already installed.

Following
- [our docs](https://pitt-broker.readthedocs.io/en/development/deployment/deploying_images.html)
- [Pushing and pulling images](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
- [Containers on Compute Engine](https://cloud.google.com/compute/docs/containers)

```bash
# configure Docker
# gcloud auth configure-docker gcr.io

# build the image
cd /home/troy_raen_pitt/Pitt-Google-Broker
docker build -t consume_ztf_today -f /home/troy_raen_pitt/Pitt-Google-Broker/docker_files/consume_ztf_today.Dockerfile . --no-cache=true
# docker build -t consume_ztf -f /home/troy_raen_pitt/Pitt-Google-Broker/docker_files/consume_ztf.Dockerfile . #--no-cache=true

# tag the image
tag='tag1203a'
git log -1 --format=format:"%H" # get git commit hash to use for the TAG
# docker tag [SOURCE_IMAGE] [HOSTNAME]/[PROJECT-ID]/[IMAGE]:[TAG]
docker tag consume_ztf_today gcr.io/ardent-cycling-243415/consume_ztf_today:${tag}
# docker tag consume_ztf gcr.io/ardent-cycling-243415/consume_ztf:b0bf99587db1ce3f02ace762b087503d1d48db71c

# push the image
docker push gcr.io/ardent-cycling-243415/consume_ztf_today:${tag}
# docker push gcr.io/ardent-cycling-243415/consume_ztf:b0bf99587db1ce3f02ace762b087503d1d48db71c
```

__Setup GCP__
```python
from broker import gcp_setup
gcp_setup.auto_setup()
```

__Setup firewall rule__
```bash
gcloud compute firewall-rules create 'ztfport' --allow=tcp:9094 --description="Allow incoming traffic on TCP port 9094" --direction=INGRESS --enable-logging
```



__Deploy using scheduleinstance.sh__

Before doing this, delete resources if previously created:
- VM instances
- PubSub topics
- Cloud functions
- Cloud Scheduler

```bash
cd ~/Pitt-Google-Broker/broker/cloud_functions
# nano scheduleinstance.sh # update image tag
./scheduleinstance_today.sh
# ./scheduleinstance.sh
```

This schedules the broker to be deployed nightly.
To test some functionality, __start/stop an instance__ by manually sending a PubSub message to trigger the cloud function:

```bash
cd scheduleinstance
echo -n '{"zone":"us-central1-a", "label":"env=consume-ztf-1"}' | base64
# copy the encoded output and use it to replace `${data}` below
gcloud functions call startInstancePubSub --data '{"data":"${data}"}'
gcloud functions call startInstancePubSub --data '{"data":"eyJ6b25lIjoidXMtY2VudHJhbDEtYSIsICJsYWJlbCI6ImVudj1jb25zdW1lLXp0Zi0xIn0="}'

# check the status
gcloud compute instances describe consume-ztf-1 \
    --zone us-central1-a \
    | grep status

us-central1-a

# us-west1-b
# Using this zone, output from gcloud functions call:
# result: Successfully started instance(s)
# However, gcloud compute call could not find the instance
```

This is not running because it can't find the authentication files.

Solution: package the files with the Dockerimage

For the service account credentials:
<!-- fe deploy broker -->

---
<a name="gcptasks"></a>
# Helpful GCP tasks
<!-- fs -->

<a name="logging"></a>
## Error Logging
<!-- fs -->
__Some useful log messages to search for__
- container ID: `Starting a container with ID: <af17530117a00547c18818ebf0bc87e492dad06117f78b98706f4141b1349937>`
<!-- gcr.io/ardent-cycling-243415/consume_ztf_today -->
- `Pulling image: <'gcr.io/ardent-cycling-243415/consume_ztf_today:tag1103c'>`
- `Successfully sent gRPC to Stackdriver Logging API.`

__Write to Stackdriver logs directly__
- [severity options](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity)

```python
from google.cloud import logging
logging_client = logging.Client()
log_name = 'troy-manual-ops'
logger = logging_client.logger(log_name)
logger.log_text(msg, severity='NOTICE')
```

__Trying to integrate GCP logging with python modules:__
- [quickstart](https://cloud.google.com/logging/docs/quickstart-python)
- [severity options](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity)

Testing from terminal
```bash
sshg
gcloud auth login
git clone https://github.com/GoogleCloudPlatform/python-docs-samples
cd python-docs-samples/logging/cloud-client
python snippets.py my-log write
# this doesn't work. i think the issue is authentication from service account but error messages are very vague.
```

__GCP console dashboard recommends installing monitoring and logging agents.__
Found that neither is supported for Container-Optimized OS, so we can't use them.
- [Cloud Monitoring](https://cloud.google.com/monitoring/agent/installation?_ga=2.164611839.-1326490616.1602709223&_gac=1.191248728.1603912261.Cj0KCQjwreT8BRDTARIsAJLI0KJddB2avE270n6iRzLZrZVZVhlZn4kOSQsflblDZU_ebUXMtllmbBAaArLlEALw_wcB) - NOT SUPPORTED FOR THE Container-Optimized OS)
    - seems like this has to be installed in the instance itself, not in the container => can't use the Dockerfile for this. suggestion is to either install this just after creating the instance (which will stop/start the instance) or to apply monitoring agent across multiple VMs (this will not work with the cos OS)
- [Cloud Logging](https://cloud.google.com/logging/docs/agent/installation?_ga=2.232268255.-1326490616.1602709223&_gac=1.162537038.1603912261.Cj0KCQjwreT8BRDTARIsAJLI0KJddB2avE270n6iRzLZrZVZVhlZn4kOSQsflblDZU_ebUXMtllmbBAaArLlEALw_wcB) - something was enabled by adding ` --metadata=google-logging-enabled=true` to the `gcloud compute instances create-with-container` command, but I think it's different from the cloud logging agent.

<!-- fe # Error Logging -->

<a name="viewlogs"></a>
## View VM logs
<!-- fs -->
```bash
gcloud compute instances describe consume-ztf-nov15 --zone us-central1-a
# copy instance id
gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=3541645371775973317" --limit 10 --format json
```

```python
from google.cloud import logging
from google.cloud.logging import DESCENDING
client = logging.Client()
filter = "resource.type:gce_instance"
for i, entry in enumerate(client.list_entries(filter_=filter)):
    print(entry.resource)
    print(entry.payload)
    print()
    if i==10: break
```

<!-- fe View VM logs -->

<a name="stopvm"></a>
## Manually stop, delete instance
<!-- fs -->
```bash
gcloud compute instances list
gcloud compute instances stop consume-ztf-nov12 --zone us-central1-a
gcloud compute instances delete consume-ztf-nov12 consume-ztf-today --zone us-central1-a

```

<!-- fe ## Manually stop, delete instance -->

<a name="manualGCS2BQ"></a>
## Manual load GCS -> BQ
<!-- fs -->
Taking most of this from GCS2BQ cloud function.

List all alerts in the bucket

```bash
gsutil ls gs://ardent-cycling-243415_ztf_alert_avro_bucket/ > alertsinbucket.txt
```

first message in bucket: 1602555837398.avro
first message ingested on 11/11: 1605061900912.avro

`gcloud auth login`

```python
# import time
# import datetime
# s = "11/10/2020"
# time.mktime(datetime.datetime.strptime(s, "%d/%m/%Y").timetuple())
# kafka_datetime = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(1605062619785/1000.))

import manual_GCS2BQ as g2b

file_name = '1605*.avro'
g2b.GCS2BQ(file_name)

```

<!-- fe Manual load GCS -> BQ -->

<a name="dld-from-gcs"></a>
## Download an alert from GCS bucket
<!-- fs -->
Following instructions [here](https://medium.com/@sandeepsinh/multiple-file-download-form-google-cloud-storage-using-python-and-gcs-api-1dbcab23c44)

```python
import logging
import os
from google.cloud import storage

bucket_name = 'ardent-cycling-243415_ztf_alert_avro_bucket'
fname_prefix = '1605062619785'  # recently ingested avro file name, get from logging
local_dir = './testdownload'
delimiter = '/'

storage_client = storage.Client.from_service_account_json('GCPauth_pitt-google-broker-prototype-0679b75dded0.json')
bucket = storage_client.get_bucket(bucket_name)
blobs = bucket.list_blobs(prefix=fname_prefix, delimiter=delimiter) #List all objects that satisfy the filter.
# Download the file to a destination
# Iterating through for loop one by one using API call
for blob in blobs:
    destination_uri = '{}/{}'.format(local_dir, blob.name)
    blob.download_to_filename(destination_uri)
```
<!-- fe Download an alert from GCS bucket -->

<a name="triggervm"></a>
## Manually trigger startInstancePubSub
<!-- fs -->
I was able to manually trigger the cloud function startInstancePubSub with `gcloud functions call startInstancePubSub --data '{"data":"${data}"}'`. The logs say that the function executed successfully, and that the compute instance started, but nothing further happens. There are no errors in the logs, but none of the resources get set up and the VM doesn’t appear to actually be doing anything. Still looking…

It looks like the instance is already running due to the first command in `scheduleinstance.py`, `gcloud compute instances create-with-container`. Then I manually stopped (but did not delete) the container and tried the manual trigger again. This time it gives an error,
`{ "@type": "type.googleapis.com/cloud_integrity.IntegrityEvent", "bootCounter": "2", "lateBootReportEvent": { ... } }`
which appears to be due to the "Shielded VM" integrity measures. This integrity check passed before, so I don't think this is a useful error to track down.

Manually created a compute instance (`instance-1`) using the image. Logs show no errors, look similar to previous "successes". Logged into the VM instance:
`Google Cloud Platform -> VM Instances -> arrow next to "SSH" in connect column -> Open in browser window`. When I logged in there was a message saying
`The startup agent encountered errors. Your container
  was not started. To inspect the agent's logs use
  'sudo journalctl -u konlet-startup' command.`
When I ran this command I found the error
`Error: Failed to start container: Error response fr
om daemon: {"message":"pull access denied for gcr.io/ardent-cycling-243415/consume_ztf, repository does not exist or ma
y require 'docker login': denied: Permission denied for \"5b4068358afbf88c34b7cb0aa48e68553482eb2f\" from request \"/v2
/ardent-cycling-243415/consume_ztf/manifests/5b4068358afbf88c34b7cb0aa48e68553482eb2f\". "}`

Logged in (SSH) to `consume-ztf-2` (which I don't think I've altered since trying to start it using `scheduleinstance.py` using same method from above... Same error message is displayed at top of screen, and same error is in the "agent's logs".

<!-- fe Manually trigger compute instance -->

<!-- fe Helpful GCP tasks -->

---
<a name="fix"></a>
# Attempts to fix various things (Kafka consumer ingestion is buggy)

Biggest issue is that consumer sometimes just can't/won't receive alerts.
Call to `consumer.poll()` just timeout, returns `None`.


<a name="ingestionstops"></a>
## Consumer ingests for awhile, then just stops
<!-- fs -->
See, e.g.,
- machine id 5597883590625052742
- [Logs from time period where ingestion stoped](https://console.cloud.google.com/logs/query;timeRange=2020-10-30T20:30:26.178Z%2F2020-10-30T20:33:26.178Z?project=ardent-cycling-243415)

Confirmed I was able to get alerts from today's topic (ztf_20201110_programid1). Now try broker with this topic.
- _MACHINE_ID": "3d66d010f2ccccc60d32b64cdc93310d"
- first msg successfully received at 14:41:56.482

<!-- fe Consumer ingests for awhile, then just stops -->

<a name="offsets"></a>
## Restting Kafka consumer offsets
<!-- fs -->
- [confluent-kafka Consumer Read the Docs](https://docs.confluent.io/current/clients/confluent-kafka-python/#consumer)
- [Consumer config dict options](https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md)

Email exchange with Christopher Phillips (ZTF):
- Me: It seems that once I lose access to a certain topic I can never get it back. Every call to `poll()` just times out. I'll see what happens over the next few days and go from there.
- Christopher: Ah! You have to reset your consumer offsets. If you don't, kafka thinks that you're done ingesting the topic. If you reset your consumer offsets then you will be able to ingest past topics (up until 7 days).
- Christopher: If resetting the consumer offsets does not work at first, then you may have some 'stale' records that can be found (in our configuration) /var/lib/kafka/ In there you may find consumer offsets that look something like this: `__consumer_offset*` Delete these and then restart kafka/mirrormaker, and your alerts may start to flow again.

I think these instructions or for if I'm using Kafka from the command line, wihch I have never gotten to work.

Trying in python:

```python

from confluent_kafka import Consumer, KafkaException, TopicPartition, OFFSET_BEGINNING
import os
import sys

os.environ['KRB5_CONFIG'] = './krb5.conf'
# Consumer configuration
# See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
conf = {
            'bootstrap.servers': 'public2.alerts.ztf.uw.edu:9094',
            'group.id': 'group',
            'session.timeout.ms': 6000,
            'enable.auto.commit': 'TRUE',
            'sasl.kerberos.principal': 'pitt-reader@KAFKA.SECURE',
            'sasl.kerberos.kinit.cmd': 'kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}',
            'sasl.kerberos.keytab': './pitt-reader.user.keytab',
            'sasl.kerberos.service.name': 'kafka',
            'security.protocol': 'SASL_PLAINTEXT',
            'sasl.mechanisms': 'GSSAPI',
            'auto.offset.reset': 'earliest',
#             'enable.sparse.connections': 'false',
#             'max.poll.interval.ms': 1000000
            }
c = Consumer(conf, debug='fetch')

topic = 'ztf_20201116_programid1'
tp = TopicPartition(topic)
print(tp)
tp.offset = OFFSET_BEGINNING
print(tp)

c.assign([tp])

msg = None
try:
    while msg is None:
        msg = c.poll(timeout=5.0)
        print(msg)
except KeyboardInterrupt:
        sys.stderr.write('%% Aborted by user\n')
finally:
        c.close()

```

<!-- fe Restting Kafka consumer offsets -->


<a name="">startinstance</a>
## Stop/Start compute instance not working properly
<!-- fs -->
Trying to make this process work: https://cloud.google.com/scheduler/docs/start-and-stop-compute-engine-instances-on-a-schedule

start today instance
manually trigger PS message to stop
manually trigger PS message to start
see what happens

add debug log statements
    - connect Cloud Logging to python root logger: https://cloud.google.com/logging/docs/setup/python#connecting_the_library_to_python_logging
add logs writer role to IAM service account
re-deploy

trigger cloud function to Start/Stop an instance from command line
```bash
echo '{"zone":"us-central1-a", "label":"env=consume-ztf-1"}' | base64
# there ended up being a space in data that I had to manually remove. no idea why
gcloud functions call stopInstancePubSub --data '{"data":"eyJ6b25lIjoidXMtY2VudHJhbDEtYSIsICJsYWJlbCI6ImVudj1jb25zdW1lLXp0Zi0xIn0K"}'
gcloud functions call startInstancePubSub --data '{"data":"eyJ6b25lIjoidXMtY2VudHJhbDEtYSIsICJsYWJlbCI6ImVudj1jb25zdW1lLXp0Zi0xIn0K"}'
```

<!-- fe Stop/Start compute instance not working -->


<a name="testkafkaconnection"></a>
## Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb
<!-- fs -->
```python
# conda activate pgb2, on Roy
from confluent_kafka import Consumer, KafkaException
import os
import sys

os.environ['KRB5_CONFIG'] = './krb5.conf'

# Consumer configuration
# See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
conf = {
            'bootstrap.servers': 'public2.alerts.ztf.uw.edu:9094',
            'group.id': 'group',
            'session.timeout.ms': 6000,
            'enable.auto.commit': 'TRUE',
            'sasl.kerberos.principal': 'pitt-reader@KAFKA.SECURE',
            'sasl.kerberos.kinit.cmd': 'kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}',
            'sasl.kerberos.keytab': './pitt-reader.user.keytab',
            'sasl.kerberos.service.name': 'kafka',
            'security.protocol': 'SASL_PLAINTEXT',
            'sasl.mechanisms': 'GSSAPI',
            'auto.offset.reset': 'earliest'
            }

# Create Consumer instance
# Hint: try debug='fetch' to generate some log messages
c = Consumer(conf)

def print_assignment(consumer, partitions):
        print('Assignment:', partitions)

# Subscribe to topics
c.subscribe(['ztf_20201201_programid1'])

# msg = c.consume(num_messages=1, timeout=1)

# Read messages from Kafka, print to stdout
try:
    while True:
        print('while True')

        msg = c.poll(timeout=1.0)
        print('poll')

        if msg is None:
            print('continue')
            continue
        if msg.error():
            print('error')
            raise KafkaException(msg.error())
        else:
            print('else')
            print(msg.value())
            break
except KeyboardInterrupt:
        print('%% Aborted by user\n')
finally:
        # Close down consumer to commit final offsets.
        c.close()

```

<!-- fe # Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb -->

<a name="pykafka"></a>
## Using PyKafka
<!-- fs -->
- [PyKafka](https://pykafka.readthedocs.io/en/latest/index.html)
- Also see "Writing your own consumer" at the bottom of [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/)

```bash
conda clean --all
conda create -n pgb-pykafka python=3.7 ipython
conda activate pgb-pykafka
pip install pykafka

ipython
```
```python
from pykafka import KafkaClient, SslConfig
config = SslConfig( cafile='pitt-reader@KAFKA.SECURE',
                    certfile='pitt-reader@KAFKA.SECURE',  # optional
                    keyfile='./pitt-reader.user.keytab')  # optional
client = KafkaClient(hosts="public2.alerts.ztf.uw.edu:9094", ssl_config=config)
```

_This will not work because PyKafka does not provide SASL support._

<!-- fe Using PyKafka -->


<a name="svccreds"></a>
## Service Account Credentials (8/17/20)
<!-- fs -->
Following instructions [here](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances).

Service account
- [x]  name: Compute Engine default service account
- [x]  email: 591409139500-compute@developer.gserviceaccount.com
- [x]  remove role: Editor
- [x]  add role: Compute Admin
- [x]  add role: Service Account User

Code changes:
- [x]  Removed line `ENV GOOGLE_APPLICATION_CREDENTIALS "GCPauth.json"` from `consume_ztf.Dockerfile`. Not sure if it will cause other problems since that file will no longer be there.
- [x]  Removed line `COPY GCPauth.json GCPauth.json` from `consume_ztf.Dockerfile`.

It is unclear to me whether this will cause authentication problems for other parts of the deployment code or for individual modules. Need to try it and see. If there are problems, see [this link](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#clientlib) for help.

<!-- fe Service Account Credentials -->


<a name="dockerlogin"></a>
## docker login
<!-- fs -->
May need to do `gcloud auth configure-docker`, see [this help page](https://cloud.google.com/sdk/gcloud/reference/auth/configure-docker). Configuration may already be set up in Google Cloud Shell. Log into that and try it.

```bash
# set the project
gcloud config set project ardent-cycling-243415

# clone the repo
git clone https://github.com/mwvgroup/Pitt-Google-Broker.git
cd Pitt-Google-Broker
git fetch
git checkout development
cd broker/cloud_functions
./scheduleinstance.sh

# this gives the same `docker login` error
```

The Docker image is in the GCP project, so we should not need to configure Docker authentication for this (see 3rd paragraph [here](https://cloud.google.com/artifact-registry/docs/docker/authentication#methods))

Added role `Artifact Registry Administrator` to the compute service account. Got same `docker login` error.

Added `storage-rw` scope to `gcloud compute instances create-with-container` call. Got same `docker login` error.

Found out `docker` is installed on Google Cloud Shell. Try using this to create and push an image and then call `scheduleinstance.sh`. This will ensure I have Docker credentials on the machine I'm using to call `scheduleinstance`. Got same `docker login` error.

Tried to do `gcloud auth configure-docker gcr.io/ardent-cycling-243415/consumeztf` and got `WARNING: gcr.io/ardent-cycling-243415/consumeztf is not a supported registry
`

Tried to do `docker pull gcr.io/ardent-cycling-243415/consumeztf:7019f8aa86ffe16dcb36fa791dc2fb7e56bb687f` and got
`ERROR: (gcloud.auth.docker-helper) You do not currently have an active account selected.
Please run:

  $ gcloud auth login

to obtain new credentials.`

Ran `gcloud auth login` and followed the instructions, then got `You are now logged in as [troy.raen.pitt@gmail.com].` The `docker pull` command now works. Trying to `scheduleinstance.sh` again.

Added project editor IAM permissions to compute default account. Now it seems to be working.
<!-- fe docker login -->

<a name="sasl"></a>
## SASL error
<!-- fs -->
getting error
`cimpl.KafkaException: KafkaError{code=_INVALID_ARG,val=-186,str="Failed to create consumer: No provider for SASL mechanism GSSAPI: recompile librdkafka with libsasl2 or openssl support. Current build options: PLAIN SASL_SCRAM OAUTHBEARER"}`

Email from ZTF people, forwarded by Daniel, says this is an Ubuntu-specific problem and that we need to install via `sudo apt install krb5-user python3-kafka python3-confluent-kafka`. Tried to add this to `consume_ztf.Dockerfile`, can get the build to complete successfully, but still getting the same error.

Later convo with Christopher Phillips, he said people he knows have abandoned try to use Conda with Kafka and are just installing directly.
<!-- fe SASL error -->
