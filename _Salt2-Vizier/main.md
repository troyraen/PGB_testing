- [dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)
- [salt2-fits dashboard](https://console.cloud.google.com/monitoring/dashboards/resourceDetail/dataflow_job,project_id:ardent-cycling-243415,region:us-central1,job_name:salt2-fits?project=ardent-cycling-243415&timeDomain=1d) 

# Outline
- [Run beam pipeline](#runbeam)
- [Filter for extragalactic transients](#filtertrans)
- [Salt2 setup and fit example data](#salt2setup)

# To Do
- [ ]  create buckets in `gcp_setup.py`

<a name="runbeam"></a>
# Run beam pipeline
<!-- fs -->
```bash
cd PGB_testing/_Salt2-Vizier
pgbenv

python -m salt2_vizier_beam \
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

## test with some BQ data

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
    epochs = alert['prv_candidates'] + [alert['candidate']]
    epoch_dictlst.append(bhelp.extract_epochs(epochs))
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

# plot results
sncosmo.plot_lc(epoch_tbl, model=fitted_model, errors=result.errors, fname='figs/fitbq.png')
```

<!-- fe Salt2 setup and fit data -->


# Xmatch with Vizier and store in BQ
