#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Adapted from https://github.com/lsst-dm/alert-stream-simulator#writing-your-own-consumer

import sys
from tempfile import SpooledTemporaryFile
import json
from google.cloud import storage, pubsub_v1
import pykafka
import lsst.alert.stream.serialization as lass

# parse sys args
broker_host = sys.argv[1]
N_alerts = int(sys.argv[2])  # num alerts to ingest before quitting
# send a third arg (= bq table name) to load 1 alert to a bq table (see below)

# consumer setup
message_max_bytes = 10000000
client = pykafka.KafkaClient(hosts=broker_host)
topic = client.topics['rubin_example_stream']
consumer = topic.get_simple_consumer(fetch_message_max_bytes=message_max_bytes)

# GCS storage
PROJECT_ID = 'ardent-cycling-243415'
storage_client = storage.Client()
bucket_name = f'{PROJECT_ID}_rubin-sims'
gcs_folder_name = 'alert_avro'
bucket = storage_client.get_bucket(bucket_name)
def store_in_bucket(alert_bytes, gcs_filename):
    blob = bucket.blob(f'{gcs_folder_name}/{gcs_filename}')
    with SpooledTemporaryFile(max_size=message_max_bytes, mode='w+b') as ftmp:
        ftmp.write(alert_bytes)
        ftmp.seek(0)
        blob.upload_from_file(ftmp)

# PubSub
topic_name = 'rubin-simulated-alerts'
pubsub_client = pubsub_v1.PublisherClient()
topic_path = pubsub_client.topic_path(PROJECT_ID, topic_name)
def publish_pubsub(alert_bytes):
    # alert_dict['gcs_filename'] = gcs_filename
    # del alert_dict['cutoutDifference']
    # del alert_dict['cutoutTemplate']
    # abytes = json.dumps(alert_dict).encode('utf-8')
    future = pubsub_client.publish(topic_path, data=alert_bytes)


for i, raw_msg in enumerate(consumer):
    # extract alert
    alert_bytes = raw_msg.value
    alert_dict = lass.deserialize_alert(alert_bytes)
    # strip the bytes header (alert is in confluent wire format)
    # see lsst.alert.stream.serialization.py
    alert_bytes = alert_bytes[5:]

    gcs_filename = f"{alert_dict['diaObject']['diaObjectId']}_{alert_dict['alertId']}.avro"
    store_in_bucket(alert_bytes, gcs_filename)

    publish_pubsub(alert_bytes)

    if i==(N_alerts-1): break

# load one alert into BQ table to ensure the table exists with the proper schema
# this avoids having to generate a bigquery schema when calling
# WriteToBigQuery in Beam pipeline
# skipped if no 3rd system argument supplied
def load_last_avro2bq(BQ_TABLE_ID, uri):
    from google.cloud import bigquery
    print('attempting to create BQ table')

    BQ = bigquery.Client()
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.source_format = bigquery.SourceFormat.AVRO
    
    load_job = BQ.load_table_from_uri(uri, BQ_TABLE_ID, job_config=job_config)
    load_job.result() # run the job

    if load_job.error_result is not None:
        print(load_job.error_result)
    else:
        print(f'successfully created/appended {BQ_TABLE_ID}')

try:
    BQ_TABLE_ID = sys.argv[3]
except:
    pass
else:
    uri = f'gs://{bucket_name}/{gcs_folder_name}/{gcs_filename}'
    load_last_avro2bq(BQ_TABLE_ID, uri)