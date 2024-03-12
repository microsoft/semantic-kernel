#!/usr/bin/env python
# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import os
from datetime import datetime, timedelta
from boto.utils import parse_ts
import boto

class ResultProcessor(object):

    LogFileName = 'log.csv'

    def __init__(self, batch_name, sd, mimetype_files=None):
        self.sd = sd
        self.batch = batch_name
        self.log_fp = None
        self.num_files = 0
        self.total_time = 0
        self.min_time = timedelta.max
        self.max_time = timedelta.min
        self.earliest_time = datetime.max
        self.latest_time = datetime.min
        self.queue = self.sd.get_obj('output_queue')
        self.domain = self.sd.get_obj('output_domain')

    def calculate_stats(self, msg):
        start_time = parse_ts(msg['Service-Read'])
        end_time = parse_ts(msg['Service-Write'])
        elapsed_time = end_time - start_time
        if elapsed_time > self.max_time:
            self.max_time = elapsed_time
        if elapsed_time < self.min_time:
            self.min_time = elapsed_time
        self.total_time += elapsed_time.seconds
        if start_time < self.earliest_time:
            self.earliest_time = start_time
        if end_time > self.latest_time:
            self.latest_time = end_time

    def log_message(self, msg, path):
        keys = sorted(msg.keys())
        if not self.log_fp:
            self.log_fp = open(os.path.join(path, self.LogFileName), 'a')
            line = ','.join(keys)
            self.log_fp.write(line+'\n')
        values = []
        for key in keys:
            value = msg[key]
            if value.find(',') > 0:
                value = '"%s"' % value
            values.append(value)
        line = ','.join(values)
        self.log_fp.write(line+'\n')

    def process_record(self, record, path, get_file=True):
        self.log_message(record, path)
        self.calculate_stats(record)
        outputs = record['OutputKey'].split(',')
        if 'OutputBucket' in record:
            bucket = boto.lookup('s3', record['OutputBucket'])
        else:
            bucket = boto.lookup('s3', record['Bucket'])
        for output in outputs:
            if get_file:
                key_name = output.split(';')[0]
                key = bucket.lookup(key_name)
                file_name = os.path.join(path, key_name)
                print('retrieving file: %s to %s' % (key_name, file_name))
                key.get_contents_to_filename(file_name)
            self.num_files += 1

    def get_results_from_queue(self, path, get_file=True, delete_msg=True):
        m = self.queue.read()
        while m:
            if 'Batch' in m and m['Batch'] == self.batch:
                self.process_record(m, path, get_file)
                if delete_msg:
                    self.queue.delete_message(m)
            m = self.queue.read()

    def get_results_from_domain(self, path, get_file=True):
        rs = self.domain.query("['Batch'='%s']" % self.batch)
        for item in rs:
            self.process_record(item, path, get_file)

    def get_results_from_bucket(self, path):
        bucket = self.sd.get_obj('output_bucket')
        if bucket:
            print('No output queue or domain, just retrieving files from output_bucket')
            for key in bucket:
                file_name = os.path.join(path, key)
                print('retrieving file: %s to %s' % (key, file_name))
                key.get_contents_to_filename(file_name)
                self.num_files + 1

    def get_results(self, path, get_file=True, delete_msg=True):
        if not os.path.isdir(path):
            os.mkdir(path)
        if self.queue:
            self.get_results_from_queue(path, get_file)
        elif self.domain:
            self.get_results_from_domain(path, get_file)
        else:
            self.get_results_from_bucket(path)
        if self.log_fp:
            self.log_fp.close()
        print('%d results successfully retrieved.' % self.num_files)
        if self.num_files > 0:
            self.avg_time = float(self.total_time)/self.num_files
            print('Minimum Processing Time: %d' % self.min_time.seconds)
            print('Maximum Processing Time: %d' % self.max_time.seconds)
            print('Average Processing Time: %f' % self.avg_time)
            self.elapsed_time = self.latest_time-self.earliest_time
            print('Elapsed Time: %d' % self.elapsed_time.seconds)
            tput = 1.0 / ((self.elapsed_time.seconds/60.0) / self.num_files)
            print('Throughput: %f transactions / minute' % tput)

