# -*- coding: utf-8 -*-
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
dataflow_job_name = 'salt2-vizier'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
input_bq_table = 'ztf_alerts.alerts'
output_bq_table = 'dataflow_test.salt2'
output_schema = 'mjd:FLOAT, flux:FLOAT'  # must match salt2fit() return

# beam options
options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = dataflow_job_name
gcloud_options.project = PROJECTID
gcloud_options.staging_location = f'gs://{beam_bucket}/staging'
gcloud_options.temp_location = f'gs://{beam_bucket}/temp'
worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 50
worker_options.max_num_workers = 2
# worker_options.num_workers = 2
# worker_options.machine_type = 'n1-standard-8'
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'


def modify_data1(element):
    # beam.Map
    # element = {u'corpus_date': 0, u'corpus': u'sonnets', u'word': u'LVII', u'word_count': 1}

    corpus_upper = element['publisher'].upper()
    word_len = len(element['objectId'])

    return {'publisher': corpus_upper,
            'objectId_len': word_len
            }

def salt2fit(alert):
    epochs = alert['prv_candidates'] + [alert['candidate']]
    epoch_dict = bhelp.extract_epochs(epochs)

    return {'mjd': epoch_dict['mjd'],
            'flux': epoch_dict['flux']
            }

p4 = beam.Pipeline(options=options)

query = f'SELECT * FROM {PROJECTID}.{input_bq_table} LIMIT 10'

(p4 | 'read' >> beam.io.Read(beam.io.ReadFromBigQuery(project=PROJECTID,
        use_standard_sql=True, query=query))
    | 'modify' >> beam.Map(salt2fit)
    | 'write' >> beam.io.Write(beam.io.WriteToBigQuery(output_bq_table,
        schema=output_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))
 )

p4.run()  # .wait_until_finish()
