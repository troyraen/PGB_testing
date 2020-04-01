# Set up Google Cloud Function to grab Avro files from GCS bucket and import to BigQuery

__Not yet done:__
- [ ]  check for duplicates in BQ tables.
    - PS has an "at _least_ once" delivery. Only way to check if the data is already in the table prior to uploading is to query the database which could be very expensive. It is recommended to insert duplicates and handle their removal later. See [this post](https://stackoverflow.com/questions/39853782/check-if-data-already-exists-before-inserting-into-bigquery-table-using-python).
- [ ]  unittest: test that datasets, buckets, PS topics, etc. needed by the cloud function exist and have appropriate permissions


- [Java package](#Java)
- [Python function](#Python)
    - [Create module](#create_gcs2BQ)
    - [Test module](#test_gcs2BQ)
    - [Unit test](#unittest)
    - [Install Google Cloud SDK](#gcloudsdk)
- [Create BigQuery Table via file upload (GUI)](#BQupload)
    - Schema headers in the ZTF version 3.3 Avro files do not meet BQ's strict compliance requirements. BQ cannot create (or append to) the table using the original files. The schema in the header must be fixed first.
- [Fix schema header](#header)
    - [use Fastavro to fix the schema and write a new file](#fastavro)
    - [Replace the schema in the `alert_bytes` object directly](#replace_bytes)
    - [Write `alert_bytes` to temporary file and use Fastavro to replace the schema](#tempfile)
    - [Generate the schema from multiple files (based on LSST code)](#lsst)
- [Run PEP8](#pep8)
- [Sandbox](#sand)

__The code resulting from this markdown file is split between the `tjraen/alert_formatting` and `tjraen/gcs2bq` branches of the `mwvgroup/Pitt-Google-Broker` repo.__


<a name="Java"></a>
## Starting with a pre-written (Java) package
<!-- fs -->

_Note: Couldn't get this to work. Don't want to use a Java package anyway.. found some example Python code to try (see below)_

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

<a name="Python"></a>
## Writing my own cloud function (Python)
<!-- fs -->

_Note: This did not work until I reformatted the incoming alerts (see below) so that the schema header is valid under the strict Avro file requirements that BQ requires._

Based on the previous pre-written package and the instructions at [Loading Avro data from Cloud Storage](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-avro). Also using the code at [this repo](https://github.com/GoogleCloudPlatform/solutions-gcs-bq-streaming-functions-python/blob/master/functions/streaming/main.py).

<a name="create_gcs2BQ"></a>
### Creating the `gcs2BQ` module
<!-- fs -->

Using the web interface:
    1. From [Cloud Function](https://console.cloud.google.com/functions/list?project=ardent-cycling-243415), `CREATE FUNCTION`.
    2. Name = `GCS-Avro-to-BigQuery`
    3. Runtime = `Python 3.7`
    4. For the function code in `main.py`, use the instruction and repo links above.

Now put this into a module in `gcs2BQ/main.py`. Module should:
    1. accept the data as input
    2. create a load_job
    3. ~check for duplicates~ Only way to do this is to query the database which could be very expensive. Recommended to insert duplicates and handle their removal later. See [this post](https://stackoverflow.com/questions/39853782/check-if-data-already-exists-before-inserting-into-bigquery-table-using-python).
    4. run the job
    5. handle errors


__Error handling__

Trying `error_result` and `errors` attributes of `load_job` from [this page](https://googleapis.dev/python/bigquery/latest/_modules/google/cloud/bigquery/job.html#LoadJob).

```python
# Put these in main.py

eres = load_job.error_result
if eres is not None:
    log.error(f'{eres}')
else:
    log.info(f'stream_GCS_to_BQ job {load_job.job_id} completed successfully')

eres = load_job.errors
if eres is not None:
    log.error(f'{eres}')
else:
    log.info(f'stream_GCS_to_BQ job {load_job.job_id} completed successfully')

```

Test by uploading a file with an incorrect (non-reformatted) schema. Looking at the GCP log [here](https://console.cloud.google.com/logs/viewer?project=ardent-cycling-243415):
    - With no explicit error handling: get a Traceback error that includes `error message: The Apache Avro library failed to parse the header with the following error: Unexpected type for default value. Expected double, but found null: null`
    - Using `error_result`: get the Traceback error from above, plus an entry that says `Error detected in stream_GCS_to_BQ`.
    - Using `errors`: only get the Traceback error from above.

__Questions__
1. Since the appropriate error is logged automatically after calling `load_job.result()`, do I also need to explicitly log the error?
2. Where is the logging usually recorded (when running code locally)?
3. Where is the logging recorded when running with GCP?
    - These logs seem to be tied in to the GCP Logs... are they also recorded elsewhere?




<!-- fe ### Creating the `gcs2BQ` module -->


<a name="test_gcs2BQ"></a>
### Testing the `gcs2BQ` module
<!-- fs -->

- The module must be named `main.py`.
- See below to install the gcloud SDK.
- Dependencies for a Cloud Function must be specified in a `requirements.txt` file (or packaged with the function) in the same directory as `main.py`. See [this documentation](https://cloud.google.com/functions/docs/writing/specifying-dependencies-python).

From instructions on GCS triggers [here](https://cloud.google.com/functions/docs/calling/storage):

__Deploy the module:__
> To deploy the function with an object finalize trigger, run the following command in the directory that contains the function code:
`gcloud functions deploy stream_GCS_to_BQ --runtime python37 --trigger-resource gcs_avro_to_bigquery_test --trigger-event google.storage.object.finalize`

In response to the prompt `Allow unauthenticated invocations of new function [streaming]? (y/N)?`, I chose `N` and got the following message: `WARNING: Function created with limited-access IAM policy. To enable unauthorized access consider "gcloud alpha functions add-iam-policy-binding streaming --member=allUsers --role=roles/cloudfunctions.invoker"`

__The function is now running.__ Check the status [here](https://console.cloud.google.com/functions/).
<!-- fe ### Testing the `gcs2BQ` module -->


<a name="unittest"></a>
### Running the unit test for the `gcs2BQ` module
<!-- fs -->
```python
from tests import test_gcs_to_bq as gb
g = gb.GCS2BQ_upload() # instantiate the test class
g.test_upload_GCS_to_BQ() # run the test


from broker.alert_ingestion.GCS_to_BQ import main
data = {
                'bucket': 'ardent-cycling-243415_testing_bucket',
                'name': 'ztf_3.3_validschema_1154446891615015011.avro'
        }
context = {}
job_errors = main.stream_GCS_to_BQ(data, context)
```

<!-- fe ### Running the unit test for the `gcs2BQ` module -->


<a name="gcloudsdk"></a>
### Installing Google Cloud SDK
<!-- fs -->
Need to install the Google Cloud SDK for the command line (currently installed dependencies from `requirements.txt` are Python-specific).

- [Quickstart and how-to guides](https://cloud.google.com/sdk/docs/quickstarts) (see side panel)
- [Manual download and install](https://cloud.google.com/sdk/install)
- [Conda install](https://anaconda.org/conda-forge/google-cloud-sdk)

Trying the Conda install
```bash
pgbenv
conda install -c conda-forge google-cloud-sdk
gcloud components update
```

This works, however I can't figure out who actually developed the package. It _seems_ to be an official Google package (based on links listed on the webpage and those provided in the message printed to the screen when running `gcloud components update`). However the Conda install option is not listed in any official documentation (i.e. quickstart guides listed above).

Now follow the instructions [here](https://cloud.google.com/sdk/docs/quickstart-macos) to initialize.
```bash
gcloud init --console-only
# follow the onscreen prompts
```

Helpful output from the initialization:
> Created a default .boto configuration file at [/Users/troyraen/.boto]. See this file and
> [https://cloud.google.com/storage/docs/gsutil/commands/config] for more
> information about configuring Google Cloud Storage.
> Your Google Cloud SDK is configured and ready to use!
>
> * Commands that require authentication will use troy.raen.pitt@gmail.com by default
> * Commands will reference project `ardent-cycling-243415` by default
> * Compute Engine commands will use region `us-east1` by default
> * Compute Engine commands will use zone `us-east1-b` by default
>
> Run `gcloud help config` to learn how to change individual settings
>
> This gcloud configuration is called [default]. You can create additional configurations if you work with multiple accounts and/or projects.
> Run `gcloud topic configurations` to learn more.
>
> Some things to try next:
>
> * Run `gcloud --help` to see the Cloud Platform services you can interact with. And run `gcloud help COMMAND` to get help on any gcloud command.
> * Run `gcloud topic --help` to learn about advanced features of the SDK like arg files and output formatting

<!-- fe ### Installing Google Cloud SDK -->

<!-- fe ## Writing my own cloud function -->


<a name="BQupload"></a>
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

~__I think the problem is in the `"default": null` encoding, where `null` is not quoted and I think it should be.__~
__See email from Eric Bellm. Problem seems to be that the default value (which should be null) needs to come first in the definition.__

<!-- fe ## Trying to create a BQ table via direct upload of an Avro file -->

<a name="header"></a>
# Fix schema header idiosyncrasies
<!-- fs -->
~This fix is going in the `alert_ingestion.format_alerts` module which will be called by the `consume` module.~ Module `alert_ingestion.format_alerts` is unnecessary and has been deleted. Instead, generate a valid schema once (per survey/version) using Fastavro and write it to a pickle file. The fixing of individual alerts is then handled directly in `consume`.

<a name="fastavro"></a>
## Fix using Fastavro (outside broker environment)
<!-- fs -->
THIS WORKS AND BQ CAN AUTOMATICALLY CREATE A TABLE FROM IT

```python
# in repo/broker dir:
import fastavro

# get data and schema from file
def load_data():
    path = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
    with open(path, 'rb') as f:
        avro_reader = fastavro.reader(f)
        schema = avro_reader.writer_schema
        for r in avro_reader:
            data = r
            break
    return schema, data
# correct the schema
def reverse_types_if_default_is_null(field):
    if isinstance(field['type'],list):

        try:
            if field['default'] is None: # default is None -> reverse the list
                new_types = field['type'][::-1]
            else: # default is something other than null -> leave list unchanged
                new_types = field['type']
        except KeyError: # default not specified -> reverse the list
            new_types = field['type'][::-1]

        field['type'] = new_types

    return field

schema, data = load_data()
for l1, level1_field in enumerate(schema['fields']):
    # level1_field is a dict

    schema['fields'][l1] = reverse_types_if_default_is_null(level1_field)

    # if isinstance(level1_field['type'],dict):
    if level1_field['name'] == 'candidate':
        for l2, level2_field in enumerate(level1_field['type']['fields']):
            schema['fields'][l1]['type']['fields'][l2] = reverse_types_if_default_is_null(level2_field)

    if level1_field['name'] == 'prv_candidates':
        print('prv')
        # print(level1_field['type'])
        for l2, level2_field in enumerate(level1_field['type'][1]['items']['fields']):
            # print(level2_field.keys())
            # print(level2_field['type'])
            schema['fields'][l1]['type'][1]['items']['fields'][l2] = reverse_types_if_default_is_null(level2_field)

# write the new file
newpath = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(newpath, 'wb') as out:
    fastavro.writer(out, schema, [data])

# THIS WORKS AND BQ CAN AUTOMATICALLY CREATE A TABLE FROM IT
```
<!-- fe ## Fix using Fastavro -->

Write the valid schema to a file so that we can use it to replace all version 3.3 schema headers.

## Test module in PGB_version
<!-- fs -->
```python
import gen_valid_schema as gvs

fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/ztf_v3_3_schema.bytes'

# schema, data = gvs.load_Avro(fin)
schema = gvs.fix_schema(fin, fout, survey='ZTF', version=3.3)

with open(fout, 'rb') as f:
    sch = f.read()

```
<!-- fe ## Test module in PGB_version -->

<a name="replace_bytes"></a>
## Test module in PGB repo/broker/alert_ingestion
<!-- fs -->
Generate the valid schema file and use it to replace the schema header directly in the `alert_bytes` object.

THIS DOES NOT WORK. The bytes object seems to be written in a way that encodes header information outside the human readable schema so that replacing the human readable parts breaks the encoding. Instead, use fastavro (see [next section](#tempfile))

```python
### Generate the schema bytes files
# navigate to repo/broker/alert_ingestion/valid_schemas

# Generate the file holding the valid 3.3 schema.
import gen_valid_schema as gvs

fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
fout_stub = 'ztf_v3_3'
schema = gvs.fix_schema(fin, fout_stub, survey='ZTF', version=3.3)


### Test the schema replacement on a bytes object
# navigate to the top level repo directory
from broker.alert_ingestion import format_alerts as fa

fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
with open(fin, 'rb') as f:
    alert_bytes = f.read()
ab = fa.format_alert_schema(alert_bytes, survey='ztf', version=3.3)
ab == alert_bytes # returns True
## THIS DOES NOT WORK.
## THE SCHEMA IN alert_bytes IS DIFFERENT FROM THE ONE IN old_bytes GENERATED USING fastavro. Need to generate the original bytes file from the alert_bytes directly instead of using fastavro.
# print alert_bytes to the terminal, copy and paste the schema portion to the old_bytes file.

# read the old and new schemas from file
finOG = 'broker/alert_ingestion/valid_schemas/ztf_v3_3_original.bytes'
with open(finOG, 'rb') as f:
    old_bytes = f.read()
    old_bytes = old_bytes.strip(b'\n')
finVAL = 'broker/alert_ingestion/valid_schemas/ztf_v3_3_valid.bytes'
with open(finVAL, 'rb') as f:
    new_bytes = f.read()
    new_bytes = new_bytes.strip(b'\n')
alert_bytes.find(old_bytes) # returns a valid index (26)
ab = re.sub(old_bytes, new_bytes, alert_bytes)
ab == alert_bytes # returns True... previous line DOES NOT WORK!
ab = alert_bytes.replace(old_bytes,new_bytes)
ab == alert_bytes # returns False... THIS WORKS!

## Change format_alerts and run the previous test again
ab == alert_bytes # returns False, so this seems to work

## Now try writing the corrected alert_bytes to file and uploading to BQ
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'wb') as f:
    f.write(ab)
# THIS DOES NOT WORK
# When uploading to BQ I get the following error:
    # Error while reading data, error message: The Apache Avro library failed to parse the header with the following error: Cannot have a string of negative length: -59

## Make sure I can read Avro file -> bytes object, change nothing, write the bytes object to file, upload to BQ
# Use the Avro file that I know works with BQ
fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new_WORKS.avro'
with open(fin, 'rb') as f:
    alert_bytes = f.read()
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'wb') as f:
    f.write(alert_bytes)
# THIS WORKS
# Now try replacing one item in the file to see if the find and replace action is causing the problem.
new, old = b'["float", "null"]', b'["null", "float"]',
ab = alert_bytes.replace(old,new) # switch these
ab == alert_bytes # returns False
ab = alert_bytes.replace(new,old) # switch them back so the schema is still valid
ab == alert_bytes # returns True
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'wb') as f:
    f.write(ab)
# THIS WORKS



## Try converting old_bytes to a dict and running it through the gen_valid_schema module
import ast
str = old_bytes.decode("UTF-8")
dic = ast.literal_eval(str)
# THIS DOESN'T WORK
# try loading the schema as a regular string
finOG = 'broker/alert_ingestion/valid_schemas/ztf_v3_3_original.bytes'
with open(finOG, 'r') as f:
    old_bytes = f.read()
    old_bytes = old_bytes.strip('\n')
dic = ast.literal_eval(old_bytes)
# THIS DOESN'T WORK, CAN'T LOAD THE BYTES STRING TO A DICT


## Try replacing each substring in the bytes object directly
fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
with open(fin, 'rb') as f:
    alert_bytes = f.read()

replace_dict = {
        ### fix fields that have a null default
        ## simple fields
        b'["float", "null"]': b'["null", "float"]',
        b'["string", "null"]': b'["null", "string"]',
        b'["long", "null"]': b'["null", "long"]',
        b'["int", "null"]': b'["null", "int"]',
        b'["double", "null"]': b'["null", "double"]',
        ## more complex fields
        b'["ztf.alert.cutout", "null"]': b'["null", "ztf.alert.cutout"]',

        # b'[{"type": "array", "items": "ztf.alert.prv_candidate"}, "null" ]': \
        #     b'["null", {"type": "array", "items": "ztf.alert.prv_candidate"}]',

        b'[{"type": "record", "version": "3.3", "name": "cutout", "namespace": "ztf.alert", "fields": [{"type": "string", "name": "fileName"}, {"type": "bytes", "name": "stampData", "doc": "fits.gz"}], "doc": "avro alert schema"}, "null"]': \
            b'["null", {"type": "record", "version": "3.3", "name": "cutout", "namespace": "ztf.alert", "fields": [{"type": "string", "name": "fileName"}, {"type": "bytes", "name": "stampData", "doc": "fits.gz"}], "doc": "avro alert schema"}]',

        ## very comlex prv_candidates field
        # add null to beginning of list
        b'[{"type": "array", "items": {"type": "record", "version": "3.3", "name": "prv_candidate",': \
            b'["null", {"type": "array", "items": {"type": "record", "version": "3.3", "name": "prv_candidate",',
        # remove null from end of list
        b', "null"], "name": "prv_candidates"': b'], "name": "prv_candidates"',

        ### revert fields that have a default other than null
        b'"type": ["null", "int"], "name": "tooflag", "default": 0': \
            b'"type": ["int", "null"], "name": "tooflag", "default": 0',
    }

ab = alert_bytes[:]
for old, new in replace_dict.items():
    print(ab.find(old))
    ab = ab.replace(old, new)
ab == alert_bytes # returns FALSE, so this seems to work
## Now try writing the corrected alert_bytes to file and uploading to BQ
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'wb') as f:
    f.write(ab)
# THIS DOES NOT WORK. Get the following error when uploading to BQ
    # Error while reading data, error message: The Apache Avro library failed to read data with the following error: vector

## Check the data output in ab and alert_bytes
# manually print these to the terminal and save to file
f1 = '/Users/troyraen/Documents/PGB/PGB_testing/_avro2BQ/ab_data.txt'
with open(f1, 'rb') as f:
    ab_data = f.read()
f2 = '/Users/troyraen/Documents/PGB/PGB_testing/_avro2BQ/alert_bytes_data.txt'
with open(f2, 'rb') as f:
    alert_bytes_data = f.read()
alert_bytes_data == ab_data # RETURNS True. THE SUBSTRING SUBSTITUTION IS NOT CHANGING THE DATA

## Check the find and replace action again, this time actually change some data
fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new_WORKS.avro'
with open(fin, 'rb') as f:
    alert_bytes = f.read()
# Try replacing something trivial
old, new = b'stampData', b'stampDat1'
ab = alert_bytes.replace(old,new) # switch these
ab == alert_bytes # returns False
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'wb') as f:
    f.write(ab)
# THIS WORKS
# Try changing the length of a string
old, new = b'stampData', b'stampDat'
ab = alert_bytes.replace(old,new) # switch these
ab == alert_bytes # returns False
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'wb') as f:
    f.write(ab)
# THIS DOES NOT WORK. BQ upload returns the following error:
    # Error while reading data, error message: The Apache Avro library failed to parse the header with the following error: Cannot have bytes of negative length: -69427866


## Check that fastavro can load the file
import fastavro
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(fout, 'rb') as f:
    avro_reader = fastavro.reader(f)
    schema = avro_reader.writer_schema
    for r in avro_reader:
        data = r
        break
# THIS DOES NOT WORK. It fails at the line `avro_reader = fastavro.reader(f)` eith the error
    # VUnicodeDecodeError: 'utf-8' codec can't decode byte 0xe5 in position 1: invalid continuation byte


# Try reading fout back in and reversing the above change
with open(fout, 'rb') as f:
    alert_bytes = f.read()
ab = alert_bytes.replace(new,old) # switch these back
ab == alert_bytes # returns False
with open(fout, 'wb') as f:
    f.write(ab)
# THIS WORKS

```
<!-- fe ## Test module in PGB repo/broker/alert_ingestion -->

<a name="tempfile"></a>
## Write `alert_bytes` to temporary file and use Fastavro to replace the schema
<!-- fs -->
High level logic is the following:
1. write the `alert_bytes` object to a temporary file
2. read it in with fastavro
3. write a new temporary file with the alert packet data and a valid schema
4. read that file back in to a bytes object and dump to GCS

This will be integrated into the `consume` module which already does items 1 and 4.

```python
from tempfile import SpooledTemporaryFile
# from tempfile import NamedTemporaryFile
import fastavro
# import json
import pickle

from broker.alert_ingestion.valid_schemas import gen_valid_schema as gvs

fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
fvalidsch = '/Users/troyraen/Documents/PGB/repo/broker/alert_ingestion/valid_schemas/ztf_v3_3_valid.pkl'
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'

# generate a file containing the valid schema such that it can be read back in as a dict
schema, data = gvs._load_Avro(fin) # load the file
valid_schema = gvs._fix_schema_ZTF_v3_3(schema) # get the corrected schema
with open(fvalidsch, 'wb') as file:
    pickle.dump(valid_schema,file) # write the dict to a pkl file
with open(fvalidsch, 'rb') as file:
    schema_from_file = pickle.load(file) # read the dict back in to check last. THIS WORKS

# get alert_bytes object
with open(fin, 'rb') as f:
    alert_bytes = f.read()

# function that fixes the schema in the temp_file
def fix_schema(temp_file):
    # load the file with fastavro
    avro_reader = fastavro.reader(temp_file)
    schema = avro_reader.writer_schema
    for r in avro_reader:
        data = r
        break
    # avro_reader = fastavro.reader(temp_file, reader_schema=valid_schema)

    with open(fvalidsch, 'rb') as file: # get the corrected schema
        valid_schema = pickle.load(file)

    # with SpooledTemporaryFile(max_size=max_alert_packet_size, mode='w+b') as new_temp_file:
        # fastavro.writer(new_temp_file, valid_schema, [data])
        # temp_file.seek(0)
        # temp_file = new_temp_file.copy()
    # THIS DOES NOT WORK, gives error:
        # AttributeError: 'SpooledTemporaryFile' object has no attribute 'seekable'
    # with NamedTemporaryFile(mode='w+b') as new_temp_file:
        # fastavro.writer(... use code from above
    # THIS WORKS, but we cannot copy the NamedTemporaryFile to a SpooledTemporaryFile and we want to use the SpooledTemporaryFile object. Solution is to modify the TempAlertFile class to include a `seekable` attribute.
    temp_file.seek(0)
    fastavro.writer(temp_file, valid_schema, [data])
        # temp_file.seek(0)
        # temp_file = new_temp_file.copy()

    return temp_file

# this class is from `consume.py`, and we have added the `seekable` attribute so that fastavro can write to it
class TempAlertFile(SpooledTemporaryFile):
    """Subclass of SpooledTemporaryFile that is tied into the log
    Log warning is issued when file rolls over onto disk.
    """
    def rollover(self) -> None:
        """Move contents of the spooled file from memory onto disk"""
        log.warning(f'Alert size exceeded max memory size: {self._max_size}')
        super().rollover()
    @property
    def readable(self):
        return self._file.readable
    @property
    def writable(self):
        return self._file.writable
    @property
    def seekable(self): # this is necessary so that fastavro can write to the file
        return self._file.seekable

# generate a temporary file and call the function to fix the schema
max_alert_packet_size = 150000
with TempAlertFile(max_size=max_alert_packet_size, mode='w+b') as temp_file:
    # with NamedTemporaryFile(mode='w+b') as temp_file:
    temp_file.write(alert_bytes)
    temp_file.seek(0)

    temp_file = fix_schema(temp_file)

    # test that this worked by gettin the data and schema so can close file and then write a corrected Avro file to disk (then upload to BQ to see if it works)
    temp_file.seek(0)
    avro_reader = fastavro.reader(temp_file)
    schema = avro_reader.writer_schema
    for r in avro_reader:
        data = r
        break

with open(fout, 'wb') as f:
    fastavro.writer(f, schema, [data])

# THIS WORKS! meaning it generates a valid Avro file that BQ can successfully create a table from

```

Port this into the broker. In `consume.py`, the function `upload_bytes_to_bucket` has this snippet:
```python
with TempAlertFile(max_size=max_alert_packet_size, mode='w+b') as temp_file:
            temp_file.write(data)
            temp_file.seek(0)
            blob.upload_from_file(temp_file)
```
Between the `seek` and `upload_from_file`, need to insert a function call, where the function does the following:
- get the survey and version
- load the valid schema from file
- use fastavro to:
    - read the temp_file in (to get the data)
    - write the valid schema and the data back out to the temp_file

Test the function outside of `consume`:
```python
import pickle
import fastavro
from tempfile import SpooledTemporaryFile
def fix_schema(temp_file: TempAlertFile, survey: str, version: float) -> None:
    # get the corrected schema, if it exists
    try:
        f = f'/Users/troyraen/Documents/PGB/repo/broker/alert_ingestion/valid_schemas/{survey}_v{version}.pkl'
        with open(f, 'rb') as file:
            valid_schema = pickle.load(file)

    except FileNotFoundError:
        return

    # load the file and get the data with fastavro
    data = []
    temp_file.seek(0)
    for r in fastavro.reader(temp_file):
        data.append(r)

    # write the corrected file
    temp_file.seek(0)
    fastavro.writer(temp_file, valid_schema, data)
    temp_file.truncate() # truncate at current position (removes leftover data)

    return

fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
fout = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'

with open(fin, 'rb') as f:
    alert_bytes = f.read()

# from broker.alert_ingestion import format_alerts as fa
# survey = fa.guess_schema_survey(alert_bytes)
# version = fa.guess_schema_version(alert_bytes)
survey, version = 'ztf', 3.3
max_alert_packet_size = 150000
with TempAlertFile(max_size=max_alert_packet_size, mode='w+b') as temp_file:
    temp_file.write(alert_bytes)
    temp_file.seek(0)
    fix_schema(temp_file, survey, version)

    # test that this worked by gettin the data and schema so can close file and then write a corrected Avro file to disk (then upload to BQ to see if it works)
    temp_file.seek(0)
    avro_reader = fastavro.reader(temp_file)
    schema = avro_reader.writer_schema
    for r in avro_reader:
        data = r
        break

with open(fout, 'wb') as f:
    fastavro.writer(f, schema, [data])
# THIS WORKS! meaning it generates a valid Avro file that BQ can successfully create a table from
```

Test `gen_valid_schema`. It should take in the Avro file path and write the schema dict as a pickle file.
```python
from broker.alert_ingestion.valid_schemas import gen_valid_schema as gvs
fin = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
survey, version = 'ztf', 3.3
valid_schema = gvs.write_valid_schema(fin, survey, version)
```
This works.

<!-- fe ## Write `alert_bytes` to temporary file and use Fastavro to replace the schema -->

<a name="writetests"></a>
## Write tests for the fix
<!-- fs -->
Hacking to create the `test_format_alerts` module in the tests directory of the repo.

```python
from pathlib import Path
import os

test_alerts_dir = Path('/Users/troyraen/Documents/PGB/repo/tests/test_alerts')

def get_survey_and_schema(filename: str) -> (str, float):
    f = filename.split('_')
    survey = f[0]
    version = float('.'.join(f[1].strip('v').split('-')))
    return (survey, version)

def _load_Avro(fin):
    f = open(fin, 'rb') if type(fin)==str else fin

    avro_reader = fastavro.reader(f)
    schema = avro_reader.writer_schema
    data = []
    for r in avro_reader:
        data.append(r)

    if type(fin)==str: f.close()

    return schema, data

# def test_data_unchanged():
max_size = 150000
def test_data_unchanged():
    for path in test_alerts_dir.glob('*.avro'):
        __, original_data = _load_Avro(str(path))

        survey, version = get_survey_and_schema(path.name)
        max_size = 150000
        with consume.TempAlertFile(max_size=max_size, mode='w+b') as temp_file:
            with open(path, 'rb') as f:
                temp_file.write(f.read())
            temp_file.seek(0)
            consume.GCSKafkaConsumer.fix_schema(temp_file, survey, version)
            temp_file.seek(0)
            __, corrected_data = _load_Avro(temp_file)

        print(original_data == corrected_data)

```

Test the module
```python
from tests import test_format_alerts as tfa

# test that formatting leaves data unchanged
a = tfa.AlertFormattingDataUnchanged()
a.test_data_unchanged_ztf_3_3()
# THIS WORKS

# test that reformatted file can be uploaded to BQ
a = tfa.AlertFormattedForBigQuery()
a.setUpClass()
a.test_BQupload_ztf_3_3()
# THIS WORKS
# Now trying to make this break:
# using a dataset that does not exist gives
    # NotFound: 404 POST https://www.googleapis.com/upload/bigquery/v2/projects/ardent-cycling-243415/jobs?uploadType=resumable: Not found: Dataset ardent-cycling-243415:test_AlertFormattedForBigQuery1
# uploading a ZTFv3.3 file without reformatting it first gives
    # BadRequest: 400 Error while reading data, error message: The Apache Avro library failed to parse the header with the following error: Unexpected type for default value. Expected double, but found null: null


```

<!-- fe ## Write tests for the fix -->

<a name="lsst"></a>
## USE LSST functions to correct the schema (Fix schema header idiosyncrasies)
<!-- fs -->

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

<!-- fe # USE LSST functions to correct the schema -->
<!-- fe # Fix schema header idiosyncrasies -->


<a name="pep8"></a>
# Run PEP8
<!-- fs -->
This has been renamed to `pycodestyle`.

```bash
pgbrepo
pgbenv
pip install pycodestyle

cd broker/alert_ingestion
pycodestyle consume.py
pycodestyle gen_valid_schema.py
cd GCS_to_BQ
pycodestyle main.py

cd.
cd.
cd tests
pycodestyle test_format_alerts.py
pycodestyle test_gcs_to_bq.py

```
<!-- fe # Run PEP8 -->


<a name="sand"></a>
# Sand
<!-- fs -->
```python
# from fastavro import writer, parse_schema
# parsed_schema = parse_schema(schema)

# get a ZTF avro file as a bytes object to test on
path = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011.avro'
with open(path, 'rb') as f:
    fbyt = f.read()






# types that need to be replaced:
from collections import OrderedDict as OD
replace_dict = OD({
    ### fix fields that have a null default
    ## simple fields
    b'["float", "null"]': b'["null", "float"]',
    b'["string", "null"]': b'["null", "string"]',
    b'["long", "null"]': b'["null", "long"]',
    b'["int", "null"]': b'["null", "int"]',
    b'["double", "null"]': b'["null", "double"]',
    ## more complex fields
    b'["ztf.alert.cutout", "null"]': b'["null", "ztf.alert.cutout"]',

    # b'[{"type": "array", "items": "ztf.alert.prv_candidate"}, "null" ]': \
    #     b'["null", {"type": "array", "items": "ztf.alert.prv_candidate"}]',

    b'[{"type": "record", "version": "3.3", "name": "cutout", "namespace": "ztf.alert", "fields": [{"type": "string", "name": "fileName"}, {"type": "bytes", "name": "stampData", "doc": "fits.gz"}], "doc": "avro alert schema"}, "null"]': \
        b'["null", {"type": "record", "version": "3.3", "name": "cutout", "namespace": "ztf.alert", "fields": [{"type": "string", "name": "fileName"}, {"type": "bytes", "name": "stampData", "doc": "fits.gz"}], "doc": "avro alert schema"}]',

    ## very comlex prv_candidates field
    # add null to beginning of list
    b'[{"type": "array", "items": {"type": "record", "version": "3.3", "name": "prv_candidate",': \
        b'["null", {"type": "array", "items": {"type": "record", "version": "3.3", "name": "prv_candidate",',
    # remove null from end of list
    b', "null"], "name": "prv_candidates"': b'], "name": "prv_candidates"',

    ### fix fields that have a default other than null
    b'"type": ["null", "int"], "name": "tooflag", "default": 0': \
        b'"type": ["int", "null"], "name": "tooflag", "default": 0',
})

fbytnew = fbyt[:]
for old, new in replace_dict.items():
    print(fbytnew.find(old))
    fbytnew = fbytnew.replace(old, new)

newpath = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.avro'
with open(newpath, 'wb') as f:
    f.write(fbytnew)
# write the new file as a string so I can read it
# newpaths = '/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new.txt'
# with open(newpaths, 'w') as f:
#     f.write(fbyt)

# read the new file
with open(newpath, 'rb') as f:
    fbyt = f.read()





# SAND
import fastavro

with open(path, 'rb') as f:
    avro_reader = fastavro.reader(f)
    for r in avro_reader:
        record = r

itype = fbyt.find(b'"type": [')
fsplt = fbyt.split(b'"type": [',1)

import re # regex

fmatch = re.match(b'"type": [', fbyt)

```
<!-- fe # Sand -->
