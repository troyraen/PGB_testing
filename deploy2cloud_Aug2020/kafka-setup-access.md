- [GCP Console: Deployments](https://console.cloud.google.com/dm/deployments)
- `gcloud beta compute ssh --zone "us-west3-c" "kafka-1-vm" --project "ardent-cycling-243415"`
- `gcloud compute instances stop kafka-1-vm --zone us-west3-c`

---

# Kafka Install, Configuration, & Access

- Install Kafka:
    - [on a local machine.](#local-install)
    - [on a Google Compute Engine VM using the prepackaged, "Click to Deploy" stack the Google Marketplace.](#gce-marketplace-install)
- [Configure Kafka for ZTF access.](#config)
- [Run the Kafka Consumer](#run-consumer)
- Access the GCE VM Kafka server I've set up for testing purposes.

---

<a name="local-install"></a>
## Install Kafka on a local machine
<!-- fs -->

1. Install the `Java Development Kit (JDK)`. Debian 10 instructions are [here](https://www.digitalocean.com/community/tutorials/how-to-install-java-with-apt-on-debian-10). From that page you can select different versions or distributions.
    - Be sure to set the `JAVA_HOME` environment variable; instructions at the bottom of the page linked above.

2. Install the `Confluent Platform`. Follow the instructions in the "Get the Software" section of [this page](https://docs.confluent.io/platform/current/installation/installing_cp/deb-ubuntu.html). Those instructions are for Ubuntu and Debian.See links on LHS of the page for RHEL, CentOS, or Docker installs.
    - Note that we really only need the `Kafka` package, but I wasn't able to get that to install by itself, so I just installed the entire platform (likely just user error, but I didn't spend much time tracking it down). Entire platform includes (e.g.,) ZooKeeper, which is only needed for Publishers, not Consumers.

<!-- fe Install and configure Kafka on a local machine -->


<a name="gce-marketplace-install"></a>
## Install Kafka on a Google Compute Engine VM using the prepackaged, "Click to Deploy" stack on the Google Marketplace
<!-- fs -->

1. Go to the [Kafka, Click to Deploy stack on Google Marketplace](https://console.cloud.google.com/marketplace/product/click-to-deploy-images/kafka?q=kafka&id=f19a0f63-fc57-47fd-9d94-8d5ca6af935e&project=ardent-cycling-243415&folder=&organizationId=)
2. Click "Launch", fill in VM configuration info
    - This will spin up a VM and install Kafka, Java, and other necessary packages.

You can view the deployment at [GCP Console: Deployments](https://console.cloud.google.com/dm/deployments)

Helpful notice from GCP:
__"Kafka has been installed into /opt/kafka. Here you will find kafka config files and provided scripts. Documentation on configuration can be found [here](https://www.google.com/url?q=https%3A%2F%2Fkafka.apache.org%2Fdocumentation%2F%23configuration). You can also restart the kafka server by running the below command."__
```bash
sudo systemctl restart kafka
```

`ssh` into the VM from the GCP Console Deployments or VM instances pages, or the following:
```bash
gcloud beta compute ssh --zone "us-west3-c" "kafka-1-vm" --project "ardent-cycling-243415"
```

Set `JAVA_HOME` env variable following instructions in doc linked in previous section.

_[ToDo:] Create an "image" or a "machine image" of this VM and figure out how to use it to deploy a new ZTF consumer daily._

<!-- fe # Install on a Google Compute Engine VM -->

<a name="config"></a>
## Configure Kafka for ZTF access
<!-- fs -->
Following instructions:
- [Kafka Consumer Configs](https://kafka.apache.org/documentation/#consumerconfigs)
- [SASL configuration for Kafka Clients](https://docs.confluent.io/3.0.0/kafka/sasl.html#sasl-configuration-for-kafka-clients)
- [Confluent Kafka Consumer](https://docs.confluent.io/platform/current/clients/consumer.html)
- info I got from Christopher Phillips over phone/email.

1. Find out where Kafka is installed.
On the VM using Marketplace, it is in `/opt/kafka`.
Otherwise, try `/etc/kafka`.
The following assumes we are on the VM using the Marketplace stack.

2. This requires two authorization files:
    1. `krb5.conf`, which should be at `/etc/krb5.conf`
    2. `pitt-reader.user.keytab`. I store this in the directory `/home/troy_raen_pitt/consume-ztf`; we need the path for config below.

3. Create `/opt/kafka/kafka_client_jaas.conf ` containing:
```
KafkaClient {
    com.sun.security.auth.module.Krb5LoginModule required 
    useKeyTab=true 
    storeKeyTab=true 
    debug=true
    serviceName="kafka" 
    keyTab="/home/troy_raen_pitt/consume-ztf/pitt-reader.user.keytab" 
    principal="pitt-reader@KAFKA.SECURE" 
    useTicketCache=false; 
};
```

Note: original instructions from Christopher said to use
`principal="mirrormaker/public2.alerts.ztf.uw.edu@KAFKA.SECURE" `,
but when I used that, running the console consumer (below) => complained of being asked for a password. [This answer](https://help.mulesoft.com/s/article/javax-security-auth-login-LoginException-Could-not-login-the-client-is-being-asked-for-a-password) led me to look at this `prinicpal` line and compare it to the consumer config, which has `sasl.kerberos.principal=pitt-reader@KAFKA.SECURE`. Changing the above to match.


4. Run java command to set environ variable
```bash
export KAFKA_OPTS="-Djava.security.auth.login.config=/opt/kafka/kafka_client_jaas.conf "
```


5. Setup the Kafka config file `consumer.properties`.
Sample config files are provided with the installation in `/opt/kafka/config/`.
Copy `consumer.properties` into a dir you want to work in (the following uses `/home/troy_raen_pitt/consume-ztf/`).
Edit/add the following parameters:
```bash
bootstrap.servers=public2.alerts.ztf.uw.edu:9094
group.id=group
session.timeout.ms=6000
enable.auto.commit=False
sasl.kerberos.kinit.cmd='kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}'
sasl.kerberos.service.name=kafka
security.protocol=SASL_PLAINTEXT
sasl.mechanism=GSSAPI
auto.offset.reset=earliest
```

<!-- fe Configure Kafka for ZTF access  -->

<a name="run-consumer"></a>
## Run the Kafka Consumer
<!-- fs -->
The following assumes we are using the VM set up with the Marketplace stack.

`ssh` into the machine:
```bash
gcloud beta compute ssh --zone "us-west3-c" "kafka-1-vm" --project "ardent-cycling-243415"
```

Kafka is installed at `/opt/kafka` (on a different machine, look in `/etc/kafka`)

```bash
export KAFKA_OPTS="-Djava.security.auth.login.config=/opt/kafka/kafka_client_jaas.conf "
cd /opt/kafka/bin

topicday=20201018
./kafka-console-consumer.sh --bootstrap-server public2.alerts.ztf.uw.edu:9094 --topic ztf_${topicday}_programid1 --consumer.config /home/troy_raen_pitt/consume-ztf/consumer.properties
# final argument should point to the consumer.properties file created above
```

If I pass an incorrect topic, I get an error saying I don't have access to that topic.
If I pass a correct topic, it _seems_ to work, but hangs without printing out an alert msg.

<!-- fe Run the Kafka Consumer -->
