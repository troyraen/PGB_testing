- [dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
- [salt2-fits dashboard](https://console.cloud.google.com/monitoring/dashboards/resourceDetail/dataflow_job,project_id:ardent-cycling-243415,region:us-central1,job_name:salt2-fits?project=ardent-cycling-243415&timeDomain=1d)
- [Salt2 BQ table](https://console.cloud.google.com/bigquery?project=ardent-cycling-243415) (ztf_alerts.salt2)
- [Salt2 jpg bucket](https://console.cloud.google.com/storage/browser/ardent-cycling-243415_ztf-sncosmo?project=ardent-cycling-243415&pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22%29%29&prefix=&forceOnObjectsSortingFiltering=false)

# ToC
- Go to [LEFT OFF HERE](#HERE)
- [Salt2](#salt2)
    - [Setup GCP resources](#gcpsetup)
    - [Filter for extragalactic transients](#filtertrans)
    - [Salt2 setup and fit example data](#salt2setup)
    - [Test with some BQ data](#testwithbq)
    - [Run beam pipeline](#runbeam)
- [Xmatch with Vizier](#vizier)


# To Do
- [ ]  create buckets in `gcp_setup.py`

<a name="salt2"></a>
# Salt2
<!-- fs -->

<a name="gcpsetup"></a>
## Setup GCP resources
<!-- fs -->
- [GCS Making data public](https://cloud.google.com/storage/docs/access-control/making-data-public#code-samples_1)
- couldn't find similar, straightforward example for BQ, but I pieced a solution together.

```python
from google.cloud import bigquery, storage
PROJECT_ID = 'ardent-cycling-243415'

### Create buckets
bucket_name = f'{PROJECT_ID}_ztf-sncosmo'
storage_client = storage.Client()
bucket = storage_client.create_bucket(bucket_name)
# bucket = storage_client.get_bucket(bucket_name)
# Set uniform access to bucket (rather than per object permissions)
bucket.iam_configuration.uniform_bucket_level_access_enabled = True
bucket.patch()
# Set bucket to be publicly readable
policy = bucket.get_iam_policy(requested_policy_version=3)
member, role = 'allUsers', 'roles/storage.objectViewer'
policy.bindings.append({"role": role, "members": {member}})
bucket.set_iam_policy(policy)

### BQ tables
# the table is created automatically as long as the dataset exists
dataset_id, table_id = 'ztf_alerts', 'salt2'
bigquery_client = bigquery.Client()
# bigquery_client.create_dataset('dataflow_test', exists_ok=True)
dataset = bigquery_client.get_dataset(dataset_id)
# Set table to be publicly readable
table = bigquery_client.get_table(f'{dataset_id}.{table_id}')
policy = bigquery_client.get_iam_policy(table)
member, role = 'allUsers', 'roles/bigquery.dataViewer'
policy.bindings.append({"role": role, "members": {member}})
bigquery_client.set_iam_policy(table, policy)

```
<!-- fe Setup GCP resources -->


<a name="filtertrans"></a>
## Filter for extragalactic transients
<!-- fs -->
- [Filtering ZTF alerts](https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/notebooks/Filtering_alerts.ipynb)

```python


```

<!-- fe Filter for extragalactic transients -->


<a name="salt2setup"></a>
## Salt2 setup and fit data
<!-- fs -->
- [SALT2: using distant supernovae to improve the use of type Ia supernovae as distance indicators](https://www.aanda.org/articles/aa/pdf/2007/16/aa6930-06.pdf) (Salt2 paper)
- [SNCosmo, Fitting a light curve with Salt2](https://sncosmo.readthedocs.io/en/stable/examples/plot_lc_fit.html)
- [ParDo explanation/example](https://beam.apache.org/documentation/programming-guide/#core-beam-transforms)

```bash
pip install sncosmo
pip install iminuit
pip install matplotlib
```

```python
import sncosmo

data = sncosmo.load_example_data()
# create a model
model = sncosmo.Model(source='salt2')
# run the fit
result, fitted_model = sncosmo.fit_lc(
    data, model,
    ['z', 't0', 'x0', 'x1', 'c'],  # parameters of model to vary
    bounds={'z':(0.3, 0.7)})  # bounds on parameters (if any)

print("Number of chi^2 function calls:", result.ncall)
print("Number of degrees of freedom in fit:", result.ndof)
print("chi^2 value at minimum:", result.chisq)
print("model parameters:", result.param_names)
print("best-fit values:", result.parameters)
print("The result contains the following attributes:\n", result.keys())

sncosmo.plot_lc(data, model=fitted_model, errors=result.errors, fname='figs/fit.png')
```

__Daniel's feedback:__
- t0 has a big impact on quality of fit
    - run a few fits on the data. look at how good of a job it does. if looks fine, leave it. otherwise, _limit to #days +- first datapoint with S/N > 5_
- x0 is an overall scale factor, shouldn't need to bound it
- _x1 and c bounds [-5,5]_
    - normal stretch of Ia [-1,1] but want to accommodate other objects
- if run in to wavelength error out of range (happens in high z), switch to salt2-extended

<!-- fe Salt2 setup and fit data -->


<a name="testwithbq"></a>
## Test with some BQ data
<!-- fs -->
```python
from google.cloud import bigquery
import sncosmo
import custommods.beam_helpers as bhelp

# Get some data
PROJECTID = 'ardent-cycling-243415'
# input_bq_table = 'ztf_alerts.alerts'
input_bq_table = 'dataflow_test.ztf_alerts'
client = bigquery.Client()
query = f'SELECT * FROM {PROJECTID}.{input_bq_table} LIMIT 100'
query_job = client.query(query, project=PROJECTID)  #, job_config=config)

# extract the rows
alertlst = []
for row in query_job:
    alertlst.append(row)

# extract epoch info
epoch_dictlst = []
s2f = bhelp.salt2fit()
for alert in alertlst:
    epoch_dictlst.append(s2f.extract_epochs(alert))
# get one dict with at least 10 epochs
for epoch_dict in epoch_dictlst:
    if len(epoch_dict['mjd']) > 10:
        print(len(epoch_dict['mjd']))
        break
# get astropy table for salt2
epoch_tbl, __ = s2f.format_for_salt2(epoch_dict)

# run the fit
model = sncosmo.Model(source='salt2')
result, fitted_model = sncosmo.fit_lc(
    epoch_tbl, model,
    ['z', 't0', 'x0', 'x1', 'c'],  # parameters of model to vary
    bounds={'z':(0.01, 0.2)},  # https://arxiv.org/pdf/2009.01242.pdf
    )
result['cov_names'] = result['vparam_names']  # cov_names depreciated in favor of vparam_names, but flatten_result() requires it
flatres = sncosmo.flatten_result(result)
# plot results
sncosmo.plot_lc(epoch_tbl, model=fitted_model, errors=result.errors, fname='figs/fitbq.png')

# find a DataQualityError
from sncosmo.fitting import DataQualityError
for epoch_dict in epoch_dictlst:
    epoch_tbl = bhelp.format_for_salt2(epoch_dict)
    try:
        result, fitted_model = sncosmo.fit_lc(
            epoch_tbl, model,
            ['z', 't0', 'x0', 'x1', 'c'],  # parameters of model to vary
            bounds={'z':(0.01, 0.2)},  # https://arxiv.org/pdf/2009.01242.pdf
            )
    except DataQualityError as e:
        dqe = e
        break

# save lc to temp file and upload to bucket
import shutil
from tempfile import NamedTemporaryFile, SpooledTemporaryFile
from google.cloud import storage
storage_client = storage.Client()
beam_bucket = 'ardent-cycling-243415_dataflow-test'
bucket = storage_client.get_bucket(beam_bucket)

candid = 'fake-candid'
with NamedTemporaryFile(suffix=".png") as temp_file:
    fig = sncosmo.plot_lc(epoch_tbl, model=fitted_model, errors=result.errors)
    fig.savefig(temp_file, format="png")
    # fname=temp_file.name)
    temp_file.seek(0)
    # write locally
    destination = f'figs/fit_{candid}.png'
    dest = shutil.copy(temp_file.name), destination)
    # write to gcs
    gcs_filename = f'{candid}.png'
    blob = bucket.blob(f'sncosmo/plot_lc/{gcs_filename}')
    blob.upload_from_filename(filename=temp_file.name)

```
<!-- fe Test with some BQ data -->


<a name="runbeam"></a>
## Run beam pipeline
<!-- fs -->

```bash
gcloud auth login
cd PGB_testing/_Salt2-Vizier
pgbenv

python -m salt2_beam \
            --zone us-central1-b \
            --setup_file /home/troy_raen_pitt/PGB_testing/_Salt2-Vizier/setup.py
```
<!-- fe Run beam pipeline -->

<!-- fe Salt2 -->
---

<a name="vizier"></a>
# Xmatch with Vizier
<!-- fs -->
<a name="HERE">LEFT OFF HERE</a>

Creating `vizier-beam.py` using
- [Windowing example] [Stream messages from Pub/Sub to Cloud Storage](https://cloud.google.com/pubsub/docs/pubsub-dataflow#stream_messages_from_to)
- `Pitt-Google-Broker/broker/value_added/xmatch.py`

__Links__
- [Using `astroquery`](https://astroquery.readthedocs.io/en/latest/#using-astroquery)
- [`astroquery.xmatch`](https://astroquery.readthedocs.io/en/latest/xmatch/xmatch.html#module-astroquery.xmatch)
- Apache Beam
    - [CombinePerKey](https://beam.apache.org/documentation/transforms/python/aggregation/combineperkey/)
    - [Triggers](https://beam.apache.org/documentation/programming-guide/#triggers)
    - [Windowing](https://beam.apache.org/documentation/programming-guide/#windowing)

- read from PS
- use Windowing to batch alerts
- for each batch:
    - create an `astropy.table.Table` with id, ra, dec
    - xmatch with Vizier
- store in BQ

__Vizier BQ schema (just create the BQ table from a df).__
Alert data -> astropy Table -> Vizier__
```python
from astropy.table import Table
from google.cloud import bigquery

# manually copy some candid, ra, dec from BQ ztf
data_list = [
            {'objectId': 'ZTF17aaceekp', 'candid': 1409506562015015014,
            'candidate_ra': 99.793103, 'candidate_dec': 25.8498815},
            {'objectId': 'ZTF18aaeipdy', 'candid': 1409518394515010005,
            'candidate_ra': 118.4654544, 'candidate_dec': 41.6220545},
            {'objectId': 'ZTF18abttmvk', 'candid': 1409518391215010004,
            'candidate_ra': 119.8396791, 'candidate_dec': 37.645499},
            ]
aXmatchTable = Table(rows=data_list)
# xmatch
cat2 = 'vizier:II/246/out'
xmatchTable = XMatch.query(
    cat1=aXmatchTable,
    cat2=cat2,
    max_distance=5 * u.arcsec,
    colRA1='candidate_ra',
    colDec1='candidate_dec')

# create the BQ table so we don't have to supply the schema in the pipeline
xmatchTable.rename_column('2MASS', '_2MASS')
client = bigquery.Client()
PROJECTID = 'ardent-cycling-243415'
table_id = f'{PROJECTID}.dataflow_test.vizier'
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
job = client.load_table_from_dataframe(xmdf, table_id, job_config=job_config)
job.result()  # Wait for the job to complete.
bqtable = client.get_table(table_id)  # check the result
print("Loaded {} rows and {} columns to {}".format(
        bqtable.num_rows, len(bqtable.schema), table_id))


# finish xmatchVizier class
xmatchDict = xmatchTable.to_pandas().to_dict(orient='records')
```

__Run the job__
```bash
pgbenv
cd ~/PGB_testing/_Salt2-Vizier

# args
window_size=120 # seconds


# python args
setup_file=~/Documents/PGB/PGB_testing/_Salt2-Vizier/setup.py

# xmatch args
vizierCat=vizier:II/246/out
max_xm_distance=5 # arcsec

# pipeline options
runner=DataflowRunner
region=us-east4
PROJECTID=ardent-cycling-243415
dataflow_job_name=ztf-alert-data-ps-vizier
max_num_workers=5
beam_bucket=ardent-cycling-243415_dataflow-test
staging_location=gs://${beam_bucket}/staging
temp_location=gs://${beam_bucket}/temp

# beam run args (known_args)
input_PS_topic=projects/ardent-cycling-243415/topics/ztf_alert_data
output_BQ_table=dataflow_test.vizier
# window_size=300 # seconds

python vizier-beam.py \
            --experiments use_runner_v2 \
            --setup_file ${setup_file} \
            --vizierCat ${vizierCat} \
            --max_xm_distance ${max_xm_distance} \
            --runner ${runner} \
            --region ${region} \
            --project ${PROJECTID} \
            --job_name ${dataflow_job_name} \
            --max_num_workers ${max_num_workers} \
            --staging_location ${staging_location} \
            --temp_location ${temp_location} \
            --PROJECTID ${PROJECTID} \
            --input_PS_topic ${input_PS_topic} \
            --output_BQ_table ${output_BQ_table} \
            --window_size ${window_size}
```

<!-- fe Xmatch with Vizier -->
