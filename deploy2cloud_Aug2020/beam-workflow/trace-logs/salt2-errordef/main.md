# Salt2 fit fails with `RuntimeError` in Dataflow job (streaming PS)
Solution: Told Dataflow to use specific versions of `sncosmo` and `iminuit`; see below.

Try to reproduce the error:

__Get from BQ one of the alerts that failed the fit and test it__
```python
from google.cloud import bigquery
import sncosmo
import beam_helpers.fit_salt2 as fs2

# Get some data
failed_candid = 1438471434115015171  # got this id from logs
PROJECTID = 'ardent-cycling-243415'
# input_bq_table = 'ztf_alerts.alerts'
input_bq_table = 'dataflow_test.ztf_alerts'
client = bigquery.Client()
query = f"SELECT * FROM {PROJECTID}.{input_bq_table} WHERE candid={failed_candid} LIMIT 1"
query_job = client.query(query, project=PROJECTID)  #, job_config=config)
# extract the rows
alertlst = []
for row in query_job:
    alertlst.append(row)

# extract epoch info
epoch_dictlst = []
s2f = fs2.fitSalt2()
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
# THIS FIT SUCCEEDS
```

Maybe this is an issue related to streaming. Try running Dataflow job with direct runner?
```python

```

Don't catch RuntimeError, just let it fail... running Dataflow job again.
Got more info on the error, chased it through module files on local machine, but lines/files did not match what error output said should be there.
Updated Dataflow to use the versions of `sncosmo` and `iminuit` that I can in `pip freeze` locally. Now it is working.
