# Testing branch: tjraen/alert_formatting

- [Install broker on Osiris](#install)
- [Test broker successfully deploys using `c.run()` from `consume.py`](#brokerruns)
- [Create unittests for guess survey and version functions](#guess)
- [Run `pycodestyle`](#pycodestyle)

<a name="install"></a>
## Installing the broker on Osiris (4/9/20)
<!-- fs -->

- [ ]  Fix `setup.py`? After installing broker using Conda based instructions (calling `setup.py`), got the error no module named google when trying to import `consume`. After doing `pip install -r requirements.txt` this import worked.

Command `c = consume.GCSKafkaConsumer(...` (from below) produces the following error:
    `KafkaException: KafkaError{code=_INVALID_ARG,val=-186,str="Failed to create consumer: No provider for SASL mechanism GSSAPI: recompile librdkafka with libsasl2 or openssl support. Current build options: PLAIN SASL_SCRAM OAUTHBEARER"}`
Solution was to install (from email Daniel forwarded me from Christopher Phillips):
```bash
conda install -c conda-forge kafka-python
conda install -c conda-forge python-confluent-kafka
conda install -c stuarteberg -c conda-forge librdkafka=1.0.1=hf484d3e_1
```
<!-- fe ## Installing the broker on Osiris (4/9/20) -->


<a name="brokerruns"></a>
## Test broker successfully deploys using `c.run()` from `consume.py`
<!-- fs -->

```python
import os
os.environ['KRB5_CONFIG'] = './krb5.conf'

from broker.alert_ingestion import consume

# Define connection configuration using default values as a starting point
config = consume.DEFAULT_ZTF_CONFIG.copy()
config['sasl.kerberos.keytab'] = 'pitt-reader.user.keytab'
config['sasl.kerberos.principal'] = 'pitt-reader@KAFKA.SECURE'
print(config)

# Check https://ztf.uw.edu/alerts/public/ for the most recent day with alerts
year = 2020
month = 4
day = 5
topic = f'ztf_{year}{month:02d}{day:02d}_programid1'

# Create a consumer
c = consume.GCSKafkaConsumer(
   kafka_config=config,
   bucket_name='my-gcs-bucket-name-troys-test',
   kafka_topic=topic,
   pubsub_topic='my-GCS-PubSub-name-Troys-test',
   debug=True  # Use debug to run without updating your kafka offset
)

# Ingest alerts one at a time indefinitely
c.run()

```

Now check the bucket `my-gcs-bucket-name-troys-test` and PS topic `my-GCS-PubSub-name-Troys-test`... __Success!__ I see alerts in both places.

<!-- fe ## Test broker successfully deploys using `c.run()` from `consume.py` -->


<a name="guess"></a>
## Create unittests for guess survey and version functions
<!-- fs -->

In repo dir:
```python
from tests import test_format_alerts as tfa
cls = tfa.SchemaVersionGuessing()
cls.test_guess_schema_version_ztf_3_3()


alert_bytes = tfa.load_Avro_bytes(path)


from pathlib import Path
path = Path('/Users/troyraen/Documents/PGB/repo/broker/ztf_archive/data/ztf_archive/1154446891615015011_new_WORKS.avro')


```
<!-- fe Create tests for guess survey and version functions -->


<a name="pycodestyle"></a>
## Run `pycodestyle`
```bash
pgbrepo
pgbenv

cd broker
pycodestyle gcp_setup.py

cd alert_ingestion
pycodestyle consume.py

cd.
cd.
cd tests
pycodestyle test_format_alerts.py

```
