Rewriting the consumer into a Dataflow / Apache Beam job.

- [`apache_beam.io.kafka`](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/io/kafka.py) (includes good description of the Java expansion service)
- ['kafkataxi' example](https://github.com/apache/beam/tree/master/sdks/python/apache_beam/examples/kafkataxi)

- [alternate option, `beam_nuggets`](http://mohaseeb.com/beam-nuggets/beam_nuggets.io.kafkaio.html)

__Prereqs__
```bash
# set environment variables
EXPORT ztf_server='public2.alerts.ztf.uw.edu:9094'
EXPORT ztf_principle='pitt-reader@KAFKA.SECURE'
EXPORT ztf_keytab_path='pitt-reader.user.keytab'


```

Create GCP resources
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

# Create and Run Beam
- read from kafka Stream
- transform (fix schema)
- write to gcs
- write to bq
- process
