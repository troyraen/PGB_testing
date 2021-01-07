# Daily tasks to cleanup yesterday's consumer and deploy today's consumer
The intention is for the following to be automated.

- [Replaying and purging messages](https://cloud.google.com/pubsub/docs/replay-overview)
- [Quickstart: replaying messages](https://cloud.google.com/pubsub/docs/replay-qs)


## Cleanup yesterday's consumer
1. stop yesterday's Kafka -> PS connector
2. stop the kafka-consumer VM
```bash
gcloud beta compute ssh kafka-consumer --zone us-central1-a
gcloud beta compute instances stop kafka-consumer --zone us-central1-a
```

## Start today's consumer
1. Reset Pub/Sub messages counters by [seeking subscriptions](https://cloud.google.com/sdk/gcloud/reference/alpha/pubsub/subscriptions/seek) to the current time. `projects/ardent-cycling-243415/subscriptions/`
    - `ztf_alert_data-counter`
    - `ztf_alert_avro_bucket-counter`
    - `ztf_exgalac_trans-counter`
    - `ztf_salt2-counter`

```bash
./start-night.sh
```

2. Start the Dataflow jobs
```bash
cd broker/beam
# use the readme to set the configs and start the jobs
```

3. Start the Kafka -> Pub/Sub connector
```bash
# start the vm and log in
gcloud beta compute instances start kafka-consumer --zone us-central1-a
gcloud beta compute ssh kafka-consumer --zone us-central1-a

# update the date for the current topic
sudo nano /home/troy_raen_pitt/consume-ztf/ps-connector.properties

cd /bin
screen
./connect-standalone \
    /home/troy_raen_pitt/consume-ztf/psconnect-worker.properties \
    /home/troy_raen_pitt/consume-ztf/ps-connector.properties
```
