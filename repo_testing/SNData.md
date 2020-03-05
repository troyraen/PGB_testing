# Testing Daniel's SNData package

[Read the docs](https://sn-data.readthedocs.io/en/1.0.0/index.html)

[Repo](http://github.com/djperrefort/SNData)

```bash
pgbenv
pip install sndata
git clone http://github.com/djperrefort/SNData
cd SNData
pip install -r requirements.txt
```

```python
from sndata.csp import DR3
dr3 = DR3() # instance of data release
print(dr3.survey_name) # survey info
print(dr3.survey_abbrev)
print(dr3.survey_url)
print(dr3.data_type)
print(dr3.publications)
print(dr3.ads_url)
print(dr3.band_names) # Photometric data releases include filters
help(dr3) # summary of the dataset
dr3.download_module_data() # download data
published_tables = dr3.get_available_tables()
print(published_tables)
dr3_demo_table = dr3.load_table(published_tables[0]) # read table
dr3_demo_table

# get observational data
object_ids = dr3.get_available_ids() # get object ids in DR
print(obj_ids)
demo_id = object_ids[0]
data_table = dr3.get_data_for_id(demo_id) # Get data for a given object
print(data_table)
print(data_table.meta)

# Fit the data
model = sncosmo.Model('salt2')
model.set(z=data_table.meta['redshift'])
result, fitted_model = sncosmo.fit_lc(
    data=data_table,
    model=model,
    vparam_names=['t0', 'x0', 'x1', 'c'])
print(result)

# use a filter to get only some of the available objects
def filter_func(data_table):
    return data_table.meta['redshift'] < .1
for data in dr3.iter_data(filter_func=filter_func):
    print(data)
    break

# combine two datasets
from sndata import CombinedDataset, csp, des
combined_data = CombinedDataset(csp.DR3(), des.SN3YR())
combined_data.download_module_data()
list_of_table_ids = combined_data.get_available_tables()
demo_table_id = list_of_table_ids[0]
demo_sup_table = combined_data.load_table(demo_table_id)
list_of_ids = combined_data.get_available_ids()
demo_id = list_of_ids[0]
data_table = combined_data.get_data_for_id(demo_id)
print(data_table)
for data in combined_data.iter_data():
    print(data)
    break
# join IDs for an object observed in two different surveys
combined_data.join_ids(obj_id_1, obj_id_2, obj_id_3, ...)
print(combined_data.get_joined_ids()) # get a list of joined ID values
combined_data.separate_ids(obj_id_1, obj_id_2, obj_id_3, ...) # undo the joining

dr3.delete_module_data() # delete the data
```
