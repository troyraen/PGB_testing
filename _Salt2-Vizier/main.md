[dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)

# To Do
- [ ]  create buckets in `gcp_setup.py`

# run beam
```python
python -m salt2_vizier_beam \
            --region us-central1
            --setup_file ./setup.py
```

# Salt2 setup
- [SNCosmo, Fitting a light curve with Salt2](https://sncosmo.readthedocs.io/en/stable/examples/plot_lc_fit.html)

`pip install sncosmo`

```python
import sncosmo

data = sncosmo.load_example_data()
```

# test with some data

```python
from google.cloud import bigquery

PROJECTID = 'ardent-cycling-243415'
input_bq_table = 'ztf_alerts.alerts'
client = bigquery.Client()

query = f'SELECT * FROM {PROJECTID}.{input_bq_table} LIMIT 1'
# config = bigquery.job.QueryJobConfig()
# config.use_legacy_sql = False
query_job = client.query(query, project=PROJECTID)  #, job_config=config)

for row in query_job:
    print("publisher={}, objectId={}".format(row['publisher'], row["objectId"]))
    alert = row


```


# Xmatch with Vizier and store in BQ
