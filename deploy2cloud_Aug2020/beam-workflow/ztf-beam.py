#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import apache_beam as beam
from apache_beam.io import BigQueryDisposition as bqdisp
from apache_beam.io import ReadFromPubSub, Write, WriteToBigQuery
from apache_beam.io.gcp.bigquery_tools import RetryStrategy

from apache_beam import DoFn


# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = f'production-ztf-alert-data-ps-extract-strip-bq'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_PS_topic = 'projects/ardent-cycling-243415/topics/ztf_alert_data'
# output_BQ_table = 'dataflow_test.ztf_alerts'
output_BQ_table = 'ztf_alerts.alerts'

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 50
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'

class ExtractAlertDict(DoFn):
    def process(self, msg):
        from io import BytesIO
        from fastavro import reader

        # Extract the alert data from msg -> dict
        with BytesIO(msg) as fin:
            # print(type(fin))
            alertDicts = [r for r in reader(fin)]

        # candid = alertDicts[0]['candid']
        # logging.info(f'Extracted alert data dict for candid {candid}')
        # print(f'{alertDicts[0]}')
        return alertDicts

class StripCutouts(DoFn):
    # before stripping the cutouts, the upload to BQ failed with the following:
    # UnicodeDecodeError: 'utf-8 [while running 'WriteToBigQuery/WriteToBigQuery/_StreamToBigQuery/StreamInsertRows/ParDo(BigQueryWriteFn)-ptransform-133664']' codec can't decode byte 0x8b in position 1: invalid start byte
    # See Dataflow job ztf-alert-data-ps-extract-bq
    # started on December 7, 2020 at 1:51:44 PM GMT-5
    def process (self, alertDict):
        cutouts = ['cutoutScience', 'cutoutTemplate', 'cutoutDifference']
        alertStripped = {k:v for k, v in alertDict.items() if k not in cutouts}
        return [alertStripped]


with beam.Pipeline(options=options) as bp:
    output = (
        bp | 'ReadFromPubSub' >> ReadFromPubSub(topic=input_PS_topic)
           | 'ExtractAlertDict' >> beam.ParDo(ExtractAlertDict())
           # encoding error until cutouts were stripped. see fnc for more details
           | 'StripCutouts' >> beam.ParDo(StripCutouts())
           | 'WriteToBigQuery' >> Write(WriteToBigQuery(
                                output_BQ_table,
                                # schema='SCHEMA_AUTODETECT',
                                project = PROJECTID,
                                create_disposition = bqdisp.CREATE_NEVER,
                                write_disposition = bqdisp.WRITE_APPEND,
                                validate = False,
                                insert_retry_strategy = RetryStrategy.RETRY_NEVER,
                                # TODO: ^ => returns PColl of Deadletter items.
                                # Do something with them.
                                batch_size = 5000,
                                ))
    )


# bp.run()  # .wait_until_finish()
