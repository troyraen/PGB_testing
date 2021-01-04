# Dataflow job; `ztf_alert_data` Pub/Sub -> BigQuery

Ended up just splitting off the BQ sink from the main Dataflow job into its own job. See [`../beam-workflow/ztf-bq-sink.py`](../beam-workflow/ztf-bq-sink.py)


# Kafka -> BQ connector
- See [`kafka-console-connect.md`](kafka-console-connect.md)
- I never tested it, unsure if it will pull a separate/additional (from the kafka -> PS connector) stream from ZTF.


# Use a Dataflow template to store ZTF alerts in BigQuery
- [Google-provided streaming templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-streaming#cloudpubsubtobigquery)
- [Get started with Google-provided templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates)

Some templates allow a user-defined function (UDF). Examples:
- [Here](https://medium.com/analytics-vidhya/iot-data-pipelines-in-gcp-multiple-ways-part-2-893269d56371)
- [Google Cloud Dataflow Template Pipelines](https://github.com/GoogleCloudPlatform/DataflowTemplates) (bottom of page)

__[Pub/Sub Avro to BigQuery template](https://cloud.google.com/dataflow/docs/guides/templates/provided-streaming#pubsub-avro-to-bigquery)__

```python
#-- create the schema file
# open the pickle file and write it as an avsc
from pathlib import Path
import pickle
import json
import fastavro as fa
from broker.alert_ingestion.gen_valid_schema import _load_Avro

fpkl = 'ztf_v3.3.pkl'
inpath = Path().resolve() / fpkl
with inpath.open('rb') as infile:
    valid_schema = pickle.load(infile)  # dict

fout = 'ztf_v3.3.avsc'
with open(fout, 'w') as fp:
    json.dump(valid_schema, fp,  indent=4)

# upload this file to GCS and get the uri

# sand
# check
sin = fa.schema.load_schema(fout)
def _load_Avro(fin):
    """
    Args:
        fin   (str or file-like) : Path to, or file-like object representing,
                                   alert Avro file

    Returns:
        schema (dict) : schema from the Avro file header.
        data   (list) : list of dicts containing the data from the Avro file.
    """

    is_path = isinstance(fin, str)
    f = open(fin, 'rb') if is_path else fin

    avro_reader = fastavro.reader(f)
    schema = avro_reader.writer_schema
    data = [r for r in avro_reader]

    if is_path:
        f.close()

    return schema, data

fin = '/Users/troyraen/Documents/PGB/PGB_testing/deploy2cloud_Aug2020/ps-to-gcs-CF/ztf_20201224_programid1_1608788610066_trial.avro'
__, data = _load_Avro(fin)
fa.validate(data, sin, raise_errors=False)
# returns false
```

__run the template__
```bash
JOB_NAME=ps-avro-to-bq
REGION_NAME=us-central1
SCHEMA_PATH=gs://ardent-cycling-243415_dataflow-test/schemas/ztf_v3.3.avsc
# source_PS_sub=projects/ardent-cycling-243415/subscriptions/ztf_alert_avro_bucket
source_PS_sub=projects/ardent-cycling-243415/subscriptions/ztf_alert_data_subtest
sink_BQ=ardent-cycling-243415:dataflow_test.ztf_alerts_psavro2bq
sink_BQ_deadletter=projects/ardent-cycling-243415/topics/ztf_bq_deadletter
writeDisposition=WRITE_APPEND
createDisposition=CREATE_NEVER

gcloud beta dataflow flex-template run ${JOB_NAME} \
    --region=${REGION_NAME} \
    --template-file-gcs-location=gs://dataflow-templates/latest/flex/PubSub_Avro_to_BigQuery \
    --parameters \
schemaPath=${SCHEMA_PATH},\
inputSubscription=${source_PS_sub},\
outputTableSpec=${sink_BQ},\
outputTopic=${sink_BQ_deadletter},\
writeDisposition=${writeDisposition},\
createDisposition=${createDisposition}

```

__Pub/Sub to BigQuery Template__
- This fails when using the `ztf_alert_data` topic (see jan 1 job)
- works with `ztf_exgalac_trans` topic

```bash
job_name=ztf-ps-to-bq
source_PS=projects/ardent-cycling-243415/topics/ztf_alert_avro_bucket
sink_BQ=ardent-cycling-243415:dataflow_test.ztf_alerts_psavro2bq
sink_BQ_deadletter=ardent-cycling-243415:dataflow_test.deadletter
stageloc=gs://ardent-cycling-243415_dataflow-test/ztf-ps-to-bq/temp

gcloud dataflow jobs run ${job_name} \
    --gcs-location gs://dataflow-templates-us-central1/latest/PubSub_to_BigQuery \
    --region us-central1 \
    --staging-location ${stageloc} \
    --parameters \
inputTopic=${source_PS},\
outputTableSpec=${sink_BQ},\
outputDeadletterTable=${sink_BQ_deadletter}

```
