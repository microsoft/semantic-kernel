from __future__ import print_function
import os
import urlparse
import boto
import boto.connection
import boto.jsonresponse
import boto.exception
from boto.roboto import awsqueryrequest

class NoCredentialsError(boto.exception.BotoClientError):

    def __init__(self):
        s = 'Unable to find credentials'
        super(NoCredentialsError, self).__init__(s)

class AWSQueryService(boto.connection.AWSQueryConnection):

    Name = ''
    Description = ''
    APIVersion = ''
    Authentication = 'sign-v2'
    Path = '/'
    Port = 443
    Provider = 'aws'
    EnvURL = 'AWS_URL'

    Regions = []

    def __init__(self, **args):
        self.args = args
        self.check_for_credential_file()
        self.check_for_env_url()
        if 'host' not in self.args:
            if self.Regions:
                region_name = self.args.get('region_name',
                                            self.Regions[0]['name'])
                for region in self.Regions:
                    if region['name'] == region_name:
                        self.args['host'] = region['endpoint']
        if 'path' not in self.args:
            self.args['path'] = self.Path
        if 'port' not in self.args:
            self.args['port'] = self.Port
        try:
            super(AWSQueryService, self).__init__(**self.args)
            self.aws_response = None
        except boto.exception.NoAuthHandlerFound:
            raise NoCredentialsError()

    def check_for_credential_file(self):
        """
        Checks for the existence of an AWS credential file.
        If the environment variable AWS_CREDENTIAL_FILE is
        set and points to a file, that file will be read and
        will be searched credentials.
        Note that if credentials have been explicitelypassed
        into the class constructor, those values always take
        precedence.
        """
        if 'AWS_CREDENTIAL_FILE' in os.environ:
            path = os.environ['AWS_CREDENTIAL_FILE']
            path = os.path.expanduser(path)
            path = os.path.expandvars(path)
            if os.path.isfile(path):
                fp = open(path)
                lines = fp.readlines()
                fp.close()
                for line in lines:
                    if line[0] != '#':
                        if '=' in line:
                            name, value = line.split('=', 1)
                            if name.strip() == 'AWSAccessKeyId':
                                if 'aws_access_key_id' not in self.args:
                                    value = value.strip()
                                    self.args['aws_access_key_id'] = value
                            elif name.strip() == 'AWSSecretKey':
                                if 'aws_secret_access_key' not in self.args:
                                    value = value.strip()
                                    self.args['aws_secret_access_key'] = value
            else:
                print('Warning: unable to read AWS_CREDENTIAL_FILE')

    def check_for_env_url(self):
        """
        First checks to see if a url argument was explicitly passed
        in.  If so, that will be used.  If not, it checks for the
        existence of the environment variable specified in ENV_URL.
        If this is set, it should contain a fully qualified URL to the
        service you want to use.
        Note that any values passed explicitly to the class constructor
        will take precedence.
        """
        url = self.args.get('url', None)
        if url:
            del self.args['url']
        if not url and self.EnvURL in os.environ:
            url = os.environ[self.EnvURL]
        if url:
            rslt = urlparse.urlparse(url)
            if 'is_secure' not in self.args:
                if rslt.scheme == 'https':
                    self.args['is_secure'] = True
                else:
                    self.args['is_secure'] = False

            host = rslt.netloc
            port = None
            l = host.split(':')
            if len(l) > 1:
                host = l[0]
                port = int(l[1])
            if 'host' not in self.args:
                self.args['host'] = host
            if port and 'port' not in self.args:
                self.args['port'] = port

            if rslt.path and 'path' not in self.args:
                self.args['path'] = rslt.path

    def _required_auth_capability(self):
        return [self.Authentication]

