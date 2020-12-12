#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import apache_beam as beam
from apache_beam.io import BigQueryDisposition as bqdisp
from apache_beam.io import ReadFromPubSub, WriteToBigQuery
from apache_beam.io.gcp.bigquery_tools import RetryStrategy
from apache_beam import DoFn

import beam_helpers.data_utils as dutil
from beam_helpers.filters import is_extragalactic_transient


# gcp resources
PROJECTID = 'ardent-cycling-243415'
# dataflow_job_name = f'production-ztf-alert-data-ps-extract-strip-bq'
dataflow_job_name = f'test-ztf-branch'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_PS_topic = 'projects/ardent-cycling-243415/topics/ztf_alert_data'
output_BQ_table = 'dataflow_test.ztf_alerts'
# output_BQ_table = 'ztf_alerts.alerts'

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 5
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'


config_writeBQFullPacket = {
                            # 'schema': 'SCHEMA_AUTODETECT',
                            'project': PROJECTID,
                            'create_disposition': bqdisp.CREATE_NEVER,
                            'write_disposition': bqdisp.WRITE_APPEND,
                            'validate': False,
                            'insert_retry_strategy': RetryStrategy.RETRY_NEVER,
                            'batch_size': 5000,
}

with beam.Pipeline(options=options) as bp:
    # Read from PS and extract data as dicts
    PSin = (bp | 'ReadFromPubSub' >> ReadFromPubSub(topic=input_PS_topic))
    alertDicts = (PSin | 'ExtractAlertDict' >> beam.ParDo(dutil.ExtractAlertDict()))
    alertDictsSC = (alertDicts | 'StripCutouts' >> beam.ParDo(dutil.StripCutouts()))

    # Upload to BQ
    # BQ encoding error until cutouts were stripped. see StripCutouts() for more details
    # alerts with no history cannot currently be uploaded -> RETRY_NEVER
    # TODO: track deadletters, get them uploaded to bq
    bqDeadletters = (alertDictsSC | 'WriteToBigQuery' >> WriteToBigQuery(
                            output_BQ_table, **config_writeBQFullPacket
                            ))


