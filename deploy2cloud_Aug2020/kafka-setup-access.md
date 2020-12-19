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
## Install on a Google Compute Engine VM using the prepackaged, "Click to Deploy" stack on the Google Marketplace
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

```

_[ToDo:] Create an "image" or a "machine image" of this VM and figure out how to use it to deploy a new ZTF consumer daily._

<!-- fe # Install on a Google Compute Engine VM -->

<a name="config"></a>
## Configure Kafka for ZTF access
<!-- fs -->

1. Find out where Kafka is installed.
On the VM using Marketplace, it is in `/opt/kafka`.
Otherwise, try `/etc/kafka`.
The following assumes we are on the VM using the Marketplace stack.

2. This requires two authorization files:
    1. `krb5.conf`, which should be at `/opt/krb5.conf`
    2. `pitt-reader.user.keytab`. I store this in the directory `~/consume-ztf`; we need the path for config below.

3. Create `/opt/kafka_client_jaas.conf ` containing:

```
KafkaClient {
com.sun.security.auth.module.Krb5LoginModule required 
useKeyTab=true 
storeKeyTab=true 
debug=true
serviceName="kafka" 
keyTab="~/consume-ztf/pitt-reader.user.keytab" 
principal="mirrormaker/public2.alerts.ztf.uw.edu@KAFKA.SECURE" 
useTicketCache=false; 
};
```

4. ~Run java command to set environ variable~

<!-- Instead of doing this, I had to put the path in `consumer.properties` (below). -->

```bash
export KAFKA_OPTS="-Djava.security.auth.login.config=/opt/kafka_client_jaas.conf "
  # -Djava.security.krb5.conf=/opt/krb5.conf"
 # -javaagent:/opt/jmx_exporter/jmx_prometheus_javaagent.jar=private:8080:/etc/jmx_exporter/kafka.yml'

  -Djava.security.krb5.conf=/etc/krb5.conf

# KAFKA_OPTS=java.security.auth.login.config=/opt/kafka_client_jaas.conf 
# System.setProperty("java.security.auth.login.config","/opt/kafka_client_jaas.conf ")

```


4. Setup the Kafka config file `consumer.properties`.
Sample config files are provided with the installation in `/opt/kafka/config`.
Copy `consumer.properties` into a dir you want to work in.
Edit/add the following parameters:

```bash
bootstrap.servers=public2.alerts.ztf.uw.edu:9094
group.id=group
session.timeout.ms=6000
enable.auto.commit=False
sasl.kerberos.kinit.cmd='kinit -t "%{sasl.kerberos.keytab}" -k %{sasl.kerberos.principal}',
sasl.kerberos.service.name=kafka
security.protocol=SASL_PLAINTEXT
sasl.mechanisms=GSSAPI
auto.offset.reset=earliest
sasl.kerberos.principal=pitt-reader@KAFKA.SECURE
sasl.kerberos.keytab=~/consume-ztf/pitt-reader.user.keytab  # THIS MUST POINT AT YOUR KEYTAB AUTHORIZATION FILE
# sasl.jaas.config=/opt/kafka_client_jaas.conf  # THIS MUST POINT AT THE FILE CREATED ABOVE
```


<!-- fe Configure Kafka for ZTF access  -->

<a name="run-consumer"></a>
## Run the Kafka Consumer
<!-- fs -->
The following assumes we are on the VM using the Marketplace stack.
Kafka is installed at `/opt/kafka` (otherwise, look in `/etc/kafka`)

```bash
cd /opt/kafka/bin
./kafka-console-consumer.sh --bootstrap-server public2.alerts.ztf.uw.edu:9094 --topic ztf_20201018_programid1 --consumer.config ~/consume-ztf/consumer.properties
# final argument should point to the consumer.properties file created above
```

This gives the error:
```bash
troy_raen_pitt@kafka-1-vm:/opt/kafka/bin$ ./kafka-console-consumer.sh --bootstrap-server public2.alerts.ztf.u
w.edu:9094 --topic ztf_20201018_programid1 --consumer.config ~/consume-ztf/consumer.properties
Debug is  true storeKey false useTicketCache false useKeyTab true doNotPrompt false ticketCache is null isIni
tiator true KeyTab is ~/consume-ztf/pitt-reader.user.keytab refreshKrb5Config is false principal is mirrormak
er/public2.alerts.ztf.uw.edu@KAFKA.SECURE tryFirstPass is false useFirstPass is false storePass is false clea
rPass is false
Key for the principal mirrormaker/public2.alerts.ztf.uw.edu@KAFKA.SECURE not available in ~/consume-ztf/pitt-
reader.user.keytab
                [Krb5LoginModule] authentication failed
