#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import logging
from tempfile import SpooledTemporaryFile
import fastavro as fa
from apache_beam import DoFn


class ExtractAlertData(DoFn):
    def process(self, msg):

        # Extract the alert data from msg -> dict
        maxsize = 1500000
        with SpooledTemporaryFile(max_size=maxsize, mode='w+b') as temp_file:
            temp_file.write(msg.data)
            temp_file.seek(0)
            alertDicts = [r for r in fa.reader(temp_file)]

        candid = alertDicts[0]['candid']
        logging.info(f'Extracted alert data dict for candid {candid}')

        return alertDicts
