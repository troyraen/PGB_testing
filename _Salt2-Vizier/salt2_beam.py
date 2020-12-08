#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# +----------------+
# |                |
# | Read BigQuery  |
# |                |
# +-------+--------+
#         |
#         v
# +-------+--------+
# |                |
# | Modify Element |
# |                |
# +----------------+
#         |
#         v
# +-------+--------+
# |                |
# | Write BigQuery |
# |                |
# +----------------+

import apache_beam as beam

import custommods.beam_helpers as bhelp

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = 'salt2-fits'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_bq_table = 'ztf_alerts.alerts'
output_bq_table = 'ztf_alerts.salt2'
# storage_client = storage.Client()
# bucket = storage_client.get_bucket(beam_bucket)

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 100
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'
# output_schema must match salt2fit() return
output_schema = 'objectId:STRING, candid:INTEGER, success:INTEGER, ncall:INTEGER, chisq:FLOAT, ndof:INTEGER, z:FLOAT, z_err:FLOAT, t0:FLOAT, t0_err:FLOAT, x0:FLOAT, x0_err:FLOAT, x1:FLOAT, x1_err:FLOAT, c:FLOAT, c_err:FLOAT, z_z_cov:FLOAT, z_t0_cov:FLOAT, z_x0_cov:FLOAT, z_x1_cov:FLOAT, z_c_cov:FLOAT, t0_z_cov:FLOAT, t0_t0_cov:FLOAT, t0_x0_cov:FLOAT, t0_x1_cov:FLOAT, t0_c_cov:FLOAT, x0_z_cov:FLOAT, x0_t0_cov:FLOAT, x0_x0_cov:FLOAT, x0_x1_cov:FLOAT, x0_c_cov:FLOAT, x1_z_cov:FLOAT, x1_t0_cov:FLOAT, x1_x0_cov:FLOAT, x1_x1_cov:FLOAT, x1_c_cov:FLOAT, c_z_cov:FLOAT, c_t0_cov:FLOAT, c_x0_cov:FLOAT, c_x1_cov:FLOAT, c_c_cov:FLOAT, plot_lc_bytes:BYTES'
# output_schema = 'candid:INTEGER, chisq:FLOAT, ndof:INTEGER, z:FLOAT, t0:FLOAT, x0:FLOAT, x1:FLOAT, c:FLOAT'  

p4 = beam.Pipeline(options=options)

query = f'SELECT * FROM {PROJECTID}.{input_bq_table}'  # LIMIT 1000'

(p4 | 'Read alert BQ' >> beam.io.Read(beam.io.ReadFromBigQuery(project=PROJECTID,
        use_standard_sql=True, query=query))
    | 'Filter exgal. transients' >> beam.Filter(bhelp.is_transient)
    | 'Salt2 fit' >> beam.ParDo(bhelp.salt2fit())
    | 'Write to BQ' >> beam.io.Write(beam.io.WriteToBigQuery(output_bq_table,
        schema=output_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))
 )

p4.run()  # .wait_until_finish()
