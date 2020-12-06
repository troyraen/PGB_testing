[LEFT OFF HERE](#HERE)

- [dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
- [salt2-fits dashboard](https://console.cloud.google.com/monitoring/dashboards/resourceDetail/dataflow_job,project_id:ardent-cycling-243415,region:us-central1,job_name:salt2-fits?project=ardent-cycling-243415&timeDomain=1d)
- [Salt2 BQ table](https://console.cloud.google.com/bigquery?project=ardent-cycling-243415) (ztf_alerts.salt2)
- [Salt2 jpg bucket](https://console.cloud.google.com/storage/browser/ardent-cycling-243415_ztf-sncosmo?project=ardent-cycling-243415&pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22%29%29&prefix=&forceOnObjectsSortingFiltering=false)

# Outline
- [Setup GCP resources](#gcpsetup)
- [Filter for extragalactic transients](#filtertrans)
- [Salt2 setup and fit example data](#salt2setup)
- [Test with some BQ data](#testwithbq)
- [Run beam pipeline](#runbeam)

# To Do
- [ ]  create buckets in `gcp_setup.py`

<a name="gcpsetup"></a>
# Setup GCP resources
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
# Filter for extragalactic transients
<!-- fs -->
- [Filtering ZTF alerts](https://github.com/ZwickyTransientFacility/ztf-avro-alert/blob/master/notebooks/Filtering_alerts.ipynb)

```python


```

<!-- fe Filter for extragalactic transients -->


<a name="salt2setup"></a>
# Salt2 setup and fit data
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
# Test with some BQ data
<!-- fs -->
```python
from google.cloud import bigquery
import sncosmo
import custommods.beam_helpers as bhelp

# Get the data
PROJECTID = 'ardent-cycling-243415'
input_bq_table = 'ztf_alerts.alerts'
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
# Run beam pipeline
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

<a name="HERE">LEFT OFF HERE</a>

# Xmatch with Vizier and store in BQ
