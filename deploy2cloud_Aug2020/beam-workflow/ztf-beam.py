#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import logging
import apache_beam as beam
from apache_beam.io import BigQueryDisposition as bqdisp
from apache_beam.io import ReadFromPubSub, WriteToPubSub, WriteToBigQuery
from apache_beam.io.gcp.bigquery_tools import RetryStrategy
from apache_beam import DoFn

import beam_helpers.data_utils as dutil
from beam_helpers.filters import is_extragalactic_transient
from beam_helpers.fit_salt2 import fitSalt2


# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = f'production-ztf-ps-bq-exgal-salt2'
# dataflow_job_name = f'test-ztf-full-exgal-salt2'
beam_bucket = f'{PROJECTID}_dataflow-test'
input_PS_topic = f'projects/{PROJECTID}/topics/ztf_alert_data'
# output_BQ_fullpacket = 'dataflow_test.ztf_alerts'
output_BQ_fullpacket = 'ztf_alerts.alerts'
# output_BQ_salt2 = 'dataflow_test.salt2'
output_BQ_salt2 = 'ztf_alerts.salt2'
output_PS_exgalTrans = f'projects/{PROJECTID}/topics/ztf_exgalac_trans'
output_PS_salt2 = f'projects/{PROJECTID}/topics/ztf_salt2'


# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 25
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'

config_writeBqFullPacket = {
                            # 'schema': 'SCHEMA_AUTODETECT',
                            'project': PROJECTID,
                            'create_disposition': bqdisp.CREATE_NEVER,
                            'write_disposition': bqdisp.WRITE_APPEND,
                            'validate': False,
                            'insert_retry_strategy': RetryStrategy.RETRY_NEVER,
                            'batch_size': 5000,
}

config_writeBqSalt2 = {
                      'schema': 'objectId:STRING, candid:INTEGER, success:INTEGER, ncall:INTEGER, chisq:FLOAT, ndof:INTEGER, z:FLOAT, z_err:FLOAT, t0:FLOAT, t0_err:FLOAT, x0:FLOAT, x0_err:FLOAT, x1:FLOAT, x1_err:FLOAT, c:FLOAT, c_err:FLOAT, z_z_cov:FLOAT, z_t0_cov:FLOAT, z_x0_cov:FLOAT, z_x1_cov:FLOAT, z_c_cov:FLOAT, t0_z_cov:FLOAT, t0_t0_cov:FLOAT, t0_x0_cov:FLOAT, t0_x1_cov:FLOAT, t0_c_cov:FLOAT, x0_z_cov:FLOAT, x0_t0_cov:FLOAT, x0_x0_cov:FLOAT, x0_x1_cov:FLOAT, x0_c_cov:FLOAT, x1_z_cov:FLOAT, x1_t0_cov:FLOAT, x1_x0_cov:FLOAT, x1_x1_cov:FLOAT, x1_c_cov:FLOAT, c_z_cov:FLOAT, c_t0_cov:FLOAT, c_x0_cov:FLOAT, c_x1_cov:FLOAT, c_c_cov:FLOAT, plot_lc_bytes:BYTES',
                      'create_disposition': bqdisp.CREATE_NEVER,
                      'write_disposition': bqdisp.WRITE_APPEND,
                      'insert_retry_strategy': RetryStrategy.RETRY_NEVER,
                    #   'batch_size': 50,

}

config_genericWritePS = {
                         'with_attributes': False,  # currently uploading bytes
                        #  may want to use these in the future:
                         'id_label': None,
                         'timestamp_attribute': None
}


with beam.Pipeline(options=options) as bp:
    #-- Read from PS and extract data as dicts
    PSin = (bp | 'ReadFromPubSub' >> ReadFromPubSub(topic=input_PS_topic))
    alertDicts = (PSin | 'ExtractAlertDict' >> beam.ParDo(dutil.extractAlertDict()))
    alertDictsSC = (alertDicts | 'StripCutouts' >> beam.ParDo(dutil.stripCutouts()))

    #-- Upload to BQ
    # BQ encoding error until cutouts were stripped. see StripCutouts() for more details
    # alerts with no history cannot currently be uploaded -> RETRY_NEVER
    # TODO: track deadletters, get them uploaded to bq
    bqAdDeadletters = (alertDictsSC | 'WriteToBigQuery' >> WriteToBigQuery(
                                                           output_BQ_fullpacket, 
                                                           **config_writeBqFullPacket)
                      )

    #-- Filter for extragalactic transients
    adscExgalTrans = (alertDictsSC | 'filterExgalTrans' >> beam.Filter(is_extragalactic_transient))
    # to PubSub
    egtPS = (adscExgalTrans | 'exgalTransFormatDictForPubSub' >> beam.ParDo(dutil.formatDictForPubSub()))
    psEgtDeadletters = (egtPS | 'exgalTransToPubSub' >> WriteToPubSub(
                                                        output_PS_exgalTrans,
                                                        **config_genericWritePS)
                       )

    #-- Fit with Salt2
    salt2Dicts = (adscExgalTrans | 'fitSalt2' >> beam.ParDo(fitSalt2()))
    # to BQ
    # TODO: do something with deadletters
    bqSalt2Deadletters = (salt2Dicts | 'salt2ToBQ' >> WriteToBigQuery(
                                                      output_BQ_salt2,
                                                      **config_writeBqSalt2)
                         )
    # to PubSub
    # TODO: do something with deadletters
    salt2PS = (salt2Dicts | 'salt2FormatDictForPubSub' >> beam.ParDo(dutil.formatDictForPubSub()))
    psSalt2Deadletters = (salt2PS | 'salt2ToPubSub' >> WriteToPubSub(
                                                        output_PS_salt2,
                                                        **config_genericWritePS)
                         )

