import logging
import apache_beam as beam
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io import Write, WriteToBigQuery
# from apache_beam.io.BigQueryDisposition import CREATE_IF_NEEDED, WRITE_TRUNCATE

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = 'rubin-sims-raw_alert.value'
beam_bucket = 'ardent-cycling-243415_rubin-sims'
output_bq_table = 'rubin_sims.alerts'

# Kafka options
consumer_config = {'bootstrap.servers': '34.67.113.119:9092',
                   'enable.auto.commit': 'true',
                   'auto.offset.reset': 'earliest'
                }
topic = 'rubin_example_stream'

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
# worker_options.machine_type = 'n1-standard-8'
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'

class log_alert(beam.DoFn):
    def start_batch():
        import lsst.alert.stream.serialization

    def process(self, raw_alert):
        alert = lsst.alert.stream.serialization.deserialize_alert(raw_alert.value)
        # log alert type, alert as string
        logging.info(f'Alert type: {type(alert)}')
        logging.info(f"Alert ID: {alert['alertId']}")

        return None

with beam.Pipeline(options=options) as bp:
    output = (
        bp | 'Read Kafka stream' >> ReadFromKafka(
            consumer_config=consumer_config,
            topics=[topic],
            # key_deserializer='org.apache.kafka.common.serialization.BytesDeserializer',
            # value_deserializer='org.apache.kafka.common.serialization.BytesDeserializer'
            )
            | 'Log alert info' >> beam.ParDo(log_alert())
            # | 'Write to BQ' >> Write(WriteToBigQuery(output_bq_table,
            # schema='SCHEMA_AUTODETECT',
            # create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            # write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))
    )

# bp.run()  # .wait_until_finish()
