# ZTF Beam Consumer
Rewriting the consumer into a Dataflow / Apache Beam job.

- Monitor the Dataflow job [`production-ztf-alert-data-ps-extract-strip-bq`](https://console.cloud.google.com/dataflow/jobs/us-central1/2020-12-07_12_14_06-12880147207196234384;step=;mainTab=JOB_METRICS?project=ardent-cycling-243415)

# ToC
- [Beam environment Prereqs](#beam-prereqs)
- [Create GCP resources](#gcpsetup)
- [Create and Run Beam](#runbeam)
- [Move code to `Pitt-Google-Broker` repo](#move2pgbrepo)


# To Do
- [-]  ReadFromKafka (not working, moving on)
    - Fix handling of auth files (currently packaged with Dataflow job)
- [-]  old code -> transform header and store in GCS
- [x]  store in BQ
    - [ ]  handle dead letters ([Python example](https://stackoverflow.com/questions/59102519/monitoring-writetobigquery))
- [x]  fit with Salt2
- [ ]  xmatch with Vizier



# Links
- Beam API
    - [`apache_beam.io.kafka`](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/io/kafka.py) (includes good description of the Java expansion service)
    - [`apache_beam.io.kafka.ReadFromKafka`](https://beam.apache.org/releases/pydoc/2.24.0/apache_beam.io.kafka.html#apache_beam.io.kafka.ReadFromKafka)
- Dataflow
    - [Updating an existing pipeline](https://cloud.google.com/dataflow/docs/guides/updating-a-pipeline)
    - [Read AVRO messages from PubSub in Dataflow Python](https://stackoverflow.com/questions/61216075/read-avro-messages-from-pubsub-in-dataflow-python)
- [Using Pub/Sub notifications for Cloud Storage](https://cloud.google.com/storage/docs/reporting-changes#gsutil)
- ['kafkataxi' example](https://github.com/apache/beam/tree/master/sdks/python/apache_beam/examples/kafkataxi)
- [alternate option, `beam_nuggets`](http://mohaseeb.com/beam-nuggets/beam_nuggets.io.kafkaio.html)
- [`fastavro reader`](https://fastavro.readthedocs.io/en/latest/reader.html)

<a name="beam-prereqs"></a>
# Beam environment Prereqs
<!-- fs -->
```bash
# set environment variables
EXPORT ztf_server='public2.alerts.ztf.uw.edu:9094'
EXPORT ztf_principle='pitt-reader@KAFKA.SECURE'
EXPORT ztf_keytab_path='pitt-reader.user.keytab'


```
<!-- fe Beam environment Prereqs -->


<a name="gcpsetup"></a>
# Create GCP resources
<!-- fs -->

__Setup PubSub notifications on GCS bucket__
- [Using Pub/Sub notifications for Cloud Storage](https://cloud.google.com/storage/docs/reporting-changes#gsutil)

```bash
BUCKET_NAME='ardent-cycling-243415_ztf_alert_avro_bucket'
TOPIC_NAME='projects/ardent-cycling-243415/topics/ztf_alert_avro_bucket'
format=json  # json or none; whether to deliver the payload with the PS msg
# create the notifications -> PS
gsutil notification create \
            -t ${TOPIC_NAME} \
            -e OBJECT_FINALIZE \
            -f ${format} \
            gs://${BUCKET_NAME}

# check the notifications on the bucket
gsutil notification list gs://${BUCKET_NAME}

# remove the notification
CONFIGURATION_NAME=11  # get from list command above
gsutil notification delete projects/_/buckets/${BUCKET_NAME}/notificationConfigs/${CONFIGURATION_NAME}
```

__Create other resources__

```python
from google.cloud import pubsub_v1, bigquery, storage
PROJECT_ID = 'ardent-cycling-243415'

# # create buckets
# bucket_name = f'{PROJECT_ID}_ztf-dataflow-test'
# storage_client = storage.Client()
# storage_client.create_bucket(bucket_name)
#
# # create bq dataset
# bigquery_client = bigquery.Client()
# bigquery_client.create_dataset('ztf_dataflow_test', exists_ok=True)

# create PS topics
topic = 'ztf_exgalac_trans'
topic = 'ztf_salt2'
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, topic)
publisher.create_topic(topic_path)
```

__Create test table `dataflow_test.ztf_alerts` using schema from `ztf_alerts.alerts`__
In Console -> BigQuery, perform this query:
```
CREATE TABLE dataflow_test.ztf_alerts AS
SELECT *
FROM ztf_alerts.alerts
LIMIT 0
```
<!-- fe Create GCP resources -->


<a name="runbeam"></a>
# Create and Run Beam
<!-- fs -->
Writing `ztf-beam.py` using `_LSST-sample-alerts` and `_dataflow-test` content as guides.

- [x]  update broker consumer to fix schema before publishing to PubSub
    - _this has been pushed, but currently deploying pre-saved containers => not using this update. PS is reading the messages fine._
- [ ]  listen to PS stream
- [ ]  write to BQ
- [ ]  Salt2

__Run the job__
```bash
pgbenv
cd ~/PGB_testing/deploy2cloud_Aug2020/beam-workflow
region='us-central1'
# region='us-east1'
python -m ztf-beam \
            --region ${region} \
            --experiments use_runner_v2 \
            --setup_file /home/troy_raen_pitt/PGB_testing/deploy2cloud_Aug2020/beam-workflow/setup.py \
            --streaming \
            # --update \
```


<!-- fe Create and Run Beam -->


<a name="move2pgbrepo"></a>
# Move code to `Pitt-Google-Broker` repo
<!-- fs -->

- [x]  move the existing code
- [ ]  clean up the code
    - [x]  move main script args to cmd line args, use `argparse`
    - [ ]  move function args to cmd line args
    - [ ]  handle some of the Salt2 errors with `try/except`
- [x]  add a beam+dataflow primer
- [ ]  update the docs

<!-- fe Move code to `Pitt-Google-Broker` repo -->


# Sand
<!-- fs -->
__ZTF msg data -> dict__
```python
# first, get a ztf alert using notebook code.
# msg.value() is the alert packet bytes
from tempfile import SpooledTemporaryFile
import fastavro as fa

maxsize = 1500000
with SpooledTemporaryFile(max_size=maxsize, mode='w+b') as temp_file:
    temp_file.write(msg.value())
    temp_file.seek(0)
    data = [r for r in fa.reader(temp_file)]
```

__read a tempfile__
```python
from tempfile import SpooledTemporaryFile

data = bytes('some-string', 'utf-8')
maxsize = 1500000
with SpooledTemporaryFile(max_size=maxsize, mode='w+b') as temp_file:
    temp_file.write(data)
    temp_file.seek(0)
    r = temp_file.read()
r.decode("utf-8")
```

<!-- fe Sand -->
