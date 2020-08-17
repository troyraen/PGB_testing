# Pre-meeting To do list
- [ ]  in `_avro2BQ`, see Not yet done section
- [ ]  are readthedocs up to date?
    - [ ]  alert_ingestion.rst
- [ ]  pull request conflict file `broker/alert_ingestion/GCS_to_BQ/main.py`


# Status check

1. Recommendation: "Switch VM resources with high CPU or memory usage to a recommended machine type." [here](https://console.cloud.google.com/home/recommendations?project=ardent-cycling-243415)
2. VM logs No module named `broker.consumer` from `consume_ztf.py`
3. environment variables not found

Deleting all GCP resources and trying to deploy the broker from scratch.

# Deploying the Broker

[Install Docker on a Mac](https://runnable.com/docker/install-docker-on-macos)

```bash
pgbenv
cd /Users/troyraen/Documents/PGB/repo/docker_files

docker build -t consume_ztf.image -f consume_ztf.Dockerfile /Users/troyraen/Documents/PGB/repo/docker_files

# get HOSTNAME
# https://cloud.google.com/container-registry/docs/pushing-and-pulling#pushing_an_image_to_a_registry
# using us.gcr.io

# get git commit hash to use a version number
git log -1 --format=format:"%H" docker_files/consume_ztf.Dockerfile
# copy this to replace [VERSION] in the command
# docker tag [IMAGENAME] [HOSTNAME]/[PROJECT-ID]/[IMAGENAME]:[VERSION]

docker tag consume_ztf.image gcr.io/ardent-cycling-243415/consume_ztf.image:b43d5f0e534d9d7795d0ceb12e18bead854072c9

docker push gcr.io/ardent-cycling-243415/consume_ztf.image

## I wasn't able to get the image to create, probably due to resource issues
## on my machine. Daniel finished the creation and push of the image

# Deploy using scheduleinstance.sh
cd /Users/troyraen/Documents/PGB/repo/broker/cloud_functions
./scheduleinstance.sh

# chose no to the question
# Allow unauthenticated invocations of new function
```

This is not running because it can't find the authentication files.

Solution: package the files with the Dockerimage

For the service account credentials:

# Service Account Credentials (8/17/20)

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
