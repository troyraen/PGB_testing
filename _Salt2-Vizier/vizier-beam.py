#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import logging
import apache_beam as beam
import apache_beam.transforms.window as window
from apache_beam.io import BigQueryDisposition as bqdisp
from apache_beam.io import ReadFromPubSub, Write, WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions
from astropy import units as u

from custommods.data_utils import extractAlertDict
from custommods import vizier_utils as vizutils


class windowXmatchVizier(beam.PTransform):
    """Batches the stream into fixed interval windows.
    Performs cross-match with Vizier.
    Returns PCollection of xmatch dicts (1 per alert) for upload to BigQuery.
    """

    def __init__(self, window_size, xmatchArgs):
        self.window_size = window_size  # seconds
        self.xmatchArgs = xmatchArgs  # dict

    def expand(self, alertDicts):
        """
        Args:
            alertDicts <PCollection>
        Returns:
            [xmatchDict,] <PCollection>
        """

        return (
            alertDicts
            | "Window into Fixed Intervals" >> beam.WindowInto(window.FixedWindows(self.window_size))
            # CombinePerKey groups by key and window, use dummy key
            | "Add Dummy Key" >> beam.Map(lambda elem: (None, elem))
            | "CombinePerKey alertDicts2AstropyTable" >> beam.CombinePerKey(vizutils.alertDicts2AstropyTable)
            | "Abandon Dummy Key" >> beam.MapTuple(lambda _, val: val)
            # do the cross match
            | "xmatchVizier" >> beam.ParDo(vizutils.xmatchVizier(**self.xmatchArgs))  # [xmatchDict,]
        )


def run(PROJECTID, input_PS_topic, output_BQ_table, window_size=900,
        xmatchArgs={}, pipeline_args=None):
    pipeline_options = PipelineOptions(
        pipeline_args, streaming=True, # save_main_session=True
    )

    with beam.Pipeline(options=pipeline_options) as pipeline:
        (
            pipeline
            | "ReadFromPubSub" >> ReadFromPubSub(topic=input_PS_topic)
            | 'extractAlertDict' >> beam.ParDo(extractAlertDict())
            | "windowXmatchVizier" >> windowXmatchVizier(window_size, xmatchArgs)
            | 'WriteToBigQuery' >> Write(WriteToBigQuery(
                                    output_BQ_table,
                                    project = PROJECTID,
                                    create_disposition = bqdisp.CREATE_NEVER,
                                    write_disposition = bqdisp.WRITE_APPEND,
                                    ))
        )


if __name__ == "__main__":  # noqa
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--PROJECTID",
        help="Google Cloud Platform project name.",
    )
    parser.add_argument(
        "--input_PS_topic",
        help="The Cloud Pub/Sub topic to read alerts from.\n"
        '"projects/<PROJECT_NAME>/topics/<TOPIC_NAME>".',
    )
    parser.add_argument(
        "--window_size",
        type=int,
        default=60,
        help="Batch the calls to Vizier by windowing alerts according to fixed interval window_size [sec].",
    )
    parser.add_argument(
        "--output_BQ_table",
        help="BigQuery table to store Vizier cross-matches in.",
    )
    parser.add_argument(
        "--vizierCat",
        default="vizier:II/246/out",
        help="Vizier catalog to cross-match against."
    )
    parser.add_argument(
        "--max_xm_distance",
        default=5,
        help="Max offset to check for cross-match. Will be converted to arcsec."
    )

    known_args, pipeline_args = parser.parse_known_args()

    # convert max_xm_distance to arcsec
    known_args.max_xm_distance = known_args.max_xm_distance*u.arcsec

    run(
        known_args.PROJECTID,
        known_args.input_PS_topic,
        known_args.output_BQ_table,
        known_args.window_size,
        {'vizierCat': known_args.vizierCat,
        'max_xm_distance': known_args.max_xm_distance},
        pipeline_args,
    )
