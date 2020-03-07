# Testing branch: Adds_kafka_consumer

[branch](https://github.com/mwvgroup/Pitt-Google-Broker/tree/Adds_kafka_consumer)

## Testing `consumer.py`

### Usage example copied from the file:
__Skip to next sections for the complete code to test this__
<!-- fs -->

```python
from broker.consumer import GCSKafkaConsumer, DEFAULT_ZTF_CONFIG

# Define connection configuration using default values as a starting point
config = DEFAULT_ZTF_CONFIG.copy()
config['sasl.kerberos.keytab'] = '<Path to authentication file>'
config['sasl.kerberos.principal'] = '<>'
print(config)

# Create a consumer
c = GCSKafkaConsumer(
   kafka_config=config,
   bucket_name='my-GCS-bucket-name',
   kafka_topic='ztf_20200301_programid1',
   pubsub_topic='my-GCS-PubSub-name',
   debug=True  # Use debug to run without updating your kafka offset
)

# Ingest alerts one at a time indefinitely
c.run()

```
<!-- fe ### Usage example copied from the file: -->

### Setup:
<!-- fs -->
```bash
cd /Users/troyraen/Documents/PGB/repo
pgbenv
pip install -r requirements.txt
ipython
```

- [x]  Create the bucket `my-gcs-bucket-name-troys-test` on [GCP storage](https://console.cloud.google.com/storage/browser)
    - [x]  Set permissions for the account `pbserviceaccount@pitt-broker.iam.gserviceaccount.com`, assign as "Storage Admin".
- [x]  Create the PubSub topic `my-GCS-PubSub-name-Troys-test`.
- [x]  Getting authentication info from the notebook [ztf-auth-test.ipynb](notebooks/ztf-auth-test.ipynb).
    - [x]  Need files `pitt-reader.user.keytab` and `krb5.conf` in the current directory.

<!-- fe ### Setup: -->

### Code to test `consumer.py`
<!-- fs -->
```python
import os
os.environ['KRB5_CONFIG'] = './krb5.conf'

from broker.consumer import GCSKafkaConsumer, DEFAULT_ZTF_CONFIG

# Define connection configuration using default values as a starting point
config = DEFAULT_ZTF_CONFIG.copy()
config['sasl.kerberos.keytab'] = 'pitt-reader.user.keytab'
config['sasl.kerberos.principal'] = 'pitt-reader@KAFKA.SECURE'
print(config)

# Create a consumer
c = GCSKafkaConsumer(
   kafka_config=config,
   bucket_name='my-gcs-bucket-name-troys-test',
   kafka_topic='ztf_20200301_programid1',
   pubsub_topic='my-GCS-PubSub-name-Troys-test',
   debug=True  # Use debug to run without updating your kafka offset
)

###
# Got the following errors until I set the os `KRB5_CONFIG` variable, put the authentication files in main broker repo dir, created the bucket, and gave permissions to pbserviceaccount@pitt-broker.iam.gserviceaccount.com

# kinit: Cannot find KDC for realm "KAFKA.SECURE" while getting initial credentials
# Forbidden: 403 GET https://www.googleapis.com/storage/v1/b/my-gcs-bucket-name-troys-test?projection=noAcl: pbserviceaccount@pitt-broker.iam.gserviceaccount.com does not have storage.buckets.get access to my-gcs-bucket-name-troys-test.
###

# Ingest alerts one at a time indefinitely
c.run()
```

__I can get it to `c.run()`, but it doesn't look like it's actually putting files into the bucket.__


<!-- fe ### Code to test `consumer.py` -->
