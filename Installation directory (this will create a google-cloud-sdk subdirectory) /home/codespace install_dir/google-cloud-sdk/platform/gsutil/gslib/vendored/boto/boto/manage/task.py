# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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
#

import boto
from boto.sdb.db.property import StringProperty, DateTimeProperty, IntegerProperty
from boto.sdb.db.model import Model
import datetime, subprocess, time
from boto.compat import StringIO

def check_hour(val):
    if val == '*':
        return
    if int(val) < 0 or int(val) > 23:
        raise ValueError

class Task(Model):

    """
    A scheduled, repeating task that can be executed by any participating servers.
    The scheduling is similar to cron jobs.  Each task has an hour attribute.
    The allowable values for hour are [0-23|*].

    To keep the operation reasonably efficient and not cause excessive polling,
    the minimum granularity of a Task is hourly.  Some examples:

         hour='*' - the task would be executed each hour
         hour='3' - the task would be executed at 3AM GMT each day.

    """
    name = StringProperty()
    hour = StringProperty(required=True, validator=check_hour, default='*')
    command = StringProperty(required=True)
    last_executed = DateTimeProperty()
    last_status = IntegerProperty()
    last_output = StringProperty()
    message_id = StringProperty()

    @classmethod
    def start_all(cls, queue_name):
        for task in cls.all():
            task.start(queue_name)

    def __init__(self, id=None, **kw):
        super(Task, self).__init__(id, **kw)
        self.hourly = self.hour == '*'
        self.daily = self.hour != '*'
        self.now = datetime.datetime.utcnow()

    def check(self):
        """
        Determine how long until the next scheduled time for a Task.
        Returns the number of seconds until the next scheduled time or zero
        if the task needs to be run immediately.
        If it's an hourly task and it's never been run, run it now.
        If it's a daily task and it's never been run and the hour is right, run it now.
        """
        boto.log.info('checking Task[%s]-now=%s, last=%s' % (self.name, self.now, self.last_executed))

        if self.hourly and not self.last_executed:
            return 0

        if self.daily and not self.last_executed:
            if int(self.hour) == self.now.hour:
                return 0
            else:
                return max( (int(self.hour)-self.now.hour), (self.now.hour-int(self.hour)) )*60*60

        delta = self.now - self.last_executed
        if self.hourly:
            if delta.seconds >= 60*60:
                return 0
            else:
                return 60*60 - delta.seconds
        else:
            if int(self.hour) == self.now.hour:
                if delta.days >= 1:
                    return 0
                else:
                    return 82800 # 23 hours, just to be safe
            else:
                return max( (int(self.hour)-self.now.hour), (self.now.hour-int(self.hour)) )*60*60

    def _run(self, msg, vtimeout):
        boto.log.info('Task[%s] - running:%s' % (self.name, self.command))
        log_fp = StringIO()
        process = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        nsecs = 5
        current_timeout = vtimeout
        while process.poll() is None:
            boto.log.info('nsecs=%s, timeout=%s' % (nsecs, current_timeout))
            if nsecs >= current_timeout:
                current_timeout += vtimeout
                boto.log.info('Task[%s] - setting timeout to %d seconds' % (self.name, current_timeout))
                if msg:
                    msg.change_visibility(current_timeout)
            time.sleep(5)
            nsecs += 5
        t = process.communicate()
        log_fp.write(t[0])
        log_fp.write(t[1])
        boto.log.info('Task[%s] - output: %s' % (self.name, log_fp.getvalue()))
        self.last_executed = self.now
        self.last_status = process.returncode
        self.last_output = log_fp.getvalue()[0:1023]

    def run(self, msg, vtimeout=60):
        delay = self.check()
        boto.log.info('Task[%s] - delay=%s seconds' % (self.name, delay))
        if delay == 0:
            self._run(msg, vtimeout)
            queue = msg.queue
            new_msg = queue.new_message(self.id)
            new_msg = queue.write(new_msg)
            self.message_id = new_msg.id
            self.put()
            boto.log.info('Task[%s] - new message id=%s' % (self.name, new_msg.id))
            msg.delete()
            boto.log.info('Task[%s] - deleted message %s' % (self.name, msg.id))
        else:
            boto.log.info('new_vtimeout: %d' % delay)
            msg.change_visibility(delay)

    def start(self, queue_name):
        boto.log.info('Task[%s] - starting with queue: %s' % (self.name, queue_name))
        queue = boto.lookup('sqs', queue_name)
        msg = queue.new_message(self.id)
        msg = queue.write(msg)
        self.message_id = msg.id
        self.put()
        boto.log.info('Task[%s] - start successful' % self.name)

class TaskPoller(object):

    def __init__(self, queue_name):
        self.sqs = boto.connect_sqs()
        self.queue = self.sqs.lookup(queue_name)

    def poll(self, wait=60, vtimeout=60):
        while True:
            m = self.queue.read(vtimeout)
            if m:
                task = Task.get_by_id(m.get_body())
                if task:
                    if not task.message_id or m.id == task.message_id:
                        boto.log.info('Task[%s] - read message %s' % (task.name, m.id))
                        task.run(m, vtimeout)
                    else:
                        boto.log.info('Task[%s] - found extraneous message, ignoring' % task.name)
            else:
                time.sleep(wait)






