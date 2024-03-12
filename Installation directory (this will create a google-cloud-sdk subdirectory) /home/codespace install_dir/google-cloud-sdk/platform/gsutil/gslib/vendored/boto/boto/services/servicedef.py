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

from boto.pyami.config import Config
from boto.services.message import ServiceMessage
import boto

class ServiceDef(Config):

    def __init__(self, config_file, aws_access_key_id=None, aws_secret_access_key=None):
        super(ServiceDef, self).__init__(config_file)
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        script = Config.get(self, 'Pyami', 'scripts')
        if script:
            self.name = script.split('.')[-1]
        else:
            self.name = None


    def get(self, name, default=None):
        return super(ServiceDef, self).get(self.name, name, default)

    def has_option(self, option):
        return super(ServiceDef, self).has_option(self.name, option)

    def getint(self, option, default=0):
        try:
            val = super(ServiceDef, self).get(self.name, option)
            val = int(val)
        except:
            val = int(default)
        return val

    def getbool(self, option, default=False):
        try:
            val = super(ServiceDef, self).get(self.name, option)
            if val.lower() == 'true':
                val = True
            else:
                val = False
        except:
            val = default
        return val

    def get_obj(self, name):
        """
        Returns the AWS object associated with a given option.

        The heuristics used are a bit lame.  If the option name contains
        the word 'bucket' it is assumed to be an S3 bucket, if the name
        contains the word 'queue' it is assumed to be an SQS queue and
        if it contains the word 'domain' it is assumed to be a SimpleDB
        domain.  If the option name specified does not exist in the
        config file or if the AWS object cannot be retrieved this
        returns None.
        """
        val = self.get(name)
        if not val:
            return None
        if name.find('queue') >= 0:
            obj = boto.lookup('sqs', val)
            if obj:
                obj.set_message_class(ServiceMessage)
        elif name.find('bucket') >= 0:
            obj = boto.lookup('s3', val)
        elif name.find('domain') >= 0:
            obj = boto.lookup('sdb', val)
        else:
            obj = None
        return obj


