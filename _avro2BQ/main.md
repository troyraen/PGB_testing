# Set up Google Cloud Function to grab Avro files from GCS bucket and import to BigQuery

## Starting with a pre-written function
<!-- fs -->
[AVRO/CSV Import to BigQuery from Cloud Storage with a Cloud Function](https://cloud.google.com/community/tutorials/cloud-functions-avro-import-bq)

> This tutorial demonstrates using a Cloud Function to create a serverless cron scheduled import for data management or data science workflows. One such use case would be when a third party provides data uploaded to a Cloud Storage bucket on a regular basis in a GCP project. Instead of manually importing the CSV or AVRO to BigQuery each day, you can use a cloud function with a trigger on object.finalize on a set bucket. This way, whenever a CSV or an AVRO file is uploaded to that bucket, the function imports the file to a new BigQuery table to the specified dataset.

In [BigQuery UI](https://console.cloud.google.com/bigquery?project=ardent-cycling-243415&cloudshell=true), choose `ardent-cycling-243415` then `CREATE DATASET` called `GCS_Avro_to_BigQuery_test`.

In [Storage -> Storage -> Browser](https://console.cloud.google.com/storage/browser?cloudshell=true&project=ardent-cycling-243415), `CREATE BUCKET` called `gcs_avro_to_bigquery_test`. Accept default options except for `Access control` where I chose `Uniform`.

In the GCS Cloud Shell:
```bash
wget https://github.com/GoogleCloudPlatform/community/raw/master/tutorials/cloud-functions-avro-import-bq/gcf_gcs.zip
unzip gcf_gcs.zip
nano index.js
# set projectId = ardent-cycling-243415
# set datasetId = GCS_Avro_to_BigQuery_test
nano install.sh
# replace `avro-import-source` with `gcs_avro_to_bigquery_test`
# set the runtime flag `--runtime nodejs8`
./install.sh
# select yes to `Allow unauthenticated invocations of new function [ToBigQuery_Stage]?`
```

Verify the function is running in the [GCP Console](https://console.cloud.google.com/functions/?_ga=2.203192401.1394225696.1583109582-1293827000.1581697415)

Upload an AVRO file to the source Cloud Storage bucket specified in `install.sh`

__Gives errors.__ First is `TypeError: Cannot read property 'bucket' of undefined at exports.ToBigQuery_Stage (index.js:14)`. Based on the [solution to this error](https://medium.com/p/db357cc799ca/responses/show), I tried changing `event.data` to `event` in index.js. This gave two other errors: `TypeError: callback is not a function` and `ERROR: { ApiError: Error while reading data, error message: The Apache Avro library failed to parse the header with the following error: Unexpected type for default value. Expected double, but found null: null`

Now trying to write my own function.
<!-- fe ## Starting with a pre-written function -->

## Writing my own cloud function
<!-- fs -->
Based on the previous pre-written function and the instructions at [Loading Avro data from Cloud Storage](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-avro)

From [Cloud Function](https://console.cloud.google.com/functions/list?project=ardent-cycling-243415), `CREATE FUNCTION`.

Name = `GCS-Avro-to-BigQuery`

Runtime = `Python 3.7`

For the function code in `main.py`, start with the code at [this repo](https://github.com/GoogleCloudPlatform/solutions-gcs-bq-streaming-functions-python/blob/master/functions/streaming/main.py) and modify to the following:
```python
from google.cloud import bigquery
# from google.cloud import storage
PROJECT_ID = os.getenv('GCP_PROJECT')
BQ_DATASET = 'GCS_Avro_to_BigQuery_test'
BQ_TABLE = 'test_table_1'
# CS = storage.Client()
BQ = bigquery.Client()

def streaming(data, context):
    '''This function is executed whenever a file is added to Cloud Storage'''
    bucket_name = data['bucket']
    file_name = data['name']

# from https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-avro
    table_ref = BQ.dataset(BQ_DATASET).table(BQ_TABLE)
    job_config = bigquery.LoadJobConfig()
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
    job_config.source_format = bigquery.SourceFormat.AVRO
    uri = f"gs://{bucket_name}/{file_name}"
    load_job = BQ.load_table_from_uri(
        uri, table_ref, job_config=job_config
    )  # API request
    # print("Starting job {}".format(load_job.job_id))

    load_job.result()  # Waits for table load to complete.
    # print("Job finished.")

    # destination_table = BQ.get_table(table_ref)
    # print("Loaded {} rows.".format(destination_table.num_rows))


    # db_ref = DB.document(u'streaming_files/%s' % file_name)
    # if _was_already_ingested(db_ref):
    #     _handle_duplication(db_ref)
    # else:
    try:
        _insert_into_bigquery(bucket_name, file_name)
        _handle_success(db_ref)
    except Exception:
        _handle_error(db_ref)


def _was_already_ingested(db_ref):
    status = db_ref.get()
    return status.exists and status.to_dict()['success']


def _handle_duplication(db_ref):
    dups = [_now()]
    data = db_ref.get().to_dict()
    if 'duplication_attempts' in data:
        dups.extend(data['duplication_attempts'])
    db_ref.update({
        'duplication_attempts': dups
    })
    logging.warn('Duplication attempt streaming file \'%s\'' % db_ref.id)


def _insert_into_bigquery(bucket_name, file_name):
    blob = CS.get_bucket(bucket_name).blob(file_name)
    row = json.loads(blob.download_as_string())
    table = BQ.dataset(BQ_DATASET).table(BQ_TABLE)
    errors = BQ.insert_rows_json(table,
                                 json_rows=[row],
                                 row_ids=[file_name],
                                 retry=retry.Retry(deadline=30))
    if errors != []:
        raise BigQueryError(errors)


def _handle_success(db_ref):
    message = 'File \'%s\' streamed into BigQuery' % db_ref.id
    doc = {
        u'success': True,
        u'when': _now()
    }
    db_ref.set(doc)
    PS.publish(SUCCESS_TOPIC, message.encode('utf-8'), file_name=db_ref.id)
    logging.info(message)


def _handle_error(db_ref):
    message = 'Error streaming file \'%s\'. Cause: %s' % (db_ref.id, traceback.format_exc())
    doc = {
        u'success': False,
        u'error_message': message,
        u'when': _now()
    }
    db_ref.set(doc)
    PS.publish(ERROR_TOPIC, message.encode('utf-8'), file_name=db_ref.id)
    logging.error(message)


def _now():
    return datetime.utcnow().replace(tzinfo=pytz.utc).strftime('%Y-%m-%d %H:%M:%S %Z')


class BigQueryError(Exception):
    '''Exception raised whenever a BigQuery error happened'''

    def __init__(self, errors):
        super().__init__(self._format(errors))
        self.errors = errors

    def _format(self, errors):
        err = []
        for error in errors:
            err.extend(error['errors'])
        return json.dumps(err)
```
<!-- start with the code at [Loading Avro data into a new table](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-avro#loading_avro_data_into_a_new_table) and modify as follows:

```python
from google.cloud import bigquery
client = bigquery.Client()
dataset_id = 'GCS_Avro_to_BigQuery_test'

dataset_ref = client.dataset(dataset_id)
job_config = bigquery.LoadJobConfig()
job_config.source_format = bigquery.SourceFormat.AVRO
uri = "gs://cloud-samples-data/bigquery/us-states/us-states.avro"

load_job = client.load_table_from_uri(
    uri, dataset_ref.table("us_states"), job_config=job_config
)  # API request
print("Starting job {}".format(load_job.job_id))

load_job.result()  # Waits for table load to complete.
print("Job finished.")

destination_table = client.get_table(dataset_ref.table("us_states"))
print("Loaded {} rows.".format(destination_table.num_rows))
``` -->
<!-- fe ## Writing my own cloud function -->

## Trying to create a BQ table via direct upload of an Avro file
<!-- fs -->
Getting the following error:
`Error while reading data, error message: The Apache Avro library failed to parse the header with the following error: Unexpected type for default value. Expected double, but found null: null`

Tried reading one of the Avro files using `fastavro` and everything _seemed_ fine.

Now trying to download newer alerts than the ones I already had on Roy. Downloading from [https://ztf.uw.edu/alerts/public/](https://ztf.uw.edu/alerts/public/).

Getting the same error when using a new alert to manually create a BQ table.

```python
import fastavro as fa
afile = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro' # new ZTF Avro alert

# schema defined here: https://zwickytransientfacility.github.io/ztf-avro-alert/schema.html
# dict taken from https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/schema/alert.avsc
# Note that I had to change `"default": null` to `"default": "null"` in several places.
schema = {
	"namespace": "ztf",
	"type": "record",
	"name": "alert",
	"doc": "avro alert schema for ZTF (www.ztf.caltech.edu)",
	"version": "3.3",
	"fields": [
                {"name": "schemavsn", "type": "string", "doc": "schema version used"},
                {"name": "publisher", "type": "string", "doc": "origin of alert packet"},
		{"name": "objectId", "type": "string", "doc": "object identifier or name"},
		{"name": "candid", "type": "long"},
		{"name": "candidate", "type": "ztf.alert.candidate"},
		{"name": "prv_candidates", "type": [{
				"type": "array",
				"items": "ztf.alert.prv_candidate"}, "null" ], "default": "null"},
		{"name": "cutoutScience", "type": ["ztf.alert.cutout", "null"], "default": "null"},
		{"name": "cutoutTemplate", "type": ["ztf.alert.cutout", "null"], "default": "null"},
		{"name": "cutoutDifference", "type": ["ztf.alert.cutout", "null"], "default": "null"}
			]
}

with open(afile, 'rb') as fo:
    avro_reader = fa.reader(fo)
    for record in avro_reader:
        fa.validate(record,schema)
# This returns `True`, so the data is valid when I supply the schema manually.
```

__I think the problem is in the `"default": null` encoding, where `null` is not quoted and I think it should be.__

<!-- fe ## Trying to create a BQ table via direct upload of an Avro file -->

# USE LSST functions to correct the schema (Fix schema header idiosyncrasies)

This is giving errors related to redefined schema, [see here](https://github.com/lsst-dm/alert_stream/issues/24)

To use this, would still need to fix the ordering of the type lists in the schema files.

```python
from os.path import join as pjoin
import fastavro
from _avro2BQ import LSST_Avro_utils as lau

# build schema
rootdir = '/Users/troyraen/Documents/PGB/PGB_testing/_avro2BQ/schemas'
slst = ['alert','candidate','cutout','prv_candidate']
slst.reverse() # necessary to avoid error
schema_list = []
for s in slst:
    filename = pjoin(rootdir,f'{s}.avsc')
    schema_list.append(lau.load_schema(filename))
# full_schema = resolve_schema(schema_list, root_name='ztf.alert')
full_schema = lau.resolve_schema_definition(schema_list, seen_names=None)

# get data
path = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
with open(path, 'rb') as f:
    for r in fastavro.reader(f):
        data = r
        break

# write file
lau.write_avro_data(data, full_schema)
## this give the error:
    # SchemaParseException: redefined named type: ztf.alert.candidate
newpath = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
fastavro.schemaless_writer(newpath, full_schema, data)
## this gives the same error as above
```
according to this page
https://github.com/lsst-dm/alert_stream/issues/24
newest version(s) of fastavro don't work with nested schemas when a schema is repeated
(as is the case here)


