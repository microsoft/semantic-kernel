# Copyright 2010 Google Inc.
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

"""
Test harness that allows us to raise exceptions, change file content,
and record the byte transfer callback sequence, to test various resumable
upload and download cases. The 'call' method of this harness can be passed
as the 'cb' parameter to boto.s3.Key.send_file() and boto.s3.Key.get_file(),
allowing testing of various file upload/download conditions.
"""

import socket
import time


class CallbackTestHarness(object):

    def __init__(self, fail_after_n_bytes=0, num_times_to_fail=1,
                 exception=socket.error('mock socket error', 0),
                 fp_to_change=None, fp_change_pos=None,
                 delay_after_change=None):
        self.fail_after_n_bytes = fail_after_n_bytes
        self.num_times_to_fail = num_times_to_fail
        self.exception = exception
        # If fp_to_change and fp_change_pos are specified, 3 bytes will be
        # written at that position just before the first exception is thrown.
        self.fp_to_change = fp_to_change
        self.fp_change_pos = fp_change_pos
        self.delay_after_change = delay_after_change
        self.num_failures = 0
        self.transferred_seq_before_first_failure = []
        self.transferred_seq_after_first_failure = []

    def call(self, total_bytes_transferred, unused_total_size):
        """
        To use this test harness, pass the 'call' method of the instantiated
        object as the cb param to the set_contents_from_file() or
        get_contents_to_file() call.
        """
        # Record transfer sequence to allow verification.
        if self.num_failures:
            self.transferred_seq_after_first_failure.append(
                total_bytes_transferred)
        else:
            self.transferred_seq_before_first_failure.append(
                total_bytes_transferred)
        if (total_bytes_transferred >= self.fail_after_n_bytes and
            self.num_failures < self.num_times_to_fail):
            self.num_failures += 1
            if self.fp_to_change and self.fp_change_pos is not None:
                cur_pos = self.fp_to_change.tell()
                self.fp_to_change.seek(self.fp_change_pos)
                self.fp_to_change.write('abc')
                self.fp_to_change.seek(cur_pos)
                if self.delay_after_change:
                    time.sleep(self.delay_after_change)
            self.called = True
            raise self.exception