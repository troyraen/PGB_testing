#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import apache_beam as beam
from apache_beam.io import BigQueryDisposition as bqdisp
from apache_beam.io import ReadFromPubSub, Write, WriteToBigQuery

# from tempfile import SpooledTemporaryFile
from apache_beam import DoFn

# from beam_helpers import data_utils as dutils


# year, month, day = '2020', '12', '07'

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = f'ztf-alert-data-ps-extract-log'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_PS_topic = 'projects/ardent-cycling-243415/topics/ztf_alert_data'
output_BQ_table = 'dataflow_test.ztf_alerts'

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 10
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'

class ExtractAlertData(DoFn):
    # def setup(self):
    #     import io
    #     import fastavro as fa

    def process(self, msg):
        from io import BytesIO
        from fastavro import reader

        # Extract the alert data from msg -> dict
        with BytesIO(msg) as fin:
            # print(type(fin))
            alertDicts = [r for r in reader(fin)]

        candid = alertDicts[0]['candid']
        logging.info(f'Extracted alert data dict for candid {candid}')

        # print(f'{alertDicts[0]}')
        return alertDicts


with beam.Pipeline(options=options) as bp:
    output = (
        bp | 'ReadFromPubSub' >> ReadFromPubSub(topic=input_PS_topic)
           | 'ExtractAlertDict' >> beam.ParDo(ExtractAlertData())
           # | 'Print msg bytes' >> beam.Map(print)
           # | 'WriteToBigQuery' >> Write(WriteToBigQuery(
           #                      output_BQ_table,
           #                      # schema='SCHEMA_AUTODETECT',
           #                      project = PROJECTID,
           #                      create_disposition = bqdisp.CREATE_NEVER,
           #                      write_disposition = bqdisp.WRITE_APPEND,
           #                      validate = False
           #                      ))
    )


    # alertDict | 'fit Salt2' >> beam.ParDo(s2.fitSalt2)


# bp.run()  # .wait_until_finish()
