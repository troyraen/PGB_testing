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

PROJECTID = 'ardent-cycling-243415'

options = beam.options.pipeline_options.PipelineOptions()
gcloud_options = options.view_as(beam.options.pipeline_options.GoogleCloudOptions)
gcloud_options.job_name = 'dataflow-uppercase'
gcloud_options.project = PROJECTID

bucket = 'ardent-cycling-243415_dataflow-test'
gcloud_options.staging_location = f'gs://{bucket}/staging'
gcloud_options.temp_location = f'gs://{bucket}/temp'

worker_options = options.view_as(beam.options.pipeline_options.WorkerOptions)
worker_options.disk_size_gb = 25
worker_options.max_num_workers = 2
# worker_options.num_workers = 2
# worker_options.machine_type = 'n1-standard-8'


options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'


def modify_data1(element):
    # beam.Map
    # element = {u'corpus_date': 0, u'corpus': u'sonnets', u'word': u'LVII', u'word_count': 1}

    corpus_upper = element['corpus'].upper()
    word_len = len(element['word'])

    return {'corpus_upper': corpus_upper,
            'word_len': word_len
            }


p4 = beam.Pipeline(options=options)

query = 'SELECT * FROM [bigquery-public-data.samples.shakespeare] LIMIT 10'
(p4 | 'read' >> beam.io.Read(beam.io.ReadFromBigQuery(project=PROJECTID,
        use_standard_sql=False, query=query))
    | 'modify' >> beam.Map(modify_data1)
    | 'write' >> beam.io.Write(beam.io.WriteToBigQuery(
        'dataflow_test.uppercase',
        schema='corpus_upper:STRING, word_len:INTEGER',
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))
 )

p4.run()  # .wait_until_finish()
