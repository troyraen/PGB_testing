Been trying to `ReadFromKafka` in the `Beam` pipeline.

- See `ztf-beam.py` for the code and `error.log` for the full error
    - `AttributeError: 'int' object has no attribute 'encode'`
- I checked a Kafka msg received via [deploy2cloud_Aug2020/main.md#testkafkaconnection](file:///Users/troyraen/Documents/PGB/PGB_testing/deploy2cloud_Aug2020/main.md#testkafkaconnection)
    - _`msg.key()` returns `None`_
        - This doesn't seem to be supported (see links below). _Other than the fact that the error is an `int` object, I would think this was the problem._
            - [RuntimeError: cannot encode a null byte[]](https://stackoverflow.com/questions/62899399/python-apache-beam-flink-runner-setup-readfromkafka-returns-error-runtime)
            - [same as above with more comments](http://mail-archives.apache.org/mod_mbox/beam-user/202007.mbox/%3CCAGAbUe-XUQTnO9DUw=LFc-8R9SPdHjsNiaM6yjbT36070B+Psw@mail.gmail.com%3E)
            - [Apache Beam KafkaIO Key Deserializer for messages with no keys](https://stackoverflow.com/questions/62378585/apache-beam-kafkaio-key-deserializer-for-messages-with-no-keys) [Watch this unanswered question.]
    - `msg.value()` returns the alert byte string
- It seems like reading an Avro encoded Kafka alert _should_ be supported. (See [here](https://stackoverflow.com/questions/62544980/how-to-infer-avro-schema-from-a-kafka-topic-in-apache-beam-kafkaio) and [here](https://stackoverflow.com/questions/54755668/how-to-deserialising-kafka-avro-messages-using-apache-beam) for Java example.) However, I haven't been able to make it work with ztf or lsst sim alerts.

---
What follows is the `main.md` from `beam-workflow` dir when I left this problem.

# ZTF Beam Consumer
Rewriting the consumer into a Dataflow / Apache Beam job.

# ToC
- [Beam environment Prereqs](#beam-prereqs)
- [Create GCP resources](#gcpsetup)
- [Create and Run Beam](#runbeam)


# To Do
- __Fix handling of auth files (currently packaged with Dataflow job)__
- [ ]  ReadFromKafka
- [ ]  old code -> transform header and store in GCS
- [ ]  store in BQ
- [ ]  fit with Salt2
- [ ]  xmatch with Vizier


# Links
- Beam API
    - [`apache_beam.io.kafka`](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/io/kafka.py) (includes good description of the Java expansion service)
    - [`apache_beam.io.kafka.ReadFromKafka`](https://beam.apache.org/releases/pydoc/2.24.0/apache_beam.io.kafka.html#apache_beam.io.kafka.ReadFromKafka)
- ['kafkataxi' example](https://github.com/apache/beam/tree/master/sdks/python/apache_beam/examples/kafkataxi)
- [alternate option, `beam_nuggets`](http://mohaseeb.com/beam-nuggets/beam_nuggets.io.kafkaio.html)


<a name="beam-prereqs"></a>
# Beam environment Prereqs
<!-- fs -->
```bash
# set environment variables
EXPORT ztf_server='public2.alerts.ztf.uw.edu:9094'
EXPORT ztf_principle='pitt-reader@KAFKA.SECURE'
EXPORT ztf_keytab_path='pitt-reader.user.keytab'


```
<!-- fe Beam environment Prereqs -->


<a name="gcpsetup"></a>
# Create GCP resources
<!-- fs -->
```python
from google.cloud import bigquery, storage
PROJECT_ID = 'ardent-cycling-243415'

# # create buckets
# bucket_name = f'{PROJECT_ID}_ztf-dataflow-test'
# storage_client = storage.Client()
# storage_client.create_bucket(bucket_name)
#
# # create bq dataset
# bigquery_client = bigquery.Client()
# bigquery_client.create_dataset('ztf_dataflow_test', exists_ok=True)

```
<!-- fe Create GCP resources -->


<a name="runbeam"></a>
# Create and Run Beam
<!-- fs -->
Writing `ztf-beam.py` using `_LSST-sample-alerts` and `_dataflow-test` content as guides.

- read from kafka Stream
- transform (fix schema)
- write to gcs
- write to bq
- process

on troy VM:
- [x]  install Java
- [x]  clone PGB_testing
- [x]  scp auth files
```bash
# from Roy, scp auth files to troy vm
sudo gcloud compute scp krb5.conf troy:/home/troyraen/PGB_testing/deploy2cloud_Aug2020/beam-workflow/config/krb5.conf --zone us-east4-a
sudo gcloud compute scp pitt-reader.user.keytab troy:/home/troyraen/PGB_testing/deploy2cloud_Aug2020/beam-workflow/config/pitt-reader.user.keytab --zone us-east4-a
```

__Run the job__
```bash
pgbenv
cd ~/PGB_testing/deploy2cloud_Aug2020/beam-workflow
python -m ztf-beam \
            --region us-central1 \
            --setup_file setup.py \
            --experiments use_runner_v2 \
            --streaming
```


<!-- fe Create and Run Beam -->
