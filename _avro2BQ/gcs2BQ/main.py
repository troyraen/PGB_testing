#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""The ``gcs2BQ`` module loads Avro files from a Google Cloud Storage (GCS) bucket into a BigQuery (BQ) table.

Usage Example
-------------

.. code-block:: python
   :linenos:

"""

import os
import json
from google.cloud import bigquery
from google.cloud import storage


PROJECT_ID = os.getenv('GCP_PROJECT')
BQ_DATASET = 'GCS_Avro_to_BigQuery_test'
BQ_TABLE = 'streaming_test1'
CS = storage.Client()
BQ = bigquery.Client()


def streaming(data, context):
    '''This function is executed whenever a file is added to Cloud Storage'''
    bucket_name = data['bucket']
    file_name = data['name']

    # from https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-avro
    table_ref = BQ.dataset(BQ_DATASET).table(BQ_TABLE)
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.source_format = bigquery.SourceFormat.AVRO
    uri = f"gs://{bucket_name}/{file_name}"
    load_job = BQ.load_table_from_uri(
        uri, table_ref, job_config=job_config
    )  # API request
    print("Starting job {}".format(load_job.job_id))

    load_job.result()  # Waits for table load to complete.

    destination_table = BQ.get_table(table_ref)
    print("Loaded {} rows.".format(destination_table.num_rows))

    # _insert_into_bigquery(bucket_name, file_name)



def _insert_into_bigquery(bucket_name, file_name):
    blob = CS.get_bucket(bucket_name).blob(file_name)
    row = json.loads(blob.download_as_string())
    table = BQ.dataset(BQ_DATASET).table(BQ_TABLE)
    errors = BQ.insert_rows_json(table,
                                 json_rows=[row],
                                 row_ids=[file_name],
                                 retry=retry.Retry(deadline=30))
    if errors != []:
        raise BigQueryError(errors)
