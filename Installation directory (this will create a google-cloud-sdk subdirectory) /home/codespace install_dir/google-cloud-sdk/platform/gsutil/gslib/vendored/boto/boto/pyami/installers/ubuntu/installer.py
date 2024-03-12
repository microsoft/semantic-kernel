# Copyright (c) 2006,2007,2008 Mitch Garnaat http://garnaat.org/
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
import boto.pyami.installers
import os
import os.path
import stat
import boto
import random
from pwd import getpwnam

class Installer(boto.pyami.installers.Installer):
    """
    Base Installer class for Ubuntu-based AMI's
    """
    def add_cron(self, name, command, minute="*", hour="*", mday="*", month="*", wday="*", who="root", env=None):
        """
        Write a file to /etc/cron.d to schedule a command
            env is a dict containing environment variables you want to set in the file
            name will be used as the name of the file
        """
        if minute == 'random':
            minute = str(random.randrange(60))
        if hour == 'random':
            hour = str(random.randrange(24))
        fp = open('/etc/cron.d/%s' % name, "w")
        if env:
            for key, value in env.items():
                fp.write('%s=%s\n' % (key, value))
        fp.write('%s %s %s %s %s %s %s\n' % (minute, hour, mday, month, wday, who, command))
        fp.close()

    def add_init_script(self, file, name):
        """
        Add this file to the init.d directory
        """
        f_path = os.path.join("/etc/init.d", name)
        f = open(f_path, "w")
        f.write(file)
        f.close()
        os.chmod(f_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        self.run("/usr/sbin/update-rc.d %s defaults" % name)

    def add_env(self, key, value):
        """
        Add an environemnt variable
        For Ubuntu, the best place is /etc/environment.  Values placed here do
        not need to be exported.
        """
        boto.log.info('Adding env variable: %s=%s' % (key, value))
        if not os.path.exists("/etc/environment.orig"):
            self.run('cp /etc/environment /etc/environment.orig', notify=False, exit_on_error=False)
        fp = open('/etc/environment', 'a')
        fp.write('\n%s="%s"' % (key, value))
        fp.close()
        os.environ[key] = value

    def stop(self, service_name):
        self.run('/etc/init.d/%s stop' % service_name)

    def start(self, service_name):
        self.run('/etc/init.d/%s start' % service_name)

    def create_user(self, user):
        """
        Create a user on the local system
        """
        self.run("useradd -m %s" % user)
        usr = getpwnam(user)
        return usr

    def install(self):
        """
        This is the only method you need to override
        """
        raise NotImplementedError
