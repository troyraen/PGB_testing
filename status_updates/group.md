# Alert Stream Broker Updates

## Dec 4, 2020

__Question:__

1. submitting a correction to [alert-stream-simulator#writing-your-own-consumer](https://github.com/lsst-dm/alert-stream-simulator#writing-your-own-consumer)

__Upcoming:__

2. Rubin LSST alert broker proposal due __Dec. 15__

__ZTF Alert Stream Consumer:__ [[Dashboard](https://console.cloud.google.com/monitoring/dashboards/builder/3a371dcb-42d1-4ea0-add8-141d025924f6?project=ardent-cycling-243415&dashboardBuilderState=%257B%2522editModeEnabled%2522:false%257D&timeDomain=1d) ]

3. on Nov 30th, 'magically' regained access to streams starting with Nov 25th.
    - currently ingesting 2 days at a time
4. Rewriting workflow -> Apache Beam pipeline (w/ Dataflow runner)
    - will attempt 1st run this weekend

__Salt2 fits:__

5. [done] Successfully fit ZTF alerts! [[Dataflow job](https://console.cloud.google.com/dataflow/jobs/us-central1/2020-12-03_20_59_17-16682442575249541749;step=?project=ardent-cycling-243415)]
    - fit params stored in BigQuery db
    - lightcurve figure png stored in GCS bucket

__Cross matching with Vizier service:__

6. Haven't tried yet (recently). Will try (briefly) this weekend.

__Rubin LSST simulated alerts:__ [[Dashboard](https://console.cloud.google.com/monitoring/dashboards/builder/a431efde-cc61-49db-939c-fb3b9715eb4b?dashboardBuilderState=%257B%2522editModeEnabled%2522:false%257D&project=ardent-cycling-243415&timeDomain=1d) ]

7. [done] Alert Stream Simulator:
    - Successfully running (publishing public Kafka stream) [[VM Dashboard](https://console.cloud.google.com/monitoring/dashboards/resourceDetail/gce_instance,project_id:ardent-cycling-243415,zone:us-central1-a,instance_id:30795360064810098?project=ardent-cycling-243415&timeDomain=1d)]
8. Ingest the stream:
    - Trouble reading the alert packets in Beam pipeline (`cannot encode a null byte`). Instead:
    1. [done] Wrote simple consumer to:
        - listen to Kafka stream
        - extract alert data
        - store as Avro file in GCS bucket
        - publish alert (bytes) to PubSub stream
    2. Writing Beam pipeline to:
        - listen to PubSub stream
        - parse the alert
        - write to BigQuery table
        - data processing??? (random data in simulated alerts)
