# manually load files from GCS into BQ by filename

import sys
from google.cloud import logging
from google.cloud import bigquery

logging_client = logging.Client()
log_name = 'troy-manual-ops'
logger = logging_client.logger(log_name)


PROJECT_ID = 'ardent-cycling-243415'
BQ = bigquery.Client()

ztf_bucket = '_'.join([PROJECT_ID, 'ztf_alert_avro_bucket'])
BQ_DATASET, BQ_TABLE = 'ztf_alerts', 'alerts'
BQ_TABLE_ID = '.'.join([PROJECT_ID, BQ_DATASET, BQ_TABLE])

def GCS2BQ(file_name):
    nrowsOG = BQ.get_table(BQ_TABLE_ID).num_rows

    uri = f'gs://{ztf_bucket}/{file_name}'

    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.source_format = bigquery.SourceFormat.AVRO

    load_job = BQ.load_table_from_uri(uri, BQ_TABLE_ID, job_config=job_config)
    load_job.result()  # Waits for the job to complete.

    nrows = BQ.get_table(BQ_TABLE_ID).num_rows
    msg = ( f'Loaded avro files matching {file_name} '
            f'from bucket {ztf_bucket} '
            f'to table {BQ_TABLE_ID}. '
            f'Number of rows in table increased by {nrows-nrowsOG} '
            f'(from {nrowsOG} to {nrows}).'
            )
    logger.log_text(msg, severity='NOTICE')
    print(msg)

# run the function
GCS2BQ(sys.argv[1])