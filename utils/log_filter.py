# -*- coding: utf-8 -*-

"""
Log Filter, color and disable head method
"""

import re

P_REQUEST_LOG = re.compile(r'^(.*?) - - \[(.*?)\] "(.*?)" (\d+) (\d+|-)$')

all_methods = ['PUT', 'POST', 'DELETE', 'GET']


class WerkzeugLogFilter(object):
    def filter(self, record):
        match = P_REQUEST_LOG.match(record.msg)
        if match:
            try:
                ip, date, request_line, status_code, size = match.groups()
                method = request_line.split(' ')[0]  # key 0 always exists
                if method in all_methods:
                    return record
                else:
                    return None
            except ValueError:
                pass
        return record

