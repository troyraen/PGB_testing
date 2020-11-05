- [Install instructions](#instructions)
- [GCP Account Info](#gcpinfo)


<a name="instructions"></a>
# Personalized instructions to install the broker
<!-- fs -->
[Generic instructions from broker docs](https://pitt-broker.readthedocs.io/en/latest/installation.html#)

## Installing with Conda

Remove Conda environment:
```bash
conda remove --name PGB --all
```

Install:
```bash
conda create -n PGB python=3.7
conda activate PGB  # Activate the new environment
python setup.py install --user  # Install the package

OGdir=$(pwd)
cd $CONDA_PREFIX

# Create files to run on startup and exit
mkdir -p ./etc/conda/activate.d
mkdir -p ./etc/conda/deactivate.d
touch ./etc/conda/activate.d/env_vars.sh
touch ./etc/conda/deactivate.d/env_vars.sh

# Add environmental variables
echo 'export GOOGLE_CLOUD_PROJECT="ardent-cycling-243415"' >> ./etc/conda/activate.d/env_vars.sh
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/home/tjr63/PGB/repo/GCPauth_pitt-google-broker-prototype-0679b75dded0.json"' >> ./etc/conda/activate.d/env_vars.sh
echo 'export PGB_DATA_DIR="/home/tjr63/PGB/repo/broker/ztf_archive/data"' >> ./etc/conda/activate.d/env_vars.sh

echo 'unset GOOGLE_CLOUD_PROJECT' >> ./etc/conda/deactivate.d/env_vars.sh
echo 'unset GOOGLE_APPLICATION_CREDENTIALS' >> ./etc/conda/deactivate.d/env_vars.sh
echo 'unset PGB_DATA_DIR' >> ./etc/conda/deactivate.d/env_vars.sh

cd $OGdir
```

<!-- fe # Personalized instructions to install the broker -->


<a name="gcpinfo"></a>
# GCP Account Info
<!-- fs -->
Project name: pitt-google-broker-prototype
Project ID: ardent-cycling-243415
Project number: 591409139500

Service Account: tjraen-owner@ardent-cycling-243415.iam.gserviceaccount.com
project_id = 'ardent-cycling-243415'
topic_name = 'troy_test_topic'
subscription_name = 'troy_test_subscript'
<!-- fe # GCP Account Info -->
