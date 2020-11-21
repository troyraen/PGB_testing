# LSST Sample Alerts
[LEFT OFF HERE](#HERE)

- [Sample alert info](https://github.com/lsst-dm/sample_alert_info)
- [Alert packet utils](https://github.com/lsst/alert_packet)
- [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/)
    - Larger samples of alerts suitable for bulk analysis and scale testing are available; see [sample_alert_info](https://github.com/lsst-dm/sample_alert_info/) for locations from which alerts can be downloaded.
- [Bellm presentation](https://project.lsst.org/meetings/rubin2020/sites/lsst.org.meetings.rubin2020/files/Bellm_Rubin_alerts_200813.pdf) (contains links listed above)
- [DMTN-093: Design of the LSST Alert Distribution System](https://dmtn-093.lsst.io/#management-and-evolution)

# To Do

- [ ]  set up VM to run the `alert-stream-simulator` and publish to a topic
- [ ]  set up Dataflow job to listen to the stream
    - [ ]  ingest to GCS, BQ
    - [ ]  Salt2
    - [ ]  xmatch with vizier
    <!-- - connect/listen to the topic
        - from within the same VM (easier) or deploy broker as in production (more realistic) -->

# VM: Alert Stream Simulator
- Rubin
    - [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/) (instructions + repo)
- GCP
    - [Create VM instance](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create)
    - [Creating and configuring VM instances](https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance)
    - [Containers on Compute Engine](https://cloud.google.com/compute/docs/containers)
    - [Docker] [Install Docker Engine on Debian](https://docs.docker.com/engine/install/debian/)
    - [Python] [Install Python 3.7 on Debian 9](https://linuxize.com/post/how-to-install-python-3-7-on-debian-9/)
    - [Python] [Install Python 3.6.4 on Debian 9](https://www.rosehosting.com/blog/how-to-install-python-3-6-4-on-debian-9/)
    - [venv] [Using venv to isolate dependencies](https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv)
    - Dashboard
        - [Connect to VM instance](https://cloud.google.com/compute/docs/instances/connecting-to-instance#gcloud)
        - [Console VM instances](https://console.cloud.google.com/compute/)


<a name="HERE">LEFT OFF HERE</a>
- _"make: python: Command not found"_
- Writing /tmp/easy_install-mrhz_3ms/python-snappy-0.5.4/setup.cfg
Running python-snappy-0.5.4/setup.py -q bdist_egg --dist-dir /tmp/easy_install-mrhz_3ms/python-snappy-0.5.4/egg-dist-tmp-plaqkw8n
/usr/lib/python3.7/distutils/dist.py:274: UserWarning: Unknown distribution option: 'cffi_modules'
  warnings.warn(msg)
snappy/snappymodule.cc:28:10: fatal error: _Python.h: No such file or directory_
 #include "Python.h"

## Prereqs + Install
<!-- fs -->
__Create and connect to VM:__
```bash
# create VM instance
gcloud compute instances create rubin-stream-simulator \
    --zone=us-central1-a \
    --machine-type=n1-standard-1 \
    --service-account=591409139500-compute@developer.gserviceaccount.com \
    --scopes=cloud-platform \
    --metadata=google-logging-enabled=true

# connect to instance
gcloud compute ssh rubin-stream-simulator --project=ardent-cycling-243415 --zone=us-central1-a

# stop/delete an instance
gcloud compute instances delete rubin-stream-simulator --zone us-central1-a

```

__Install pre-reqs `alert-stream-simulator`__
```bash
sudo apt-get update && sudo apt-get upgrade

# conda env

# # install and create virtual env
# sudo apt-get install python3-venv
# python3 -m venv ass # alert stream simulator env
# source ass/bin/activate # activate alert stream simulator env

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


# install Docker (following link above)
# prereqs
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install \
    apt-transport-https ca-certificates gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88 # verify key
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) stable"
# install
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install docker-ce docker-ce-cli containerd.io
# test
sudo docker run hello-world # see quote below for further info

# install other dependencies
sudo apt-get install make git docker-compose libsnappy-dev
# sudo apt-get install python3-pip #python3-setuptools
# sudo pip3 uninstall fastavro
# pip3 install fastavro==0.23


```

"Docker Engine is installed and running. The docker group is created but no users are added to it. You need to use sudo to run Docker commands. Continue to [Linux postinstall](Docker Engine is installed and running. The docker group is created but no users are added to it. You need to use sudo to run Docker commands. Continue to Linux postinstall to allow non-privileged users to run Docker commands and for other optional configuration steps.) to allow non-privileged users to run Docker commands and for other optional configuration steps."


__Install `alert-stream-simulator`__
```bash
git clone https://github.com/lsst-dm/alert-stream-simulator.git
cd alert-stream-simulator
sudo make install
```
<!-- fe Prereqs + Install -->

## Run `alert-stream-simulator`
<!-- fs -->
```bash
# connect to the VM instance
gcloud compute ssh rubin-stream-simulator --project=ardent-cycling-243415 --zone=us-central1-a

cd alert-stream-simulator
docker-compose up
# "This will spin up several containers; once the log output dies down, the system should be up and running."
docker-compose ps
# "we expect to see "Up" for the "State" of all containers"

# create a stream
rubin-alert-sim create-stream --dst-topic=rubin_example data/rubin_single_ccd_sample.avro
# replay the stream every --repeat-interval [sec]
rubin-alert-sim --verbose play-stream \
    --src-topic=rubin_example \
    --dst-topic=rubin_example_stream \
    --repeat-interval=37
# "Connect your consumers to the --dst-topic to simulate receiving Rubin's alerts."
```
<!-- fe Run `alert-stream-simulator` -->



# Dataflow job
- [example] [`kafkataxi`](https://github.com/apache/beam/tree/master/sdks/python/apache_beam/examples/kafkataxi)
- [`apache_beam.io.kafka`](https://github.com/apache/beam/blob/master/sdks/python/apache_beam/io/kafka.py)


Check [alert-stream-simulator/#networking-and-osx](https://github.com/lsst-dm/alert-stream-simulator/#networking-and-osx) to figure out how to connect to stream from external machine.

```bash
# find ip address of alert-stream-simulator
gcloud compute instances list
```
