# Testing branch: tjraen/alert_formatting

## Testing `consume.py`

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
month = 3
day = 9
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
