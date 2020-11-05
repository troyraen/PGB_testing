# LSST Sample Alerts

- [Sample alert info](https://github.com/lsst-dm/sample_alert_info)
- [Alert packet utils](https://github.com/lsst/alert_packet)
- [Alert stream simulator](https://github.com/lsst-dm/alert-stream-simulator/)
- [Bellm presentation](https://project.lsst.org/meetings/rubin2020/sites/lsst.org.meetings.rubin2020/files/Bellm_Rubin_alerts_200813.pdf) (contains links listed above)


# To Do

- set up VM to run alert stream simulator and publish to a topic
- connect/listen to the topic
    - from within the same VM (easier) or deploy broker as in production (more realistic)
- ingest to GCS, BQ
- classify?
- xmatch with vizier?
