#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from io import BytesIO
from fastavro import reader
from apache_beam import DoFn


class extractAlertDict(DoFn):
    def process(self, msg):
        # Extract the alert data bytes from msg -> [alertDict]
        with BytesIO(msg) as fin:
            return [r for r in reader(fin)]
