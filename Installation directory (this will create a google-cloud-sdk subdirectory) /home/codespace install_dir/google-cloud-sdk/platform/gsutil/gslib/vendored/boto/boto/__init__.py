# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010-2011, Eucalyptus Systems, Inc.
# Copyright (c) 2011, Nexenta Systems Inc.
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# Copyright (c) 2010, Google, Inc.
# All rights reserved.
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
from boto.pyami.config import Config, BotoConfigLocations
from boto.storage_uri import BucketStorageUri, FileStorageUri
import boto.plugin
import datetime
import os
import platform
import re
import sys
import logging
import logging.config

from boto.compat import urlparse
from boto.exception import InvalidUriError

__version__ = '2.49.0'
Version = __version__  # for backware compatibility

# http://bugs.python.org/issue7980
datetime.datetime.strptime('', '')

UserAgent = 'Boto/%s Python/%s %s/%s' % (
    __version__,
    platform.python_version(),
    platform.system(),
    platform.release()
)
config = Config()

# Regex to disallow buckets violating charset or not [3..255] chars total.
BUCKET_NAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\._-]{1,253}[a-zA-Z0-9]$')
# Regex to disallow buckets with individual DNS labels longer than 63.
TOO_LONG_DNS_NAME_COMP = re.compile(r'[-_a-z0-9]{64}')
GENERATION_RE = re.compile(r'(?P<versionless_uri_str>.+)'
                           r'#(?P<generation>[0-9]+)$')
VERSION_RE = re.compile('(?P<versionless_uri_str>.+)#(?P<version_id>.+)$')
ENDPOINTS_PATH = os.path.join(os.path.dirname(__file__), 'endpoints.json')


def init_logging():
    for file in BotoConfigLocations:
        try:
            logging.config.fileConfig(os.path.expanduser(file))
        except:
            pass


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

log = logging.getLogger('boto')
perflog = logging.getLogger('boto.perf')
log.addHandler(NullHandler())
perflog.addHandler(NullHandler())
init_logging()

# convenience function to set logging to a particular file


def set_file_logger(name, filepath, level=logging.INFO, format_string=None):
    global log
    if not format_string:
        format_string = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.FileHandler(filepath)
    fh.setLevel(level)
    formatter = logging.Formatter(format_string)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    log = logger


def set_stream_logger(name, level=logging.DEBUG, format_string=None):
    global log
    if not format_string:
        format_string = "%(asctime)s %(name)s [%(levelname)s]:%(message)s"
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.StreamHandler()
    fh.setLevel(level)
    formatter = logging.Formatter(format_string)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    log = logger


