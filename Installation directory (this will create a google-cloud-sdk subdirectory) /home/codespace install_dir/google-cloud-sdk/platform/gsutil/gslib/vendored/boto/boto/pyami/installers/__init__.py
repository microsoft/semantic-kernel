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
from boto.pyami.scriptbase import ScriptBase


class Installer(ScriptBase):
    """
    Abstract base class for installers
    """

    def add_cron(self, name, minute, hour, mday, month, wday, who, command, env=None):
        """
        Add an entry to the system crontab.
        """
        raise NotImplementedError

    def add_init_script(self, file):
        """
        Add this file to the init.d directory
        """

    def add_env(self, key, value):
        """
        Add an environemnt variable
        """
        raise NotImplementedError

    def stop(self, service_name):
        """
        Stop a service.
        """
        raise NotImplementedError

    def start(self, service_name):
        """
        Start a service.
        """
        raise NotImplementedError

    def install(self):
        """
        Do whatever is necessary to "install" the package.
        """
        raise NotImplementedError
