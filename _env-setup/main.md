# Anchors
- [Setup Troy VM](#troyvm)
- [Setup Cloud Shell](#cloudshell)
- [install kafka directly and try to run from command line](#cmdkafka)


<a name="troyvm"></a>
# Setup Troy VM
<!-- fs -->
```bash
# create the VM
gcloud compute instances create troysVM \
    --zone=us-east4-a \
    --machine-type=n1-standard-4 \
    --service-account=tjraen-owner@ardent-cycling-243415.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --metadata=google-logging-enabled=true

# login
gcloud compute ssh troy --project=ardent-cycling-243415 --zone=us-east4-a

# scp example
gcloud compute scp --recurse troy:/path/to/vm/source/file /path/to/local/dest/file
```

__Installs__
```bash
sudo apt-get update && sudo apt-get upgrade

sudo apt-get install git wget gcc python-dev

# install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo mkdir /root/.conda
bash Miniconda3-latest-Linux-x86_64.sh
rm -f Miniconda3-latest-Linux-x86_64.sh

# get latest repo versions
# gcloud alpha cloud-shell ssh
git clone https://github.com/mwvgroup/Pitt-Google-Broker.git
git clone https://github.com/troyraen/PGB_testing.git

# # create conda env
conda create -n pgb python=3.8
conda activate pgb

# pip install some things
pip install -r Pitt-Google-Broker/requirements.txt
pip install ipython
pip install lsst-alert-stream lsst-alert-packet
# pip install google-cloud-storage
#
```

<!-- fe Setup Troy VM -->


<a name="cloudshell"></a>
# Setup Cloud Shell
<!-- fs -->
```bash
# log into Cloud Shell and get latest repo version
gcloud alpha cloud-shell ssh
cd Pitt-Google-Broker
git fetch
git pull
# authorize account
gcloud auth login

# install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
mkdir /root/.conda
Miniconda3-latest-Linux-x86_64.sh
rm -f Miniconda3-latest-Linux-x86_64.sh

# create conda env
# conda remove --name pgb --all
conda env create -f environment.yml -n pgb
# includes `pip install -r Pitt-Google-Broker/requirements.txt`
conda activate pgb

# copy credential files to cloudshell
gcloud alpha cloud-shell scp localhost:/Users/troyraen/Documents/PGB/repo/krb5.conf cloudshell:~/Pitt-Google-Broker/.
gcloud alpha cloud-shell scp localhost:/Users/troyraen/Documents/PGB/repo/pitt-reader.user.keytab cloudshell:~/Pitt-Google-Broker/.


```
<!-- fe Setup Cloud Shell -->


<a name="cmdkafka"></a>
# install kafka directly and try to run from command line
<!-- fs -->
Christopher says to use: `yum install confluent-kafka-2.11`

on Mac, don't have apt-get or yum. probably need to install homebrew.

on Cloud Shell, `sudo apt-get install confluent-kafka-2.11` results in:
```
(base) troy_raen_pitt@cloudshell:~$ sudo apt-get install confluent-kafka-2.11
Reading package lists... Done
Building dependency tree       
Reading state information... Done
E: Unable to locate package confluent-kafka-2.11
E: Couldn't find any package by glob 'confluent-kafka-2.11'
E: Couldn't find any package by regex 'confluent-kafka-2.11'
```

trying in broker... same error as above

_Install full kafka platform on cloud shell._ Following `Get the Software` instructions here (): https://docs.confluent.io/current/installation/installing_cp/deb-ubuntu.html#systemd-ubuntu-debian-install (uninstall command at bottom of page)

Saving warnings from command `sudo apt-get update && sudo apt-get install confluent-platform`:
```
Setting up confluent-kafka-rest (6.0.0-1) ...
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-kafka-rest group confluent
Notice: If you are planning to use the provided systemd service units for
Notice: confluent-kafka-rest, make sure that read-write permissions
Notice: for user cp-kafka-rest and group confluent are set up according to the
Notice: following commands:
chown cp-kafka-rest:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent

Setting up confluent-schema-registry (6.0.0-1) ...
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-schema-registry group confluent
Notice: If you are planning to use the provided systemd service units for
Notice: confluent-schema-registry, make sure that read-write permissions
Notice: for user cp-schema-registry and group confluent are set up according to the
Notice: following commands:
chown cp-schema-registry:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent

Setting up confluent-kafka-connect-replicator (6.0.0-1) ...
Setting up confluent-ksqldb (6.0.0-1) ...
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-ksql group confluent
Creating directory /var/lib/kafka-streams with owner cp-ksql:confluent
Notice: If you are planning to use the provided systemd service units for
Notice: confluent-ksql, make sure that read-write permissions
Notice: for user cp-ksql and group confluent are set up according to the
Notice: following commands:
chown cp-ksql:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent

Setting up confluent-hub-client (6.0.0-1) ...
Setting up confluent-control-center (6.0.0-1) ...
Creating directory /var/lib/confluent/control-center with owner cp-control-center:confluent
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-control-center group confluent
Creating directory /var/log/confluent/control-center with owner cp-control-center:confluent
Notice: If you are planning to use the provided systemd service units for
Notice: confluent-control-center, make sure that read-write permissions
Notice: for user cp-control-center and group confluent are set up according to the
Notice: following commands:
chown cp-control-center:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent

Setting up confluent-ce-kafka-http-server (6.0.0-1) ...
Creating directory /var/lib/confluent/ce-kafka-http-server with owner cp-ce-kafka-http-server:confluent
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-ce-kafka-http-server group confluent
Creating directory /var/log/confluent/ce-kafka-http-server with owner cp-ce-kafka-http-server:confluent
Notice: If you are planning to use the provided systemd service units for
Notice: ce-kafka-http-server, make sure that read-write permissions
Notice: for user cp-ce-kafka-http-server and group confluent are set up according to the
Notice: following commands:
chown cp-ce-kafka-http-server:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent\n
Setting up confluent-server-rest (6.0.0-1) ...
Creating directory /var/lib/confluent/ce-kafka-rest with owner cp-ce-kafka-rest:confluent
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-ce-kafka-rest group confluent
Creating directory /var/log/confluent/ce-kafka-rest with owner cp-ce-kafka-rest:confluent
Notice: If you are planning to use the provided systemd service units for
Notice: ce-kafka-rest, make sure that read-write permissions
Notice: for user cp-ce-kafka-rest and group confluent are set up according to the
Notice: following commands:
chown cp-ce-kafka-rest:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent\n
Setting up confluent-platform (6.0.0-1) ...
Setting up confluent-server (6.0.0-1) ...
Creating directory /var/log/kafka with owner cp-kafka:confluent
Notice: Not creating existing directory /var/log/confluent, ensure proper permissions for user cp-kafka group confluent
Creating directory /var/lib/kafka with owner cp-kafka:confluent
Creating directory /var/lib/zookeeper with owner cp-kafka:confluent
Notice: If you are planning to use the provided systemd service units for
Notice: Kafka, ZooKeeper or Connect, make sure that read-write permissions
Notice: for user cp-kafka and group confluent are set up according to the
Notice: following commands:
chown cp-kafka:confluent /var/log/confluent && chmod u+wx,g+wx,o= /var/log/confluent
```

`consumer.properties` template is in `etc/kafka/consumer.properties`
```bash
cp /etc/kafka/consumer.properties ~/Pitt-Google-Broker/.
cd ~/Pitt-Google-Broker/
# edit consumer.properties to reflect settings from jupyter notebook
```


create `etc/kafka_client_jaas.conf ` containing
```
 KafkaClient {
    com.sun.security.auth.module.Krb5LoginModule required 
    useKeyTab=true 
    storeKeyTab=true 
    serviceName="kafka" 
    keyTab="~/Pitt-Google-Broker/pitt-reader.user.keytab" 
    principal="mirrormaker/public2.alerts.ztf.uw.edu@KAFKA.SECURE" 
    useTicketCache=false; 
};
```

run java command to set environ variable
```bash
KAFKA_OPTS=-Djava.security.auth.login.config=/etc/kafka_client_jaas.conf 
 # -javaagent:/opt/jmx_exporter/jmx_prometheus_javaagent.jar=private:8080:/etc/jmx_exporter/kafka.yml'
```

try running consumer from command line
```bash
cd /usr/bin # kafka-console-consumer is here
./kafka-console-consumer --bootstrap-server public2.alerts.ztf.uw.edu:9094 --topic ztf_20201013_programid1 --consumer.config ~/Pitt-Google-Broker/consumer.properties
```

getting error:
```
(base) troy_raen_pitt@cloudshell:/usr/bin (ardent-cycling-243415)$ ./kafka-console-consumer --bootstrap-server public2.alerts.ztf.uw.edu:9094 --topic ztf_20201013_programid1 --consumer.config ~/Pitt-Google-Broker/consumer.properties
[2020-10-19 20:17:48,015] ERROR Unknown error when running consumer:  (kafka.tools.ConsoleConsumer$)
org.apache.kafka.common.KafkaException: Failed to construct kafka consumer
	at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:823)
	at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:667)
	at kafka.tools.ConsoleConsumer$.run(ConsoleConsumer.scala:68)
	at kafka.tools.ConsoleConsumer$.main(ConsoleConsumer.scala:55)
	at kafka.tools.ConsoleConsumer.main(ConsoleConsumer.scala)
Caused by: java.lang.IllegalArgumentException: Could not find a 'KafkaClient' entry in the JAAS configuration. System property 'java.security.auth.login.config' is not set
	at org.apache.kafka.common.security.JaasContext.defaultContext(JaasContext.java:143)
	at org.apache.kafka.common.security.JaasContext.load(JaasContext.java:108)
	at org.apache.kafka.common.security.JaasContext.loadClientContext(JaasContext.java:94)
	at org.apache.kafka.common.network.ChannelBuilders.create(ChannelBuilders.java:134)
	at org.apache.kafka.common.network.ChannelBuilders.clientChannelBuilder(ChannelBuilders.java:73)
	at org.apache.kafka.clients.ClientUtils.createChannelBuilder(ClientUtils.java:105)
	at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:740)
	... 4 more
```

However, Christopher Phillips (ZTF) reset the consumer offsets and the python code is now working and receiving alerts. Trying to deploy the broker again.

<!-- fe install kafka directly and try to run from command line -->
