import apache_beam as beam
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io import Write, WriteToBigQuery
from apache_beam.io.BigQueryDisposition import CREATE_IF_NEEDED, WRITE_TRUNCATE

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = 'rubin-alert-stream-simulator'
beam_bucket = 'ardent-cycling-243415_rubin-sims'
# input_bq_table = 'rubin_sims.alerts'
output_bq_table = 'rubin_sims.alerts'

# Kafka options
bootstrap_servers = 'localhost:9092'
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
worker_options.max_num_workers = 6
# worker_options.num_workers = 2
# worker_options.machine_type = 'n1-standard-8'
options.view_as(beam.options.pipeline_options.StandardOptions).runner = 'DataflowRunner'

with beam.Pipeline(options=options) as bp:
    output = (
        bp | 'Read Kafka stream' >> ReadFromKafka(
            consumer_config={'bootstrap.servers': bootstrap_servers},
            topics=[topic])
            | 'Write to BQ' >> Write(WriteToBigQuery(output_bq_table,
            schema=output_schema,
            create_disposition=CREATE_IF_NEEDED,
            write_disposition=WRITE_TRUNCATE))
    )

# bp.run()  # .wait_until_finish()
