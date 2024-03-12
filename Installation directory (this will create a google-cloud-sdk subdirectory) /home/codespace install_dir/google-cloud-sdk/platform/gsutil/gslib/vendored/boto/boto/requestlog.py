import sys
from datetime import datetime
from threading import Thread
import Queue

from boto.utils import RequestHook
from boto.compat import long_type


class RequestLogger(RequestHook):
    """
    This class implements a request logger that uses a single thread to
    write to a log file.
    """
    def __init__(self, filename='/tmp/request_log.csv'):
        self.request_log_file = open(filename, 'w')
        self.request_log_queue = Queue.Queue(100)
        Thread(target=self._request_log_worker).start()

    def handle_request_data(self, request, response, error=False):
        len = 0 if error else response.getheader('Content-Length')
        now = datetime.now()
        time = now.strftime('%Y-%m-%d %H:%M:%S')
        td = (now - request.start_time)
        duration = (td.microseconds + long_type(td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

        # write output including timestamp, status code, response time, response size, request action
        self.request_log_queue.put("'%s', '%s', '%s', '%s', '%s'\n" % (time, response.status, duration, len, request.params['Action']))

    def _request_log_worker(self):
        while True:
            try:
                item = self.request_log_queue.get(True)
                self.request_log_file.write(item)
                self.request_log_file.flush()
                self.request_log_queue.task_done()
            except:
                import traceback
                traceback.print_exc(file=sys.stdout)
