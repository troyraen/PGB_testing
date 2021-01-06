#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""The ``setup_gcp`` module sets up services on the Google Cloud Platform (GCP
project for use by the parent package. Setup tasks can be run individually or
collectively using the ``auto_setup`` function. Each task should only have to
be run once for a given GCP project.

Usage Example
-------------

.. code-block:: python
   :linenos:

   from broker import gcp_setup

   # Tasks can be run individually
   gcp_setup.setup_big_query
   gcp_setup.setup_buckets
   gcp_setup.setup_logging_sinks

   # Tasks can also be run as a collective set.
   gcp_setup.auto_setup


Module Documentation
--------------------
"""

import os
from pathlib import Path

if not os.getenv('GPB_OFFLINE', False):
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery, pubsub, logging, storage

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

_tables = ('alerts', 'test_GCS_to_BQ')


def setup_big_query() -> None:
    """Create the necessary Big Query datasets if they do not already exist

    New datasets include:
      ``ztf_alerts``
      ``testing_dataset``
    """

    bigquery_client = bigquery.Client()
    bigquery_client.create_dataset('ztf_alerts', exists_ok=True)
    bigquery_client.create_dataset('testing_dataset', exists_ok=True)


def setup_buckets() -> None:
    """Create new storage buckets and upload testing files.
    Files are expected to reside in the ``tests/test_alerts`` directory.

    New buckets [files] include:
      ``<PROJECT_ID>_ztf_alert_avro_bucket``
      ``<PROJECT_ID>_testing_bucket`` [``ztf_3.3_validschema_1154446891615015011.avro``]
    """

    buckets = {  # '<bucket name>': ['file name',]
                # f'{PROJECT_ID}_ztf_alert_avro_bucket': [],
                # f'{PROJECT_ID}_testing_bucket':
                    # ['ztf_3.3_validschema_1154446891615015011.avro']
                f'{PROJECT_ID}-broker_files':
                    ['consumer/vm_install.sh',
                     'consumer/vm_startup.sh',
                     'consumer/ps-connector.properties',
                     'consumer/psconnect-worker.properties'],
                }

    storage_client = storage.Client()

    for bucket_name, files in buckets.items():
        # Create buckets if they do not exist
        try:
            storage_client.get_bucket(bucket_name)
        except NotFound:
            storage_client.create_bucket(bucket_name)

        # Upload any files
        for filename in files:
            bucket = storage_client.get_bucket(bucket_name)
            blob = bucket.blob(filename)
            # inpath = Path('tests/test_alerts') / filename
            inpath = Path(__file__) / filename
            with inpath.open('rb') as infile:
                blob.upload_from_file(infile)


def setup_pubsub() -> None:
    """ Create new Pub/Sub topics and subscriptions

    New topics [subscriptions] include:
        ``ztf_alert_data``
        ``ztf_alert_avro_in_bucket``
        ``ztf_alerts_in_BQ``
        ``test_alerts_in_BQ``
        ``test_alerts_PS_publish`` [``test_alerts_PS_subscribe``]
    """

    topics = {# '<topic_name>': ['<subscription_name>', ]
                'ztf_alert_data':
                    ['ztf_alert_data-counter'],
                'ztf_alert_avro_bucket':
                    ['ztf_alert_avro_bucket-counter'],
                'ztf_exgalac_trans':
                    ['ztf_exgalac_trans-counter'],
                'ztf_salt2-counter':
                    ['ztf_salt2-counter'],
                'test_alerts_in_BQ': [],
                'test_alerts_PS_publish': ['test_alerts_PS_subscribe'],
                }

    publisher = pubsub.PublisherClient()
    subscriber = pubsub.SubscriberClient()

    for topic, subscriptions in topics.items():
        topic_path = publisher.topic_path(PROJECT_ID, topic)

        # Create the topic
        try:
            publisher.get_topic(topic_path)
        except NotFound:
            publisher.create_topic(topic_path)

        # Create any subscriptions:
        for sub_name in subscriptions:
            sub_path = subscriber.subscription_path(PROJECT_ID, sub_name)
            try:
                subscriber.get_subscription(sub_path)
            except NotFound:
                subscriber.create_subscription(sub_path, topic_path)


def setup_logging_sinks() -> None:
    """Create sinks for exporting log entries to GCP

    This function assumes destination buckets have already been created.

    New Sinks include:
      ``broker_logging_sink``
    """

    # Define logging sink
    logging_client = logging.Client()
    logging_sink_name = 'logging_sink'
    sink = logging_client.sink(logging_sink_name)

    # Create sink if not exists
    if not sink.exists():
        sink.create()


def auto_setup() -> None:
    """Create and setup GCP products required by the ``broker`` package

    New data sets include:
        ``ztf_alerts``
        ``testing_dataset``

    New buckets include:
        ``<PROJECT_ID>_ztf_alert_avro_bucket``
        ``<PROJECT_ID>_testing_bucket``

    New topics include:
        ``ztf_alerts_in_BQ``
        ``test_alerts_in_BQ``

    New sinks include:
        ``broker_logging_sink``
    """

    setup_big_query()
    setup_buckets()
    setup_pubsub()
    setup_logging_sinks()

if __name__ == "__main__":
    auto_setup()
