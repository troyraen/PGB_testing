- Apache Beam
    - [Apache Beam Overview/Tutorial](https://beam.apache.org/documentation/programming-guide/)
    - [Apache Beam SDK (2.25.0) for Python](https://beam.apache.org/releases/pydoc/2.25.0/) 
    - [Managing Python Pipeline Dependencies](https://beam.apache.org/documentation/sdks/python-pipeline-dependencies/#multiple-file-dependencies)
    - [ParDo explanation/example](https://beam.apache.org/documentation/programming-guide/#core-beam-transforms)
    - [Deadletter handling, Python example](https://stackoverflow.com/questions/59102519/monitoring-writetobigquery)
- Dataflow
    - [dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
    - [Dataflow Quotas & limits](https://cloud.google.com/dataflow/quotas)
    - [Logging pipeline messages](https://cloud.google.com/dataflow/docs/guides/logging)


# Setup (install Beam, create resources)

```bash
gcloud auth login

pip install apache-beam[gcp]
```

Create resources:
```python
from google.cloud import bigquery, logging, storage
PROJECT_ID = 'ardent-cycling-243415'

# create buckets
bucket_name = f'{PROJECT_ID}_dataflow-test'
storage_client = storage.Client()
storage_client.create_bucket(bucket_name)

# create bq tables
bigquery_client = bigquery.Client()
bigquery_client.create_dataset('dataflow_test', exists_ok=True)
```

# Run beam pipeline

## `wordcount.py`: bucket (file) -> transform -> bucket
- [wordcount.py](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/examples/wordcount.py)
- [execute pipeline](https://beam.apache.org/get-started/quickstart-py/#execute-a-pipeline)

```bash

# python -m apache_beam.examples.wordcount --input gs://dataflow-samples/shakespeare/kinglear.txt \
#                                          --output gs://<your-gcs-bucket>/counts \
#                                          --runner DataflowRunner \
#                                          --project your-gcp-project \
#                                          --region your-gcp-region \
#                                          --temp_location gs://<your-gcs-bucket>/tmp/
bucket='ardent-cycling-243415_dataflow-test'
python -m wordcount --input gs://dataflow-samples/shakespeare/kinglear.txt \
                            --output gs://${bucket}/counts \
                            --runner DataflowRunner \
                            --project ardent-cycling-243415 \
                            --region us-central1 \
                            --temp_location gs://${bucket}/tmp/

```

## `uppercase.py`: BQ -> transform -> BQ
- [uppercase.py](https://github.com/hayatoy/dataflow-tutorial/blob/master/tutorial4.py)

```python
python -m uppercase --region us-central1
```
