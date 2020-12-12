- [bucket: rubin-sims/alert_avro](https://console.cloud.google.com/storage/browser/ardent-cycling-243415_rubin-sims/alert_avro?pageState=(%22StorageObjectListTable%22:(%22f%22:%22%255B%255D%22%29%29&project=ardent-cycling-243415&prefix=&forceOnObjectsSortingFiltering=false)
- [BQ table](https://console.cloud.google.com/bigquery?project=ardent-cycling-243415) (rubin_sims.)
- [dataflow console](https://console.cloud.google.com/dataflow/jobs?project=ardent-cycling-243415)

Process Rubin sample alerts:
1. Run the Rubin alert stream simulator (Kafka stream)
2. Dataflow job to
    1. listen to the kafka stream
    2. upload alerts to BQ
    3. fit with Salt2, xmatch with Vizier

# ToC
- Go to: [LEFT OFF HERE](#HERE)
- [To Do](#todo)
- [Links: LSST Sample Alerts](#lsst-links)
- [VM: Alert Stream Simulator](#stream-sim-vm)
    - [Prereqs + Install](#sim-prereqs)
    - [Run `alert-stream-simulator`](#run-stream-sim)
- [`pykafka` Consumer](#consumer)
- [Dataflow job](#dataflow)
    - [Prereqs + GCP setup + Alert schema](#dataflow-prereqs)
    - [Create and run job](#dataflow-run)

<a name="todo"></a>
# To Do
- [x]  set up VM to run the `alert-stream-simulator` and publish to a topic
    - [ ]  set up publish as public host (to be accessed externally, necessary for Dataflow)
- [ ]  set up Dataflow job to listen to the stream
    - [ ]  ingest to GCS, BQ
    - [ ]  Salt2
    - [ ]  xmatch with vizier
    <!-- - connect/listen to the topic
        - from within the same VM (easier) or deploy broker as in production (more realistic) -->

<a name="lsst-links"></a>
# Links: LSST Sample Alerts
<!-- fs -->
- [Sample alert info](https://github.com/lsst-dm/sample_alert_info)
- [Alert packet utils](https://github.com/lsst/alert_packet)
- [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/)
    - Larger samples of alerts suitable for bulk analysis and scale testing are available; see [sample_alert_info](https://github.com/lsst-dm/sample_alert_info/) for locations from which alerts can be downloaded.
- [Bellm presentation](https://project.lsst.org/meetings/rubin2020/sites/lsst.org.meetings.rubin2020/files/Bellm_Rubin_alerts_200813.pdf) (contains links listed above)
- [DMTN-093: Design of the LSST Alert Distribution System](https://dmtn-093.lsst.io/#management-and-evolution)
- __These are Snappy Avro compressed files in Confluent Wire format (first 5 bytes of message is the wire header)__

<!-- fe Links: LSST Sample Alerts -->

<a name="stream-sim-vm"></a>
# VM: Alert Stream Simulator
<!-- fs -->
<!-- fs LINKS -->
- Rubin
    - [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/) (instructions + repo)
- GCP
    - [Create VM instance](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create)
    - [Creating and configuring VM instances](https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance)
    - [Connect to VM instance](https://cloud.google.com/compute/docs/instances/connecting-to-instance#gcloud)
    - [Resize a VM disk](https://cloud.google.com/compute/docs/disks/add-persistent-disk#gcloud_4) (Persistent disk space starts at 10G for all machine types)
        - [extra instructions to access the newly added space](https://stackoverflow.com/questions/22381686/how-can-size-of-the-root-disk-in-google-compute-engine-be-increased)
    - [Containers on Compute Engine](https://cloud.google.com/compute/docs/containers)
    - [Docker] [Install Docker Engine on Debian](https://docs.docker.com/engine/install/debian/)
    - [Python] [Install Python 3.7 on Debian 9](https://linuxize.com/post/how-to-install-python-3-7-on-debian-9/)
    - [Python] [Install Python 3.6.4 on Debian 9](https://www.rosehosting.com/blog/how-to-install-python-3-6-4-on-debian-9/)
    - [venv] [Using venv to isolate dependencies](https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv)
    - [Anaconda] [Install the Anaconda Python Distribution on Debian 10](https://www.digitalocean.com/community/tutorials/how-to-install-the-anaconda-python-distribution-on-debian-10)
    - Dashboard
        - [Console VM instances](https://console.cloud.google.com/compute/)
<!-- fe LINKS -->

<a name="sim-prereqs"></a>
## Prereqs + Install
<!-- fs -->
__Create and connect to VM:__
```bash
# create VM instance
gcloud compute instances create rubin-stream-simulator32 \
    --zone=us-central1-a \
    --machine-type=n1-standard-32 \
    --service-account=591409139500-compute@developer.gserviceaccount.com \
    --scopes=cloud-platform \
    --metadata=google-logging-enabled=true \
    --tags=kafka-server # for the firewall rule

# increase the disk space (default starts at 10G for all machine types)
gcloud compute disks resize rubin-stream-simulator32 --zone us-central1-a --size 20
sudo apt install -y cloud-utils         # Debian jessie
# sudo apt install -y cloud-guest-utils   # Debian stretch, Ubuntu
sudo growpart /dev/sda 1
sudo resize2fs /dev/sda1

# connect to instance
gcloud compute ssh rubin-stream-simulator32 --project=ardent-cycling-243415 --zone=us-central1-a

# stop/delete an instance
gcloud compute instances delete rubin-stream-simulator --zone us-central1-a

```

__Install pre-reqs `alert-stream-simulator`__
```bash
sudo apt-get update && sudo apt-get upgrade

# # install conda
# cd /tmp
# sudo apt-get install curl
# curl -O https://repo.anaconda.com/archive/Anaconda3-2020.11-Linux-x86_64.sh
# bash Anaconda3-2020.11-Linux-x86_64.sh
# source ~/anaconda3/bin/activate
# conda init
# conda list
# # create env
# conda create --name rass python=3
# conda activate rass

# install and create virtual env
sudo apt-get install -y python3-venv
python3 -m venv rass-venv # alert stream simulator env
source rass-venv/bin/activate # activate alert stream simulator env

# # install Python 3.6 (following link above)
# sudo apt-get install -y make build-essential libssl-dev zlib1g-dev
# sudo apt-get install -y libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm
# sudo apt-get install -y libncurses5-dev  libncursesw5-dev xz-utils tk-dev
# wget https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tgz
# tar xvf Python-3.6.4.tgz
# cd Python-3.6.4
# ./configure --enable-optimizations
# nproc # find number of cores
# make -j <ncores>
# sudo make altinstall
# python3 --version
# python --version

# # install Python 3.7 (following link above)
# sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl libbz2-dev
# # trying a root install
# cd ..
# cd ..
# sudo curl -O https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
# sudo tar -xf Python-3.7.3.tar.xz
# cd Python-3.7.3
# sudo ./configure --enable-optimizations
# nproc # find number of cores
# sudo make -j <ncores>
# # HERE
# sudo make altinstall
# python3.7 --version # check install

sudo apt-get install -y python3-dev

# install Docker (following link above)
# prereqs
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install -y \
    apt-transport-https ca-certificates gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88 # verify key
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) stable"
# install
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
# test
sudo docker run hello-world # see quote below for further info

# install other dependencies
sudo apt-get install -y make git docker-compose libsnappy-dev
# sudo apt-get install python3-pip #python3-setuptools

# couldn't get 'create-stream' to work until i did this
# sudo pip3 uninstall fastavro
pip3 install fastavro==0.23
pip install astropy
# may also need to uninstall/reinstall snappymodule
```

"Docker Engine is installed and running. The docker group is created but no users are added to it. You need to use sudo to run Docker commands. Continue to [Linux postinstall](Docker Engine is installed and running. The docker group is created but no users are added to it. You need to use sudo to run Docker commands. Continue to Linux postinstall to allow non-privileged users to run Docker commands and for other optional configuration steps.) to allow non-privileged users to run Docker commands and for other optional configuration steps."


__Install `alert-stream-simulator`__
```bash
git clone https://github.com/lsst-dm/alert-stream-simulator.git
cd alert-stream-simulator
sudo make install
# skipped this: complains about not finding python. change python -> python3 in Makefile
# complains about not finding setuptools. run manually:
python setup.py install
# comment that line out of the Makefile and run it again to complete setup
sudo make install

# add user to the docker group so can do docker-compose up
sudo usermod -aG docker troy_raen_pitt
# now log out and back in
```

__Config to broadcast externally / Listen from external host__

- [alert-stream-simulator/#networking-and-osx](https://github.com/lsst-dm/alert-stream-simulator/#networking-and-osx)
- [GCP/Kafka open ports for external listening](https://github.com/GoogleCloudPlatform/java-docs-samples/tree/master/dataflow/flex-templates/kafka_to_bigquery#starting-the-kafka-server)

"The listeners are:
- Kafka: localhost:9092 (for the stream) and localhost:9292 (for JMX metrics)
- Zookeeper: localhost:2181
- Grafana: localhost:3000
- InfluxDB: localhost:8086

Edit the docker-compose.yml file, changing all references to "localhost" to the IP address of the broker." _I found that I had to leave `KAFKA_ZOOKEEPER_CONNECT` as `localhost:32181`, otherwise the kafka client/listener could not connect to zookeeper and `docker-compose up` did not work._

```bash
# following instructions to open ports (above)
# from any machine:
gcloud compute instances list # find ip address
# Create a firewall rule to open the port used by Zookeeper and Kafka.
# Allow connections to ports 2181, 9092 in VMs with the "kafka-server" tag.
gcloud compute firewall-rules create allow-kafka \
  --target-tags "kafka-server" \
  --allow tcp:2181,tcp:9092
# add the tag to the instance if it's already been created
gcloud compute instances add-tags rubin-stream-simulator32 --tags=kafka-server

# on the instance machine:
# following networking-and-osx instructions (above)
cd alert-stream-simulator
nano docker-compose.yml
# replace 'localhost' with the instance ip address
```
<!-- fe Prereqs + Install -->

<a name="run-stream-sim"></a>
## Run `alert-stream-simulator`
<!-- fs -->
```bash
# connect to the VM instance
gcloud compute ssh rubin-stream-simulator32 --project=ardent-cycling-243415 --zone=us-central1-a
source rass-venv/bin/activate # activate alert stream simulator env
cd /home/troy_raen_pitt/alert-stream-simulator
# if VM has been shut down since last run, update IP address in docker-compose.yml

docker-compose up
# "This will spin up several containers; once the log output dies down, the system should be up and running."
# open a second terminal
docker-compose ps
# "we expect to see "Up" for the "State" of all containers"

# create a stream
rubin-alert-sim create-stream --dst-topic=rubin_example --force data/rubin_single_ccd_sample.avro
# replay the stream every --repeat-interval [sec]
rubin-alert-sim --verbose play-stream \
    --src-topic=rubin_example \
    --dst-topic=rubin_example_stream \
    --force \
    --repeat-interval=37
    # --property "parse.key=true" \
    # --property "key.separator=:"
# "Connect your consumers to the --dst-topic to simulate receiving Rubin's alerts."


rubin-alert-sim print-stream \
    --src-topic=rubin_example

```
<!-- fe Run `alert-stream-simulator` -->

<!-- fe VM: Alert Stream Simulator -->


<a name="consumer"></a>
# `pykafka` Consumer -> PubSub
<!-- fs -->
Cannot get Dataflow job to decode the alerts. Write a separate consumer to listen and store files in GCS. Optionally writes one file from GCS -> BQ table so that the table exists with the proper schema before the Beam PubSub consumer runs. This avoids having to manually supply a schema for Beam.
- [LSST example] [Writing your own consumer](https://github.com/lsst-dm/alert-stream-simulator#writing-your-own-consumer)

## pykafka Setup
<!-- fs -->

```bash
pip install pykafka
pip install lsst-alert-stream  #lsst-alert-packet
```

__GCP setup__
```python
from google.cloud import storage, pubsub_v1
PROJECT_ID = 'ardent-cycling-243415'
# bucket
storage_client = storage.Client()
bucket_name = f'{PROJECT_ID}_rubin-sims/alert_avro/'
storage_client.create_bucket(bucket_name)

# pubsub
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()
topic_name = 'rubin-simulated-alerts'
topic_path = publisher.topic_path(PROJECT_ID, topic_name)
sub_path = subscriber.subscription_path(PROJECT_ID, topic_name)
publisher.create_topic(topic_path)
subscriber.create_subscription(sub_path, topic_path)

# listen to subscription
subscribe_alerts(topic_name, PROJECT_ID, max_alerts=1)
def subscribe_alerts(subscription_name, project_id, max_alerts=1):
    """Download, decode, and return messages from a Pub/Sub topic

    Args:
        subscription_name   (str): The Pub/Sub subcription name linked to a Pub/Sub topic
        max_alerts          (int): The maximum number of alerts to download

    Returns:
        A list of downloaded and decoded messages
    """

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_name)

    response = subscriber.pull(subscription_path, max_messages=max_alerts)

    message_list, ack_ids = [], []

    for received_message in response.received_messages:
        encoded = received_message.message.data
        # message = encoded.decode('UTF-8')
        message_list.append(encoded)
        ack_ids.append(received_message.ack_id)

    subscriber.acknowledge(subscription_path, ack_ids)

    return (message_list)
```
<!-- fe pykafka Setup -->

## Run the consumer
<!-- fs -->
```bash
pgbenv
cd ~/PGB_testing/_LSST-sample-alerts

broker_host='34.70.184.212:9092'
N_alerts=217
bq_table='ardent-cycling-243415.rubin_sims.alerts' # optional
# send bq_table if want to create a bq table from the last alert processed
# doing so ensures the table exists with the proper schema
# so that we do not have to manually specify one in Beam's WriteToBigQuery
# gcs_filename = '176517576703083331_181078402474705757.avro'

python -m rass-consumer ${broker_host} ${N_alerts} ${bq_table}
```

<!-- fe Run the consumer -->

<!-- fe `pykafka` Consumer -> PubSub -->



<a name="dataflow"></a>
# Dataflow job
<!-- fs -->
<!-- fs LINKS -->
- [example] [`kafkataxi`](https://github.com/apache/beam/tree/master/sdks/python/apache_beam/examples/kafkataxi)
- [`apache_beam.io.kafka`](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/io/kafka.py)
- Install
    - [Install Java with Apt on Debian 10](https://www.digitalocean.com/community/tutorials/how-to-install-java-with-apt-on-debian-10)
- Rubin
    - [Read alert and schema](https://github.com/lsst/alert_packet/blob/master/examples/03-avro-fastavro-comparison.ipynb)
- [possible alternative to `apache_beam.io.kafka.ReadFromKafka`](https://stackoverflow.com/questions/62775435/does-gcp-dataflow-support-kafka-io-in-python)
- GCP
    - [Generate BQ schema from JSON file](https://stackoverflow.com/questions/36127537/json-table-schema-to-bigquery-tableschema-for-bigquerysink/36162988) (2nd answer down)
<!-- fe LINKS -->

<a name="dataflow-prereqs"></a>
## Prereqs + GCP setup + Alert schema
<!-- fs -->
__Install pre-reqs__. Following instructions in `kafkataxi` example above.
```bash
# connect to the VM instance
gcloud compute ssh rubin-stream-simulator32 --project=ardent-cycling-243415 --zone=us-central1-a

# create new virtual env
python3 -m venv dataflow-venv # alert stream simulator env
source dataflow-venv/bin/activate # activate venv

sudo apt-get update

# install java
sudo apt install -y default-jre
java -version
# install dev kit
sudo apt install -y default-jdk
javac -version
export JAVA_HOME='/usr/bin/javac' # not sure this is the right dir for this
echo ${JAVA_HOME}

# get errors about bdist_wheel and setuptools unless I install some prereqs
# apt-get install --only-upgrade setuptools
# pip install --upgrade setuptools
pip install wheel
pip install 'apache-beam[gcp]'

# install ipython
# pip install --user ipython
```

__GCP setup__
```bash
pip install google-cloud-storage
```

```python
from google.cloud import bigquery, storage
PROJECT_ID = 'ardent-cycling-243415'

# create buckets
bucket_name = f'{PROJECT_ID}_rubin-sims'
storage_client = storage.Client()
storage_client.create_bucket(bucket_name)

# create bq dataset
bigquery_client = bigquery.Client()
bigquery_client.create_dataset('rubin_sims', exists_ok=True)

```

__Install LSST packages__
```bash
pip install lsst-alert-stream lsst-alert-packet
```
<!-- fe ## Prereqs + GCP setup + alert schema -->

<a name="HERE">LEFT OFF HERE</a>
_rewrite rubin sim avros to GCS without stripping header. use the following code to try to read that file to see if it was written as a proper avro file._

__Load 1 alert, GCS -> BQ, so that table (with proper schema) is created__
- _Use fastavro to write a uncompressed avro as a temp file, then upload that to BQ_
    - get an alert from gcs bucket
    - read with fastavro
    - write temp file
    - upload to BQ

```python
from google.cloud import storage
project_id = 'ardent-cycling-243415'

# get an alert
bucket_name = 'rubin-sims'
fname = '176517576703083331_181078402474705757.avro'
gcs_fname = f'alert_avro/{fname}'
storage_client = storage.Client(project_id)
bucket = storage_client.get_bucket(f'{project_id}_{bucket_name}')
blob = bucket.blob(gcs_fname)
blob.download_to_filename(fname)

# read with fastavro
import fastavro as fa
fa.is_avro(fname)  # this returns false
with open(fname, 'rb') as fo:
    for record in fa.reader(fo):
        print(record)  # this doesn't work

# check a ztf alert
bucket_name = 'ztf_alert_avro_bucket'
fname = '1602556012306.avro'
storage_client = storage.Client(project_id)
bucket = storage_client.get_bucket(f'{project_id}_{bucket_name}')
blob = bucket.blob(fname)
blob.download_to_filename(fname)

fa.is_avro(fname)  # returns true
```


__SAND__

__Get alert schema for input to WriteToBigQuery().__

Following 'Generate BQ schema from JSON file' link above.

- download the 'data/rubin_single_ccd_sample.avro' file from the VM running RASS
- read with lsst alert packet, get writer schema
- convert this to a bigquery schema

```bash
# install snappy
sudo apt-get install libsnappy-dev
pip install python-snappy

# # download a schema
# wget https://raw.githubusercontent.com/lsst/alert_packet/master/python/lsst/alert/packet/schema/4/0/lsst.v4_0.alert.avsc

# download the alert avro file
# gcloud compute scp --recurse instance-name:remote-dir local-dir
gcloud compute scp --recurse rubin-stream-simulator32:/home/troy_raen_pitt/alert-stream-simulator/data/rubin_single_ccd_sample.avro .
```

```python
import lsst.alert.packet as ap
# fschema = 'lsst.v4_0.alert.avsc'
schema = ap.Schema.from_file()#fschema)  # load _a_ schema. will get alert-specific schema later

falerts = 'rubin_single_ccd_sample.avro'
with open(falerts,'rb') as f:
    writer_schema, packet_iter = schema.retrieve_alerts(f)
    # writer_schema is the schema with which alerts were written
    # (which may be different from this schema being used for deserialization)
    # https://github.com/lsst/alert_packet/blob/master/python/lsst/alert/packet/schema.py
    for packet in packet_iter:
        print(packet['diaSource']['diaSourceId'])
        break

scm = writer_schema.definition # this is the schema as a dict

import json
from google.cloud import bigquery

schemajson = 'schematmp.json'
with open(schemajson, 'w') as fp:
    json.dump(writer_schema.definition, fp)


def _get_field_schema(field):
    name = field['name']
    field_type = field.get('type', 'STRING')
    mode = field.get('mode', 'NULLABLE')
    fields = field.get('fields', [])

    if fields:
        subschema = []
        for f in fields:
            fields_res = _get_field_schema(f)
            subschema.append(fields_res)
    else:
        subschema = []

    field_schema = bigquery.SchemaField(name=name,
        field_type=field_type,
        mode=mode,
        fields=subschema
    )
    return field_schema

def parse_bq_json_schema(schema_filename):
    schema = []
    with open(schema_filename, 'r') as infile:
        jsonschema = json.load(infile)

    for field in jsonschema:
        schema.append(_get_field_schema(field))

    return schema

bq_schema = parse_bq_json_schema(schemajson)
_get_field_schema(jsonschema)
```




```bash
gcloud compute ssh rubin-stream-simulator32 --project=ardent-cycling-243415 --zone=us-central1-a
source dataflow-venv/bin/activate
# get an alert schema
cd /home/troy_raen_pitt/alert-stream-simulator/data
wget https://raw.githubusercontent.com/lsst/alert_packet/master/python/lsst/alert/packet/schema/4/0/lsst.v4_0.alert.avsc
cd ..

wget 34.70.184.212/home/troy_raen_pitt/alert-stream-simulator/data/lsst.v4_0.alert.avsc
```

- if output_schema is null
    - parse an alert to get the header
    - write it to a tmp file as JSON
    - read the tmp file into a string -> output_schema

#### SAND
__Skipped in favor of `schema_autodetect`__
- try using the beam to write to a file and look at it
- use `lsst.alert.packet` to directly access a schema or open and look at an alert
    - [sample alert info](https://github.com/lsst-dm/sample_alert_info)
    - [lsst.alert.packet](https://github.com/lsst/alert_packet)
    - __use schema_autodetect__ [WriteToBigQuery](https://beam.apache.org/releases/pydoc/2.13.0/apache_beam.io.gcp.bigquery.html#apache_beam.io.gcp.bigquery.WriteToBigQuery), [BQ schema detect](https://cloud.google.com/bigquery/docs/schema-detect#python)

Following 'Read alert and schema' link above.
```bash
gcloud compute ssh rubin-stream-simulator-venv --project=ardent-cycling-243415 --zone=us-central1-a
cd /home/troy_raen_pitt
source ass/bin/activate # activate alert stream simulator env
cd alert-stream-simulator # alerts are in data dir

# download the schema file
wget https://raw.githubusercontent.com/lsst/alert_packet/master/python/lsst/alert/packet/schema/4/0/lsst.v4_0.alert.avsc data/.

ipython
```
```python
from fastavro.schema import load_schema

```


<a name="dataflow-run"></a>
## Create and run job
<!-- fs -->
Writing `rass-beam.py` by following/combining:
- [salt2_vizier_beam.py](../_Salt2-Vizier/salt2_beam.py)
- [kafka_taxi.py](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/examples/kafkataxi/kafka_taxi.py)

__Run the job__
```bash
gcloud compute ssh rubin-stream-simulator32 --project=ardent-cycling-243415 --zone=us-central1-a
cd /home/troy_raen_pitt
source dataflow-venv/bin/activate # activate alert stream simulator env
# cd alert-stream-simulator # alerts are in data dir

# create the files to run the beam job
# mkdir beam
# cd beam
# nano setup.py
# nano rass-beam.py
gcloud auth login
cd ~/PGB_testing/_LSST-sample-alerts

python -m rass-beam \
            --region us-central1 \
            --setup_file /home/troy_raen_pitt/beam/setup.py \
            --experiments use_runner_v2 \
            --streaming

```


<!-- fe Create and run job -->

<!-- fe Dataflow job -->
