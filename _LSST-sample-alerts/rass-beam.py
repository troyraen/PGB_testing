#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import json
import apache_beam as beam
# from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.gcp.bigquery import WriteToBigQuery
# from apache_beam.io import Write, WriteToBigQuery
from apache_beam.io import BigQueryDisposition as bqd

import lsst.alert.stream.serialization as lass


# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = 'rubin-sims-ps-bq'
beam_bucket = 'ardent-cycling-243415_rubin-sims'
output_bq_table = 'rubin_sims.alerts'
topic_name = 'rubin-simulated-alerts'
topic_path = f'projects/{PROJECTID}/subscriptions/{topic_name}'
# pubsub_client = pubsub_v1.PublisherClient()
# topic_path = pubsub_client.topic_path(PROJECT_ID, topic_name)

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 3
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'


class log_alert_strip_header(beam.DoFn):
    def start_batch(self):
        import lsst.alert.stream.serialization

    def process(self, alert_bytes):
        alert = lsst.alert.stream.serialization.deserialize_alert(alert_bytes.value)
        # log alert type, Id
        logging.info(f'Alert type: {type(alert)}')
        logging.info(f"Alert ID: {alert['alertId']}")

        return [alert_bytes[5:]]

class extractAlertDict(beam.DoFn):
    def process(self, alert_bytes):
        """Expects that alert bytes were passed straight through from Kafka to PS"""
        # """Expects that alert was in form of dict before converting to bytes for PS"""
        # alert_dict = json.loads(alert_bytes.decode('utf-8')) 

        alert_dict = lass.deserialize_alert(alert_bytes)
        return [alert_dict]



with beam.Pipeline(options=options) as bp:
    output = (
        bp | 'ReadFromPubSub' >> ReadFromPubSub(subscription=topic_path)
            # | 'Log and strip header' >> beam.ParDo(log_alert_strip_header())
            | 'extractAlertDict' >> beam.ParDo(extractAlertDict())
            | 'WriteToBigQuery' >> WriteToBigQuery(output_bq_table, project=PROJECTID,
                                            #    schema='SCHEMA_AUTODETECT',
                                               create_disposition=bqd.CREATE_NEVER,
                                               write_disposition=bqd.WRITE_TRUNCATE)
            # salt2 + vizier?
    )

# bp.run()  # .wait_until_finish()