def connect_sqs(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.sqs.connection.SQSConnection`
    :return: A connection to Amazon's SQS
    """
    from boto.sqs.connection import SQSConnection
    return SQSConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_s3(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.s3.connection.S3Connection`
    :return: A connection to Amazon's S3
    """
    from boto.s3.connection import S3Connection
    return S3Connection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_gs(gs_access_key_id=None, gs_secret_access_key=None, **kwargs):
    """
    @type gs_access_key_id: string
    @param gs_access_key_id: Your Google Cloud Storage Access Key ID

    @type gs_secret_access_key: string
    @param gs_secret_access_key: Your Google Cloud Storage Secret Access Key

    @rtype: L{GSConnection<boto.gs.connection.GSConnection>}
    @return: A connection to Google's Storage service
    """
    from boto.gs.connection import GSConnection
    return GSConnection(gs_access_key_id, gs_secret_access_key, **kwargs)


def connect_ec2(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ec2.connection.EC2Connection`
    :return: A connection to Amazon's EC2
    """
    from boto.ec2.connection import EC2Connection
    return EC2Connection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_elb(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ec2.elb.ELBConnection`
    :return: A connection to Amazon's Load Balancing Service
    """
    from boto.ec2.elb import ELBConnection
    return ELBConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_autoscale(aws_access_key_id=None, aws_secret_access_key=None,
                      **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ec2.autoscale.AutoScaleConnection`
    :return: A connection to Amazon's Auto Scaling Service

    :type use_block_device_types bool
    :param use_block_device_types: Specifies whether to return described Launch Configs with block device mappings containing
        block device types, or a list of old style block device mappings (deprecated).  This defaults to false for compatability
        with the old incorrect style.
    """
    from boto.ec2.autoscale import AutoScaleConnection
    return AutoScaleConnection(aws_access_key_id, aws_secret_access_key,
                               **kwargs)


def connect_cloudwatch(aws_access_key_id=None, aws_secret_access_key=None,
                       **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ec2.cloudwatch.CloudWatchConnection`
    :return: A connection to Amazon's EC2 Monitoring service
    """
    from boto.ec2.cloudwatch import CloudWatchConnection
    return CloudWatchConnection(aws_access_key_id, aws_secret_access_key,
                                **kwargs)


def connect_sdb(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.sdb.connection.SDBConnection`
    :return: A connection to Amazon's SDB
    """
    from boto.sdb.connection import SDBConnection
    return SDBConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_fps(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.fps.connection.FPSConnection`
    :return: A connection to FPS
    """
    from boto.fps.connection import FPSConnection
    return FPSConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_mturk(aws_access_key_id=None, aws_secret_access_key=None,
                  **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.mturk.connection.MTurkConnection`
    :return: A connection to MTurk
    """
    from boto.mturk.connection import MTurkConnection
    return MTurkConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_cloudfront(aws_access_key_id=None, aws_secret_access_key=None,
                       **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.fps.connection.FPSConnection`
    :return: A connection to FPS
    """
    from boto.cloudfront import CloudFrontConnection
    return CloudFrontConnection(aws_access_key_id, aws_secret_access_key,
                                **kwargs)


def connect_vpc(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.vpc.VPCConnection`
    :return: A connection to VPC
    """
    from boto.vpc import VPCConnection
    return VPCConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_rds(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.rds.RDSConnection`
    :return: A connection to RDS
    """
    from boto.rds import RDSConnection
    return RDSConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_rds2(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.rds2.layer1.RDSConnection`
    :return: A connection to RDS
    """
    from boto.rds2.layer1 import RDSConnection
    return RDSConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_emr(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.emr.EmrConnection`
    :return: A connection to Elastic mapreduce
    """
    from boto.emr import EmrConnection
    return EmrConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_sns(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.sns.SNSConnection`
    :return: A connection to Amazon's SNS
    """
    from boto.sns import SNSConnection
    return SNSConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_iam(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.iam.IAMConnection`
    :return: A connection to Amazon's IAM
    """
    from boto.iam import IAMConnection
    return IAMConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_route53(aws_access_key_id=None, aws_secret_access_key=None,
                    **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.dns.Route53Connection`
    :return: A connection to Amazon's Route53 DNS Service
    """
    from boto.route53 import Route53Connection
    return Route53Connection(aws_access_key_id, aws_secret_access_key,
                             **kwargs)


def connect_cloudformation(aws_access_key_id=None, aws_secret_access_key=None,
                           **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.cloudformation.CloudFormationConnection`
    :return: A connection to Amazon's CloudFormation Service
    """
    from boto.cloudformation import CloudFormationConnection
    return CloudFormationConnection(aws_access_key_id, aws_secret_access_key,
                                    **kwargs)


def connect_euca(host=None, aws_access_key_id=None, aws_secret_access_key=None,
                 port=8773, path='/services/Eucalyptus', is_secure=False,
                 **kwargs):
    """
    Connect to a Eucalyptus service.

    :type host: string
    :param host: the host name or ip address of the Eucalyptus server

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ec2.connection.EC2Connection`
    :return: A connection to Eucalyptus server
    """
    from boto.ec2 import EC2Connection
    from boto.ec2.regioninfo import RegionInfo

    # Check for values in boto config, if not supplied as args
    if not aws_access_key_id:
        aws_access_key_id = config.get('Credentials',
                                       'euca_access_key_id',
                                       None)
    if not aws_secret_access_key:
        aws_secret_access_key = config.get('Credentials',
                                           'euca_secret_access_key',
                                           None)
    if not host:
        host = config.get('Boto', 'eucalyptus_host', None)

    reg = RegionInfo(name='eucalyptus', endpoint=host)
    return EC2Connection(aws_access_key_id, aws_secret_access_key,
                         region=reg, port=port, path=path,
                         is_secure=is_secure, **kwargs)


def connect_glacier(aws_access_key_id=None, aws_secret_access_key=None,
                    **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.glacier.layer2.Layer2`
    :return: A connection to Amazon's Glacier Service
    """
    from boto.glacier.layer2 import Layer2
    return Layer2(aws_access_key_id, aws_secret_access_key,
                  **kwargs)


def connect_ec2_endpoint(url, aws_access_key_id=None,
                         aws_secret_access_key=None,
                         **kwargs):
    """
    Connect to an EC2 Api endpoint.  Additional arguments are passed
    through to connect_ec2.

    :type url: string
    :param url: A url for the ec2 api endpoint to connect to

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ec2.connection.EC2Connection`
    :return: A connection to Eucalyptus server
    """
    from boto.ec2.regioninfo import RegionInfo

    purl = urlparse(url)
    kwargs['port'] = purl.port
    kwargs['host'] = purl.hostname
    kwargs['path'] = purl.path
    if not 'is_secure' in kwargs:
        kwargs['is_secure'] = (purl.scheme == "https")

    kwargs['region'] = RegionInfo(name=purl.hostname,
                                  endpoint=purl.hostname)
    kwargs['aws_access_key_id'] = aws_access_key_id
    kwargs['aws_secret_access_key'] = aws_secret_access_key

    return(connect_ec2(**kwargs))


def connect_walrus(host=None, aws_access_key_id=None,
                   aws_secret_access_key=None,
                   port=8773, path='/services/Walrus', is_secure=False,
                   **kwargs):
    """
    Connect to a Walrus service.

    :type host: string
    :param host: the host name or ip address of the Walrus server

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.s3.connection.S3Connection`
    :return: A connection to Walrus
    """
    from boto.s3.connection import S3Connection
    from boto.s3.connection import OrdinaryCallingFormat

    # Check for values in boto config, if not supplied as args
    if not aws_access_key_id:
        aws_access_key_id = config.get('Credentials',
                                       'euca_access_key_id',
                                       None)
    if not aws_secret_access_key:
        aws_secret_access_key = config.get('Credentials',
                                           'euca_secret_access_key',
                                           None)
    if not host:
        host = config.get('Boto', 'walrus_host', None)

    return S3Connection(aws_access_key_id, aws_secret_access_key,
                        host=host, port=port, path=path,
                        calling_format=OrdinaryCallingFormat(),
                        is_secure=is_secure, **kwargs)


def connect_ses(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ses.SESConnection`
    :return: A connection to Amazon's SES
    """
    from boto.ses import SESConnection
    return SESConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_sts(aws_access_key_id=None, aws_secret_access_key=None, **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.sts.STSConnection`
    :return: A connection to Amazon's STS
    """
    from boto.sts import STSConnection
    return STSConnection(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_ia(ia_access_key_id=None, ia_secret_access_key=None,
               is_secure=False, **kwargs):
    """
    Connect to the Internet Archive via their S3-like API.

    :type ia_access_key_id: string
    :param ia_access_key_id: Your IA Access Key ID.  This will also look
        in your boto config file for an entry in the Credentials
        section called "ia_access_key_id"

    :type ia_secret_access_key: string
    :param ia_secret_access_key: Your IA Secret Access Key.  This will also
        look in your boto config file for an entry in the Credentials
        section called "ia_secret_access_key"

    :rtype: :class:`boto.s3.connection.S3Connection`
    :return: A connection to the Internet Archive
    """
    from boto.s3.connection import S3Connection
    from boto.s3.connection import OrdinaryCallingFormat

    access_key = config.get('Credentials', 'ia_access_key_id',
                            ia_access_key_id)
    secret_key = config.get('Credentials', 'ia_secret_access_key',
                            ia_secret_access_key)

    return S3Connection(access_key, secret_key,
                        host='s3.us.archive.org',
                        calling_format=OrdinaryCallingFormat(),
                        is_secure=is_secure, **kwargs)


def connect_dynamodb(aws_access_key_id=None,
                     aws_secret_access_key=None,
                     **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.dynamodb.layer2.Layer2`
    :return: A connection to the Layer2 interface for DynamoDB.
    """
    from boto.dynamodb.layer2 import Layer2
    return Layer2(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_swf(aws_access_key_id=None,
                aws_secret_access_key=None,
                **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.swf.layer1.Layer1`
    :return: A connection to the Layer1 interface for SWF.
    """
    from boto.swf.layer1 import Layer1
    return Layer1(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_cloudsearch(aws_access_key_id=None,
                        aws_secret_access_key=None,
                        **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.cloudsearch.layer2.Layer2`
    :return: A connection to Amazon's CloudSearch service
    """
    from boto.cloudsearch.layer2 import Layer2
    return Layer2(aws_access_key_id, aws_secret_access_key,
                  **kwargs)


def connect_cloudsearch2(aws_access_key_id=None,
                         aws_secret_access_key=None,
                         sign_request=False,
                         **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :type sign_request: bool
    :param sign_request: whether or not to sign search and
        upload requests

    :rtype: :class:`boto.cloudsearch2.layer2.Layer2`
    :return: A connection to Amazon's CloudSearch2 service
    """
    from boto.cloudsearch2.layer2 import Layer2
    return Layer2(aws_access_key_id, aws_secret_access_key,
                  sign_request=sign_request,
                  **kwargs)


def connect_cloudsearchdomain(aws_access_key_id=None,
                              aws_secret_access_key=None,
                              **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.cloudsearchdomain.layer1.CloudSearchDomainConnection`
    :return: A connection to Amazon's CloudSearch Domain service
    """
    from boto.cloudsearchdomain.layer1 import CloudSearchDomainConnection
    return CloudSearchDomainConnection(aws_access_key_id,
                                       aws_secret_access_key, **kwargs)


def connect_beanstalk(aws_access_key_id=None,
                      aws_secret_access_key=None,
                      **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.beanstalk.layer1.Layer1`
    :return: A connection to Amazon's Elastic Beanstalk service
    """
    from boto.beanstalk.layer1 import Layer1
    return Layer1(aws_access_key_id, aws_secret_access_key, **kwargs)


def connect_elastictranscoder(aws_access_key_id=None,
                              aws_secret_access_key=None,
                              **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.ets.layer1.ElasticTranscoderConnection`
    :return: A connection to Amazon's Elastic Transcoder service
    """
    from boto.elastictranscoder.layer1 import ElasticTranscoderConnection
    return ElasticTranscoderConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs)


def connect_opsworks(aws_access_key_id=None,
                     aws_secret_access_key=None,
                     **kwargs):
    from boto.opsworks.layer1 import OpsWorksConnection
    return OpsWorksConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs)


def connect_redshift(aws_access_key_id=None,
                     aws_secret_access_key=None,
                     **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.redshift.layer1.RedshiftConnection`
    :return: A connection to Amazon's Redshift service
    """
    from boto.redshift.layer1 import RedshiftConnection
    return RedshiftConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_support(aws_access_key_id=None,
                    aws_secret_access_key=None,
                    **kwargs):
    """
    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.support.layer1.SupportConnection`
    :return: A connection to Amazon's Support service
    """
    from boto.support.layer1 import SupportConnection
    return SupportConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_cloudtrail(aws_access_key_id=None,
                    aws_secret_access_key=None,
                    **kwargs):
    """
    Connect to AWS CloudTrail

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.cloudtrail.layer1.CloudtrailConnection`
    :return: A connection to the AWS Cloudtrail service
    """
    from boto.cloudtrail.layer1 import CloudTrailConnection
    return CloudTrailConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_directconnect(aws_access_key_id=None,
                          aws_secret_access_key=None,
                          **kwargs):
    """
    Connect to AWS DirectConnect

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`boto.directconnect.layer1.DirectConnectConnection`
    :return: A connection to the AWS DirectConnect service
    """
    from boto.directconnect.layer1 import DirectConnectConnection
    return DirectConnectConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )

def connect_kinesis(aws_access_key_id=None,
                    aws_secret_access_key=None,
                    **kwargs):
    """
    Connect to Amazon Kinesis

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.kinesis.layer1.KinesisConnection`
    :return: A connection to the Amazon Kinesis service
    """
    from boto.kinesis.layer1 import KinesisConnection
    return KinesisConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )

def connect_logs(aws_access_key_id=None,
                    aws_secret_access_key=None,
                    **kwargs):
    """
    Connect to Amazon CloudWatch Logs

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.kinesis.layer1.CloudWatchLogsConnection`
    :return: A connection to the Amazon CloudWatch Logs service
    """
    from boto.logs.layer1 import CloudWatchLogsConnection
    return CloudWatchLogsConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_route53domains(aws_access_key_id=None,
                           aws_secret_access_key=None,
                           **kwargs):
    """
    Connect to Amazon Route 53 Domains

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.route53.domains.layer1.Route53DomainsConnection`
    :return: A connection to the Amazon Route 53 Domains service
    """
    from boto.route53.domains.layer1 import Route53DomainsConnection
    return Route53DomainsConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_cognito_identity(aws_access_key_id=None,
                             aws_secret_access_key=None,
                             **kwargs):
    """
    Connect to Amazon Cognito Identity

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.cognito.identity.layer1.CognitoIdentityConnection`
    :return: A connection to the Amazon Cognito Identity service
    """
    from boto.cognito.identity.layer1 import CognitoIdentityConnection
    return CognitoIdentityConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_cognito_sync(aws_access_key_id=None,
                         aws_secret_access_key=None,
                         **kwargs):
    """
    Connect to Amazon Cognito Sync

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.cognito.sync.layer1.CognitoSyncConnection`
    :return: A connection to the Amazon Cognito Sync service
    """
    from boto.cognito.sync.layer1 import CognitoSyncConnection
    return CognitoSyncConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_kms(aws_access_key_id=None,
                aws_secret_access_key=None,
                **kwargs):
    """
    Connect to AWS Key Management Service

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.kms.layer1.KMSConnection`
    :return: A connection to the AWS Key Management Service
    """
    from boto.kms.layer1 import KMSConnection
    return KMSConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_awslambda(aws_access_key_id=None,
                      aws_secret_access_key=None,
                      **kwargs):
    """
    Connect to AWS Lambda

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.awslambda.layer1.AWSLambdaConnection`
    :return: A connection to the AWS Lambda service
    """
    from boto.awslambda.layer1 import AWSLambdaConnection
    return AWSLambdaConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_codedeploy(aws_access_key_id=None,
                       aws_secret_access_key=None,
                       **kwargs):
    """
    Connect to AWS CodeDeploy

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.cognito.sync.layer1.CodeDeployConnection`
    :return: A connection to the AWS CodeDeploy service
    """
    from boto.codedeploy.layer1 import CodeDeployConnection
    return CodeDeployConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_configservice(aws_access_key_id=None,
                          aws_secret_access_key=None,
                          **kwargs):
    """
    Connect to AWS Config

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.kms.layer1.ConfigServiceConnection`
    :return: A connection to the AWS Config service
    """
    from boto.configservice.layer1 import ConfigServiceConnection
    return ConfigServiceConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_cloudhsm(aws_access_key_id=None,
                     aws_secret_access_key=None,
                     **kwargs):
    """
    Connect to AWS CloudHSM

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    rtype: :class:`boto.cloudhsm.layer1.CloudHSMConnection`
    :return: A connection to the AWS CloudHSM service
    """
    from boto.cloudhsm.layer1 import CloudHSMConnection
    return CloudHSMConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_ec2containerservice(aws_access_key_id=None,
                                aws_secret_access_key=None,
                                **kwargs):
    """
    Connect to Amazon EC2 Container Service
    rtype: :class:`boto.ec2containerservice.layer1.EC2ContainerServiceConnection`
    :return: A connection to the Amazon EC2 Container Service
    """
    from boto.ec2containerservice.layer1 import EC2ContainerServiceConnection
    return EC2ContainerServiceConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def connect_machinelearning(aws_access_key_id=None,
                            aws_secret_access_key=None,
                            **kwargs):
    """
    Connect to Amazon Machine Learning service
    rtype: :class:`boto.machinelearning.layer1.MachineLearningConnection`
    :return: A connection to the Amazon Machine Learning service
    """
    from boto.machinelearning.layer1 import MachineLearningConnection
    return MachineLearningConnection(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs
    )


def storage_uri(uri_str, default_scheme='file', debug=0, validate=True,
                bucket_storage_uri_class=BucketStorageUri,
                suppress_consec_slashes=True, is_latest=False):
    """
    Instantiate a StorageUri from a URI string.

    :type uri_str: string
    :param uri_str: URI naming bucket + optional object.
    :type default_scheme: string
    :param default_scheme: default scheme for scheme-less URIs.
    :type debug: int
    :param debug: debug level to pass in to boto connection (range 0..2).
    :type validate: bool
    :param validate: whether to check for bucket name validity.
    :type bucket_storage_uri_class: BucketStorageUri interface.
    :param bucket_storage_uri_class: Allows mocking for unit tests.
    :param suppress_consec_slashes: If provided, controls whether
        consecutive slashes will be suppressed in key paths.
    :type is_latest: bool
    :param is_latest: whether this versioned object represents the
        current version.

    We allow validate to be disabled to allow caller
    to implement bucket-level wildcarding (outside the boto library;
    see gsutil).

    :rtype: :class:`boto.StorageUri` subclass
    :return: StorageUri subclass for given URI.

    ``uri_str`` must be one of the following formats:

    * gs://bucket/name
    * gs://bucket/name#ver
    * s3://bucket/name
    * gs://bucket
    * s3://bucket
    * filename (which could be a Unix path like /a/b/c or a Windows path like
      C:\a\b\c)

    The last example uses the default scheme ('file', unless overridden).
    """
    version_id = None
    generation = None

    # Manually parse URI components instead of using urlparse because
    # what we're calling URIs don't really fit the standard syntax for URIs
    # (the latter includes an optional host/net location part).
    end_scheme_idx = uri_str.find('://')
    if end_scheme_idx == -1:
        scheme = default_scheme.lower()
        path = uri_str
    else:
        scheme = uri_str[0:end_scheme_idx].lower()
        path = uri_str[end_scheme_idx + 3:]

    if scheme not in ['file', 's3', 'gs']:
        raise InvalidUriError('Unrecognized scheme "%s"' % scheme)
    if scheme == 'file':
        # For file URIs we have no bucket name, and use the complete path
        # (minus 'file://') as the object name.
        is_stream = False
        if path == '-':
            is_stream = True
        return FileStorageUri(path, debug, is_stream)
    else:
        path_parts = path.split('/', 1)
        bucket_name = path_parts[0]
        object_name = ''
        # If validate enabled, ensure the bucket name is valid, to avoid
        # possibly confusing other parts of the code. (For example if we didn't
        # catch bucket names containing ':', when a user tried to connect to
        # the server with that name they might get a confusing error about
        # non-integer port numbers.)
        if (validate and bucket_name and
            (not BUCKET_NAME_RE.match(bucket_name)
             or TOO_LONG_DNS_NAME_COMP.search(bucket_name))):
            raise InvalidUriError('Invalid bucket name in URI "%s"' % uri_str)
        if scheme == 'gs':
            match = GENERATION_RE.search(path)
            if match:
                md = match.groupdict()
                versionless_uri_str = md['versionless_uri_str']
                path_parts = versionless_uri_str.split('/', 1)
                generation = int(md['generation'])
        elif scheme == 's3':
            match = VERSION_RE.search(path)
            if match:
                md = match.groupdict()
                versionless_uri_str = md['versionless_uri_str']
                path_parts = versionless_uri_str.split('/', 1)
                version_id = md['version_id']
        else:
            raise InvalidUriError('Unrecognized scheme "%s"' % scheme)
        if len(path_parts) > 1:
            object_name = path_parts[1]
        return bucket_storage_uri_class(
            scheme, bucket_name, object_name, debug,
            suppress_consec_slashes=suppress_consec_slashes,
            version_id=version_id, generation=generation, is_latest=is_latest)


def storage_uri_for_key(key):
    """Returns a StorageUri for the given key.

    :type key: :class:`boto.s3.key.Key` or subclass
    :param key: URI naming bucket + optional object.
    """
    if not isinstance(key, boto.s3.key.Key):
        raise InvalidUriError('Requested key (%s) is not a subclass of '
                              'boto.s3.key.Key' % str(type(key)))
    prov_name = key.bucket.connection.provider.get_provider_name()
    uri_str = '%s://%s/%s' % (prov_name, key.bucket.name, key.name)
    return storage_uri(uri_str)

boto.plugin.load_plugins(config)
