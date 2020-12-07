import os
import logging
from datetime import datetime
import apache_beam as beam
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io import Write, WriteToBigQuery

os.environ['KRB5_CONFIG'] = './config/krb5.conf'

now = datetime.now()
month = f'{now.month:02d}'
day = '01' # f'{now.day:02d}'
year = f'{now.year}'

# gcp resources
PROJECTID = 'ardent-cycling-243415'
dataflow_job_name = f'ztf-consumer-{year}{month}{day}'
beam_bucket = 'ardent-cycling-243415_dataflow-test'
output_bq_table = 'dataflow_test.ztf_alerts'

# Kafka options
ztf_server = 'public2.alerts.ztf.uw.edu:9094'
ztf_principle = 'pitt-reader@KAFKA.SECURE'
ztf_keytab_path = './config/pitt-reader.user.keytab'
ztf_topic = f'ztf_{year}{month}{day}_programid1'
config = {
    'bootstrap.servers': ztf_server,
    'group.id': 'group',
    'session.timeout.ms': 6000,
    'enable.auto.commit': 'False',
    'sasl.kerberos.kinit.cmd': 'kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}',
    'sasl.kerberos.service.name': 'kafka',
    'security.protocol': 'SASL_PLAINTEXT',
    'sasl.mechanisms': 'GSSAPI',
    'auto.offset.reset': 'earliest',
    'sasl.kerberos.principal': ztf_principle,
    'sasl.kerberos.keytab': ztf_keytab_path,
}

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

# Fix schema class
class FixSchema(beam.DoFn):
    def process(self, element):
        # typ = type(element)
        logging.info(f'something happened')
        return [None]


with beam.Pipeline(options=options) as bp:
    output = (
        bp | 'Read Kafka stream' >> ReadFromKafka(
            consumer_config=config,
            topics=[ztf_topic],
            # key_deserializer='org.apache.kafka.common.serialization.StringDeserializer',
            key_deserializer='org.apache.kafka.common.serialization.StringDeserializer',
            value_deserializer='io.confluent.kafka.serializers.KafkaAvroDeserializer',
            max_num_records = 1
            # 'io.confluent.kafka.serializers.KafkaAvroDeserializer'
            # 'org.apache.kafka.common.serialization.ByteArrayDeserializer'
            )
            | 'Fix Schema' >> beam.ParDo(FixSchema())
            # | 'Write to BQ' >> Write(WriteToBigQuery(output_bq_table,
            # schema='SCHEMA_AUTODETECT',
            # create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            # write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))
    )

# bp.run()  # .wait_until_finish()
