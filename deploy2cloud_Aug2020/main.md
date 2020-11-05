# Cleanup To do list
- [ ]  do something with LSST test alerts
- [ ]  install kafka directly (without conda)
    - [-]  alternately, consider [using PyKafka](#pykafka) (recommended by Rubin for their stream)... Will not work because does not have SASL support
- [ ]  [set env variables from file](https://cloud.google.com/compute/docs/containers/configuring-options-to-run-containers#setting_environment_variables)
- [x]  clean up this file
- [ ]  WARNING: The Node.js 8 runtime is deprecated on Cloud Functions. Please migrate to Node.js 10 (--runtime=nodejs10). See https://cloud.google.com/functions/docs/migrating/nodejs-runtimes
- [ ]  add GCS2BQ cloud fnc deployment to scheduleinstance.py
- [ ]  change Dockerfile to use master branch
- [ ]  fix publish_pubsub import to GCS2BQ cloud fnc

# Pre-meeting To do list
- [ ]  in `_avro2BQ`, see Not yet done section
- [ ]  are readthedocs up to date?
    - [ ]  alert_ingestion.rst
- [ ]  pull request conflict file `broker/alert_ingestion/GCS_to_BQ/main.py`

# Fixing issues:
- [x]  [Docker login](#dockerlogin)
- [x]  [Cloud Shell](#envsetup)
- [x]  fixed paths (copy auth files) in Dockerfile
- [x]  [fixed IAM permissions (Service Account Credentials)](#svccreds)
- [x]  [SASL error](#sasl)
- [x]  `msg = self.consume(num_messages=1, timeout=5)[0]` `"IndexError: list index out of range`. Solution: ZTF reset Kafka ofsets + we now use `self.poll()` instead of `self.consume()`
    - [Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb](#testkafkaconnection)
- [ ]  [broker VM instance runs once but does not restart](#startinstance)
- [x]  Changed VM machine type to `g1-small` because resources were over-utilized
- [ ]  [Consumer ingests for awhile, then just stops](#ingestionstops)
- [ ]  `GCS_to_BQ` streaming rate limit exceeded ([quotas](https://cloud.google.com/bigquery/quotas#streaming_inserts), [table limits](https://cloud.google.com/bigquery/quotas#standard_tables))

# Outline
- [Status check](#status)
- [Deploying the Broker](#deploybroker)
    - [Set up environment](#envsetup)
    - [Manually trigger compute instance](#triggervm)
- [Error Logging](#logging)

---

need to be able to query Antares and have them query us
2 bq tables:
    - one we can just do stuff with
    - one that is complete for ~year (get all these in a bucket first - Daniel will do this)
front end:
    - look at other broker websites. what do i like/not like
focus on manually running a bunch of stuff. can connect things later.

By time we write proposal
Should have set of alerts + history
    - classifications run on them
        - cloud fnc, query BQ, fit Salt2, push output to new BQ table
            - make db table queryable, not editable by public
    - way to query output and display a table (Daniel)
Xmatch with Vizier

<a name="status"></a>
# Status check
<!-- fs -->
1. Recommendation: "Switch VM resources with high CPU or memory usage to a recommended machine type." [here](https://console.cloud.google.com/home/recommendations?project=ardent-cycling-243415)
2. VM logs No module named `broker.consumer` from `consume_ztf.py`
3. environment variables not found

Deleting all GCP resources and trying to deploy the broker from scratch.
<!-- fe # Status check -->

<a name="envsetup"></a>
## Set up environment
<!-- fs -->
```bash
# pgbenv
# cd /Users/troyraen/Documents/PGB/repo/docker_files

# copy credential files to cloudshell
gcloud alpha cloud-shell scp localhost:/Users/troyraen/Documents/PGB/repo/krb5.conf cloudshell:~/Pitt-Google-Broker/.
gcloud alpha cloud-shell scp localhost:/Users/troyraen/Documents/PGB/repo/pitt-reader.user.keytab cloudshell:~/Pitt-Google-Broker/.

# log into Cloud Shell
gcloud alpha cloud-shell ssh
gcloud auth login

# create Conda env if necessary. use _env-setup/main.md
conda activate pgb
```
<!-- fe ## Set up environment -->

<a name="deploybroker"></a>
# Deploy broker
<!-- fs -->

__Create and push the Docker image__
~[Install Docker on a Mac](https://runnable.com/docker/install-docker-on-macos)~

Use Google Cloud Shell, `docker` is already installed.

Following
- [our docs](https://pitt-broker.readthedocs.io/en/development/deployment/deploying_images.html)
- [Pushing and pulling images](https://cloud.google.com/container-registry/docs/pushing-and-pulling)
- [Containers on Compute Engine](https://cloud.google.com/compute/docs/containers)

```bash
# configure Docker
# gcloud auth configure-docker gcr.io

# consume_ztf_today:tag106a

# build the image
cd /home/troy_raen_pitt/Pitt-Google-Broker
# docker build -t consume_ztf_today -f /home/troy_raen_pitt/Pitt-Google-Broker/docker_files/consume_ztf_today.Dockerfile . --no-cache=true
docker build -t consume_ztf -f /home/troy_raen_pitt/Pitt-Google-Broker/docker_files/consume_ztf.Dockerfile . #--no-cache=true

# tag the image
git log -1 --format=format:"%H" # get git commit hash to use for the TAG
# docker tag [SOURCE_IMAGE] [HOSTNAME]/[PROJECT-ID]/[IMAGE]:[TAG]
# docker tag consume_ztf_today gcr.io/ardent-cycling-243415/consume_ztf_today:tag1103c
docker tag consume_ztf gcr.io/ardent-cycling-243415/consume_ztf:b0bf99587db1ce3f02ace762b087503d1d48db71c

# push the image
# docker push gcr.io/ardent-cycling-243415/consume_ztf_today:tag1103c
docker push gcr.io/ardent-cycling-243415/consume_ztf:b0bf99587db1ce3f02ace762b087503d1d48db71c
```

__Setup GCP__
```python
from broker import gcp_setup
gcp_setup.auto_setup()
```

__Setup firewall rule__
```bash
gcloud compute firewall-rules create 'ztfport' --allow=tcp:9094 --description="Allow incoming traffic on TCP port 9094" --direction=INGRESS --enable-logging
```



__Deploy using scheduleinstance.sh__

Before doing this, delete resources if previously created:
- VM instances
- PubSub topics
- Cloud functions
- Cloud Scheduler

```bash
cd ~/Pitt-Google-Broker/broker/cloud_functions
nano scheduleinstance.sh # update image tag
# ./scheduleinstance_today.sh
./scheduleinstance.sh
```

This schedules the broker to be deployed nightly.
To test some functionality, __start/stop an instance__ by manually sending a PubSub message to trigger the cloud function:

```bash
cd scheduleinstance
echo -n '{"zone":"us-central1-a", "label":"env=consume-ztf-1"}' | base64
# copy the encoded output and use it to replace `${data}` below
gcloud functions call startInstancePubSub --data '{"data":"${data}"}'
gcloud functions call startInstancePubSub --data '{"data":"eyJ6b25lIjoidXMtY2VudHJhbDEtYSIsICJsYWJlbCI6ImVudj1jb25zdW1lLXp0Zi0xIn0="}'

# check the status
gcloud compute instances describe consume-ztf-1 \
    --zone us-central1-a \
    | grep status

us-central1-a

# us-west1-b
# Using this zone, output from gcloud functions call:
# result: Successfully started instance(s)
# However, gcloud compute call could not find the instance
```

This is not running because it can't find the authentication files.

Solution: package the files with the Dockerimage

For the service account credentials:
<!-- fe deploy broker -->

<a name="logging"></a>
# Error Logging
<!-- fs -->
__Some useful log messages to search for__
- container ID: `Starting a container with ID: <af17530117a00547c18818ebf0bc87e492dad06117f78b98706f4141b1349937>`
<!-- gcr.io/ardent-cycling-243415/consume_ztf_today -->
- `Pulling image: <'gcr.io/ardent-cycling-243415/consume_ztf_today:tag1103c'>`
- `Successfully sent gRPC to Stackdriver Logging API.`

__Trying to integrate GCP logging with python modules:__
- [quickstart](https://cloud.google.com/logging/docs/quickstart-python)
- [severity options](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity)

Testing from terminal
```bash
sshg
gcloud auth login
git clone https://github.com/GoogleCloudPlatform/python-docs-samples
cd python-docs-samples/logging/cloud-client
python snippets.py my-log write
# this doesn't work. i think the issue is authentication from service account but error messages are very vague.
```

__GCP console dashboard recommends installing monitoring and logging agents.__
Found that neither is supported for Container-Optimized OS, so we can't use them.
- [Cloud Monitoring](https://cloud.google.com/monitoring/agent/installation?_ga=2.164611839.-1326490616.1602709223&_gac=1.191248728.1603912261.Cj0KCQjwreT8BRDTARIsAJLI0KJddB2avE270n6iRzLZrZVZVhlZn4kOSQsflblDZU_ebUXMtllmbBAaArLlEALw_wcB) - NOT SUPPORTED FOR THE Container-Optimized OS)
    - seems like this has to be installed in the instance itself, not in the container => can't use the Dockerfile for this. suggestion is to either install this just after creating the instance (which will stop/start the instance) or to apply monitoring agent across multiple VMs (this will not work with the cos OS)
- [Cloud Logging](https://cloud.google.com/logging/docs/agent/installation?_ga=2.232268255.-1326490616.1602709223&_gac=1.162537038.1603912261.Cj0KCQjwreT8BRDTARIsAJLI0KJddB2avE270n6iRzLZrZVZVhlZn4kOSQsflblDZU_ebUXMtllmbBAaArLlEALw_wcB) - something was enabled by adding ` --metadata=google-logging-enabled=true` to the `gcloud compute instances create-with-container` command, but I think it's different from the cloud logging agent.

<!-- fe # Error Logging -->


<a name="pykafka"></a>
# Using PyKafka
<!-- fs -->
- [PyKafka](https://pykafka.readthedocs.io/en/latest/index.html)
- Also see "Writing your own consumer" at the bottom of [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/)

```bash
conda clean --all
conda create -n pgb-pykafka python=3.7 ipython
conda activate pgb-pykafka
pip install pykafka

ipython
```
```python
from pykafka import KafkaClient, SslConfig
config = SslConfig( cafile='pitt-reader@KAFKA.SECURE',
                    certfile='pitt-reader@KAFKA.SECURE',  # optional
                    keyfile='./pitt-reader.user.keytab')  # optional
client = KafkaClient(hosts="public2.alerts.ztf.uw.edu:9094", ssl_config=config)
```

This will not work because PyKafka does not provide SASL support.
<!-- fe Using PyKafka -->

___
# Attempts to fix various things


<a name="ingestionstops"></a>
### Consumer ingests for awhile, then just stops
<!-- fs -->
See, e.g., machine id 5597883590625052742
[Logs from time period where ingestion stoped](https://console.cloud.google.com/logs/query;timeRange=2020-10-30T20:30:26.178Z%2F2020-10-30T20:33:26.178Z?project=ardent-cycling-243415)

<!-- fe Consumer ingests for awhile, then just stops -->


<a name="">startinstance</a>
### Stop/Start compute instance not working properly
<!-- fs -->
Trying to make this process work: https://cloud.google.com/scheduler/docs/start-and-stop-compute-engine-instances-on-a-schedule

start today instance
manually trigger PS message to stop
manually trigger PS message to start
see what happens

add debug log statements
    - connect Cloud Logging to python root logger: https://cloud.google.com/logging/docs/setup/python#connecting_the_library_to_python_logging
add logs writer role to IAM service account
re-deploy

trigger cloud function to Start/Stop an instance from command line
```bash
echo '{"zone":"us-central1-a", "label":"env=consume-ztf-1"}' | base64
# there ended up being a space in data that I had to manually remove. no idea why
gcloud functions call stopInstancePubSub --data '{"data":"eyJ6b25lIjoidXMtY2VudHJhbDEtYSIsICJsYWJlbCI6ImVudj1jb25zdW1lLXp0Zi0xIn0K"}'
gcloud functions call startInstancePubSub --data '{"data":"eyJ6b25lIjoidXMtY2VudHJhbDEtYSIsICJsYWJlbCI6ImVudj1jb25zdW1lLXp0Zi0xIn0K"}'
```

<!-- fe Stop/Start compute instance not working -->


<a name="testkafkaconnection"></a>
### Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb
<!-- fs -->
```python
from confluent_kafka import Consumer, KafkaException
import os
import sys

os.environ['KRB5_CONFIG'] = './krb5.conf'

# Consumer configuration
# See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
conf = {
            'bootstrap.servers': 'public2.alerts.ztf.uw.edu:9094',
            'group.id': 'group',
            'session.timeout.ms': 6000,
            'enable.auto.commit': 'TRUE',
            'sasl.kerberos.principal': 'pitt-reader@KAFKA.SECURE',
            'sasl.kerberos.kinit.cmd': 'kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}',
            'sasl.kerberos.keytab': './pitt-reader.user.keytab',
            'sasl.kerberos.service.name': 'kafka',
            'security.protocol': 'SASL_PLAINTEXT',
            'sasl.mechanisms': 'GSSAPI',
            'auto.offset.reset': 'earliest'
            }

# Create Consumer instance
# Hint: try debug='fetch' to generate some log messages
c = Consumer(conf)

def print_assignment(consumer, partitions):
        print('Assignment:', partitions)

# Subscribe to topics
c.subscribe(['ztf_20201013_programid1'])

# msg = c.consume(num_messages=1, timeout=1)

# Read messages from Kafka, print to stdout
try:
    while True:
        print('while True')

        msg = c.poll(timeout=1.0)
        print('poll')

        if msg is None:
            print('continue')
            continue
        if msg.error():
            print('error')
            raise KafkaException(msg.error())
        else:
            print('else')
            print(msg.value())
            break
except KeyboardInterrupt:
        print('%% Aborted by user\n')
finally:
        # Close down consumer to commit final offsets.
        c.close()

```

<!-- fe # Test whether can connect to Kafka stream using code from notebooks/ztf-auth-test.ipynb -->


<a name="svccreds"></a>
### Service Account Credentials (8/17/20)
<!-- fs -->
Following instructions [here](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances).

Service account
- [x]  name: Compute Engine default service account
- [x]  email: 591409139500-compute@developer.gserviceaccount.com
- [x]  remove role: Editor
- [x]  add role: Compute Admin
- [x]  add role: Service Account User

Code changes:
- [x]  Removed line `ENV GOOGLE_APPLICATION_CREDENTIALS "GCPauth.json"` from `consume_ztf.Dockerfile`. Not sure if it will cause other problems since that file will no longer be there.
- [x]  Removed line `COPY GCPauth.json GCPauth.json` from `consume_ztf.Dockerfile`.

It is unclear to me whether this will cause authentication problems for other parts of the deployment code or for individual modules. Need to try it and see. If there are problems, see [this link](https://cloud.google.com/compute/docs/access/create-enable-service-accounts-for-instances#clientlib) for help.

<!-- fe Service Account Credentials -->

<a name="triggervm"></a>
### Manually trigger compute instance
<!-- fs -->
I was able to manually trigger the cloud function startInstancePubSub with `gcloud functions call startInstancePubSub --data '{"data":"${data}"}'`. The logs say that the function executed successfully, and that the compute instance started, but nothing further happens. There are no errors in the logs, but none of the resources get set up and the VM doesn’t appear to actually be doing anything. Still looking…

It looks like the instance is already running due to the first command in `scheduleinstance.py`, `gcloud compute instances create-with-container`. Then I manually stopped (but did not delete) the container and tried the manual trigger again. This time it gives an error,
`{ "@type": "type.googleapis.com/cloud_integrity.IntegrityEvent", "bootCounter": "2", "lateBootReportEvent": { ... } }`
which appears to be due to the "Shielded VM" integrity measures. This integrity check passed before, so I don't think this is a useful error to track down.

Manually created a compute instance (`instance-1`) using the image. Logs show no errors, look similar to previous "successes". Logged into the VM instance:
`Google Cloud Platform -> VM Instances -> arrow next to "SSH" in connect column -> Open in browser window`. When I logged in there was a message saying
`The startup agent encountered errors. Your container   #
  #  was not started. To inspect the agent's logs use       #
  #  'sudo journalctl -u konlet-startup' command.`
When I ran this command I found the error
`Error: Failed to start container: Error response fr
om daemon: {"message":"pull access denied for gcr.io/ardent-cycling-243415/consume_ztf, repository does not exist or ma
y require 'docker login': denied: Permission denied for \"5b4068358afbf88c34b7cb0aa48e68553482eb2f\" from request \"/v2
/ardent-cycling-243415/consume_ztf/manifests/5b4068358afbf88c34b7cb0aa48e68553482eb2f\". "}`

Logged in (SSH) to `consume-ztf-2` (which I don't think I've altered since trying to start it using `scheduleinstance.py` using same method from above... Same error message is displayed at top of screen, and same error is in the "agent's logs".

<!-- fe Manually trigger compute instance -->

<a name="dockerlogin"></a>
### docker login
<!-- fs -->
May need to do `gcloud auth configure-docker`, see [this help page](https://cloud.google.com/sdk/gcloud/reference/auth/configure-docker). Configuration may already be set up in Google Cloud Shell. Log into that and try it.

```bash
# set the project
gcloud config set project ardent-cycling-243415

# clone the repo
git clone https://github.com/mwvgroup/Pitt-Google-Broker.git
cd Pitt-Google-Broker
git fetch
git checkout development
cd broker/cloud_functions
./scheduleinstance.sh

# this gives the same `docker login` error
```

The Docker image is in the GCP project, so we should not need to configure Docker authentication for this (see 3rd paragraph [here](https://cloud.google.com/artifact-registry/docs/docker/authentication#methods))

Added role `Artifact Registry Administrator` to the compute service account. Got same `docker login` error.

Added `storage-rw` scope to `gcloud compute instances create-with-container` call. Got same `docker login` error.

Found out `docker` is installed on Google Cloud Shell. Try using this to create and push an image and then call `scheduleinstance.sh`. This will ensure I have Docker credentials on the machine I'm using to call `scheduleinstance`. Got same `docker login` error.

Tried to do `gcloud auth configure-docker gcr.io/ardent-cycling-243415/consumeztf` and got `WARNING: gcr.io/ardent-cycling-243415/consumeztf is not a supported registry
`

Tried to do `docker pull gcr.io/ardent-cycling-243415/consumeztf:7019f8aa86ffe16dcb36fa791dc2fb7e56bb687f` and got
`ERROR: (gcloud.auth.docker-helper) You do not currently have an active account selected.
Please run:

  $ gcloud auth login

to obtain new credentials.`

Ran `gcloud auth login` and followed the instructions, then got `You are now logged in as [troy.raen.pitt@gmail.com].` The `docker pull` command now works. Trying to `scheduleinstance.sh` again.

Added project editor IAM permissions to compute default account. Now it seems to be working.
<!-- fe docker login -->

<a name="sasl"></a>
### SASL error
<!-- fs -->
getting error
`cimpl.KafkaException: KafkaError{code=_INVALID_ARG,val=-186,str="Failed to create consumer: No provider for SASL mechanism GSSAPI: recompile librdkafka with libsasl2 or openssl support. Current build options: PLAIN SASL_SCRAM OAUTHBEARER"}`

Email from ZTF people, forwarded by Daniel, says this is an Ubuntu-specific problem and that we need to install via `sudo apt install krb5-user python3-kafka python3-confluent-kafka`. Tried to add this to `consume_ztf.Dockerfile`, can get the build to complete successfully, but still getting the same error.

Later convo with Christopher Phillips, he said people he knows have abandoned try to use Conda with Kafka and are just installing directly.
<!-- fe SASL error -->
