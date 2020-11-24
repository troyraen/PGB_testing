[LEFT OFF HERE](#HERE)

- [dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
- [salt2-fits dashboard](https://console.cloud.google.com/monitoring/dashboards/resourceDetail/dataflow_job,project_id:ardent-cycling-243415,region:us-central1,job_name:salt2-fits?project=ardent-cycling-243415&timeDomain=1d)

# Outline
- [Run beam pipeline](#runbeam)
- [Filter for extragalactic transients](#filtertrans)
- [Salt2 setup and fit example data](#salt2setup)
- [Test with some BQ data](#testwithbq)

# To Do
- [ ]  create buckets in `gcp_setup.py`

<a name="runbeam"></a>
# Run beam pipeline
<!-- fs -->
```bash
gcloud auth login
cd PGB_testing/_Salt2-Vizier
pgbenv

python -m salt2_beam \
            --region us-central1 \
            --setup_file /home/troy_raen_pitt/PGB_testing/_Salt2-Vizier/setup.py
```
<!-- fe Run beam pipeline -->


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

<a name="HERE">LEFT OFF HERE</a>

Implement Daniel's feedback:
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
for alert in alertlst:
    epoch_dictlst.append(bhelp.extract_epochs(alert))
# get one dict with at least 10 epochs
for epoch_dict in epoch_dictlst:
    if len(epoch_dict['mjd']) > 10:
        print(len(epoch_dict['mjd']))
        break
# get astropy table for salt2
epoch_tbl = bhelp.format_for_salt2(epoch_dict)

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
from tempfile import NamedTemporaryFile, SpooledTemporaryFile
from google.cloud import storage
storage_client = storage.Client()
beam_bucket = 'ardent-cycling-243415_dataflow-test'
bucket = storage_client.get_bucket(beam_bucket)

candid = 'fake-candid'
with NamedTemporaryFile(mode='w') as temp_file:
    sncosmo.plot_lc(epoch_tbl, model=fitted_model, errors=result.errors, fname=temp_file.name)
    temp_file.seek(0)
    gcs_filename = f'{candid}.png'
    blob = bucket.blob(f'sncosmo/plot_lc/{gcs_filename}')
    blob.upload_from_filename(filename=temp_file.name)

# not working. try
# https://beam.apache.org/releases/pydoc/2.25.0/apache_beam.io.localfilesystem.html
# blob example usage
# https://googleapis.dev/python/storage/latest/index.html?highlight=upload_from_filename
# stackoverflow
# https://stackoverflow.com/questions/54223769/writing-figure-to-google-cloud-storage-instead-of-local-drive
```
<!-- fe Test with some BQ data -->


# Xmatch with Vizier and store in BQ
