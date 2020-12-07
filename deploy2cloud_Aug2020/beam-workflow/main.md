# ZTF Beam Consumer
Rewriting the consumer into a Dataflow / Apache Beam job.

- [Beam environment Prereqs](#beam-prereqs)
- [Create GCP resources](#gcpsetup)
- [Create and Run Beam](#runbeam)


# To Do
- __Fix handling of auth files (currently packaged with Dataflow job)__
- [ ]  ReadFromKafka
- [ ]  old code -> transform header and store in GCS
- [ ]  store in BQ
- [ ]  fit with Salt2
- [ ]  xmatch with Vizier


# Links
- Beam API
    - [`apache_beam.io.kafka`](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/io/kafka.py) (includes good description of the Java expansion service)
    - [`apache_beam.io.kafka.ReadFromKafka`](https://beam.apache.org/releases/pydoc/2.24.0/apache_beam.io.kafka.html#apache_beam.io.kafka.ReadFromKafka)
- ['kafkataxi' example](https://github.com/apache/beam/tree/master/sdks/python/apache_beam/examples/kafkataxi)
- [alternate option, `beam_nuggets`](http://mohaseeb.com/beam-nuggets/beam_nuggets.io.kafkaio.html)


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
```python
from google.cloud import bigquery, storage
PROJECT_ID = 'ardent-cycling-243415'

# # create buckets
# bucket_name = f'{PROJECT_ID}_ztf-dataflow-test'
# storage_client = storage.Client()
# storage_client.create_bucket(bucket_name)
#
# # create bq dataset
# bigquery_client = bigquery.Client()
# bigquery_client.create_dataset('ztf_dataflow_test', exists_ok=True)

```
<!-- fe Create GCP resources -->


<a name="runbeam"></a>
# Create and Run Beam
<!-- fs -->
Writing `ztf-beam.py` using `_LSST-sample-alerts` and `_dataflow-test` content as guides.

- read from kafka Stream
- transform (fix schema)
- write to gcs
- write to bq
- process

Troy VM:
- install Java
- clone PGB_testing
- scp auth files

__Run the job__
```bash
python -m ztf-beam \
            --region us-central1 \
            --setup_file setup.py \
            --experiments use_runner_v2 \
            --streaming
```

<!-- fe Create and Run Beam -->