Could not login: the client is being asked for a password, but the Kafka client code does not currently suppo
rt obtaining a password from the user. not available to garner  authentication information from the user
[2020-12-19 06:20:04,683] ERROR Unknown error when running consumer:  (kafka.tools.ConsoleConsumer$)
org.apache.kafka.common.KafkaException: Failed to construct kafka consumer
        at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:825)
        at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:666)
        at kafka.tools.ConsoleConsumer$.run(ConsoleConsumer.scala:67)
        at kafka.tools.ConsoleConsumer$.main(ConsoleConsumer.scala:54)
        at kafka.tools.ConsoleConsumer.main(ConsoleConsumer.scala)
Caused by: org.apache.kafka.common.KafkaException: javax.security.auth.login.LoginException: Could not login: the client is being asked for a password, but the Kafka client code does not currently support obtaining a password from the user. not available to garner  authentication information from the user
        at org.apache.kafka.common.network.SaslChannelBuilder.configure(SaslChannelBuilder.java:172)
        at org.apache.kafka.common.network.ChannelBuilders.create(ChannelBuilders.java:157)
        at org.apache.kafka.common.network.ChannelBuilders.clientChannelBuilder(ChannelBuilders.java:73)
        at org.apache.kafka.clients.ClientUtils.createChannelBuilder(ClientUtils.java:105)
        at org.apache.kafka.clients.consumer.KafkaConsumer.<init>(KafkaConsumer.java:743)
        ... 4 more
Caused by: javax.security.auth.login.LoginException: Could not login: the client is being asked for a password, but the Kafka client code does not currently support obtaining a password from the user. not available to garner  authentication information from the user
        at com.sun.security.auth.module.Krb5LoginModule.promptForPass(Krb5LoginModule.java:944)
        at com.sun.security.auth.module.Krb5LoginModule.attemptAuthentication(Krb5LoginModule.java:764)
        at com.sun.security.auth.module.Krb5LoginModule.login(Krb5LoginModule.java:618)
        at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
        at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
        at java.lang.reflect.Method.invoke(Method.java:498)
        at javax.security.auth.login.LoginContext.invoke(LoginContext.java:755)
        at javax.security.auth.login.LoginContext.access$000(LoginContext.java:195)
        at javax.security.auth.login.LoginContext$4.run(LoginContext.java:682)
        at javax.security.auth.login.LoginContext$4.run(LoginContext.java:680)
        at java.security.AccessController.doPrivileged(Native Method)
        at javax.security.auth.login.LoginContext.invokePriv(LoginContext.java:680)
        at javax.security.auth.login.LoginContext.login(LoginContext.java:587)
        at org.apache.kafka.common.security.authenticator.AbstractLogin.login(AbstractLogin.java:60)
        at org.apache.kafka.common.security.kerberos.KerberosLogin.login(KerberosLogin.java:103)
        at org.apache.kafka.common.security.authenticator.LoginManager.<init>(LoginManager.java:62)
        at org.apache.kafka.common.security.authenticator.LoginManager.acquireLoginManager(LoginManager.java:112)
        at org.apache.kafka.common.network.SaslChannelBuilder.configure(SaslChannelBuilder.java:158)
        ... 8 more
troy_raen_pitt@kafka-1-vm:/opt/kafka/bin$
```

<!-- fe Run the Kafka Consumer -->
