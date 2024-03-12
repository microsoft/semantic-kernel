# Copyright (c) 2017 Amazon.com, Inc. or its affiliates.
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
import os

from tests.unit import unittest


class TestConnectAwslambda(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.awslambda import connect_to_region
        from boto.awslambda.layer1 import AWSLambdaConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, AWSLambdaConnection)
        self.assertEqual(connection.host, 'lambda.us-east-1.amazonaws.com')


class TestConnectBeanstalk(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.beanstalk import connect_to_region
        from boto.beanstalk.layer1 import Layer1
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Layer1)
        self.assertEqual(
            connection.host, 'elasticbeanstalk.us-east-1.amazonaws.com')


class TestConnectCloudformation(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cloudformation import connect_to_region
        from boto.cloudformation.connection import CloudFormationConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CloudFormationConnection)
        self.assertEqual(
            connection.host, 'cloudformation.us-east-1.amazonaws.com')


class TestConnectCloudHsm(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cloudhsm import connect_to_region
        from boto.cloudhsm.layer1 import CloudHSMConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CloudHSMConnection)
        self.assertEqual(connection.host, 'cloudhsm.us-east-1.amazonaws.com')


class TestCloudsearchConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cloudsearch import connect_to_region
        from boto.cloudsearch.layer1 import Layer1
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Layer1)
        self.assertEqual(
            connection.host, 'cloudsearch.us-east-1.amazonaws.com')


class TestCloudsearch2Connection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cloudsearch2 import connect_to_region
        from boto.cloudsearch2.layer1 import CloudSearchConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CloudSearchConnection)
        self.assertEqual(
            connection.host, 'cloudsearch.us-east-1.amazonaws.com')


class TestCloudsearchDomainConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cloudsearchdomain import connect_to_region
        from boto.cloudsearchdomain.layer1 import CloudSearchDomainConnection
        host = 'mycustomdomain.us-east-1.amazonaws.com'
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar', host=host)
        self.assertIsInstance(connection, CloudSearchDomainConnection)
        self.assertEqual(connection.host, host)


class TestCloudTrailConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cloudtrail import connect_to_region
        from boto.cloudtrail.layer1 import CloudTrailConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CloudTrailConnection)
        self.assertEqual(connection.host, 'cloudtrail.us-east-1.amazonaws.com')


class TestCodeDeployConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.codedeploy import connect_to_region
        from boto.codedeploy.layer1 import CodeDeployConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CodeDeployConnection)
        self.assertEqual(connection.host, 'codedeploy.us-east-1.amazonaws.com')


class TestCognitoIdentityConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cognito.identity import connect_to_region
        from boto.cognito.identity.layer1 import CognitoIdentityConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CognitoIdentityConnection)
        self.assertEqual(
            connection.host, 'cognito-identity.us-east-1.amazonaws.com')


class TestCognitoSyncConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.cognito.sync import connect_to_region
        from boto.cognito.sync.layer1 import CognitoSyncConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CognitoSyncConnection)
        self.assertEqual(
            connection.host, 'cognito-sync.us-east-1.amazonaws.com')


class TestConfigserviceConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.configservice import connect_to_region
        from boto.configservice.layer1 import ConfigServiceConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, ConfigServiceConnection)
        self.assertEqual(connection.host, 'config.us-east-1.amazonaws.com')


class TestDatapipelineConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.datapipeline import connect_to_region
        from boto.datapipeline.layer1 import DataPipelineConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, DataPipelineConnection)
        self.assertEqual(
            connection.host, 'datapipeline.us-east-1.amazonaws.com')


class TestDirectconnectConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.directconnect import connect_to_region
        from boto.directconnect.layer1 import DirectConnectConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, DirectConnectConnection)
        self.assertEqual(
            connection.host, 'directconnect.us-east-1.amazonaws.com')


class TestDynamodbConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.dynamodb import connect_to_region
        from boto.dynamodb.layer2 import Layer2
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Layer2)
        self.assertEqual(
            connection.layer1.host, 'dynamodb.us-east-1.amazonaws.com')


class TestDynamodb2Connection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.dynamodb2 import connect_to_region
        from boto.dynamodb2.layer1 import DynamoDBConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, DynamoDBConnection)
        self.assertEqual(connection.host, 'dynamodb.us-east-1.amazonaws.com')

    def test_connect_to_unkown_region(self):
        from boto.dynamodb2 import connect_to_region
        from boto.dynamodb2.layer1 import DynamoDBConnection
        os.environ['BOTO_USE_ENDPOINT_HEURISTICS'] = 'True'
        connection = connect_to_region(
            'us-east-45', aws_access_key_id='foo',
            aws_secret_access_key='bar')
        self.assertIsInstance(connection, DynamoDBConnection)
        self.assertEqual(connection.host, 'dynamodb.us-east-45.amazonaws.com')


class TestEC2Connection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.ec2 import connect_to_region
        from boto.ec2.connection import EC2Connection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, EC2Connection)
        self.assertEqual(connection.host, 'ec2.us-east-1.amazonaws.com')


class TestAutoscaleConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.ec2.autoscale import connect_to_region
        from boto.ec2.autoscale import AutoScaleConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, AutoScaleConnection)
        self.assertEqual(
            connection.host, 'autoscaling.us-east-1.amazonaws.com')


class TestCloudwatchConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.ec2.cloudwatch import connect_to_region
        from boto.ec2.cloudwatch import CloudWatchConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CloudWatchConnection)
        self.assertEqual(connection.host, 'monitoring.us-east-1.amazonaws.com')


class TestElbConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.ec2.elb import connect_to_region
        from boto.ec2.elb import ELBConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, ELBConnection)
        self.assertEqual(
            connection.host, 'elasticloadbalancing.us-east-1.amazonaws.com')


class TestEc2ContainerserviceConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.ec2containerservice import connect_to_region
        import boto.ec2containerservice.layer1 as layer1
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(
            connection, layer1.EC2ContainerServiceConnection)
        self.assertEqual(connection.host, 'ecs.us-east-1.amazonaws.com')


class TestElasticacheConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.elasticache import connect_to_region
        from boto.elasticache.layer1 import ElastiCacheConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, ElastiCacheConnection)
        self.assertEqual(
            connection.host, 'elasticache.us-east-1.amazonaws.com')


class TestElastictranscoderConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.elastictranscoder import connect_to_region
        from boto.elastictranscoder.layer1 import ElasticTranscoderConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, ElasticTranscoderConnection)
        self.assertEqual(
            connection.host, 'elastictranscoder.us-east-1.amazonaws.com')


class TestEmrConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.emr import connect_to_region
        from boto.emr.connection import EmrConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, EmrConnection)
        self.assertEqual(
            connection.host, 'elasticmapreduce.us-east-1.amazonaws.com')


class TestGlacierConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.glacier import connect_to_region
        from boto.glacier.layer2 import Layer2
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Layer2)
        self.assertEqual(
            connection.layer1.host, 'glacier.us-east-1.amazonaws.com')


class TestIamConnection(unittest.TestCase):
    def assert_connection(self, region, host):
        from boto.iam import connect_to_region
        from boto.iam.connection import IAMConnection
        connection = connect_to_region(region, aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, IAMConnection)
        self.assertEqual(connection.host, host)

    def test_connect_to_region(self):
        self.assert_connection('us-east-1', 'iam.amazonaws.com')

    def test_connect_to_universal_region(self):
        self.assert_connection('universal', 'iam.amazonaws.com')


class TestKinesisConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.kinesis import connect_to_region
        from boto.kinesis.layer1 import KinesisConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, KinesisConnection)
        self.assertEqual(connection.host, 'kinesis.us-east-1.amazonaws.com')


class TestLogsConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.logs import connect_to_region
        from boto.logs.layer1 import CloudWatchLogsConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, CloudWatchLogsConnection)
        self.assertEqual(
            connection.host, 'logs.us-east-1.amazonaws.com')


class TestMachinelearningConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.machinelearning import connect_to_region
        from boto.machinelearning.layer1 import MachineLearningConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, MachineLearningConnection)
        self.assertEqual(
            connection.host, 'machinelearning.us-east-1.amazonaws.com')


class TestOpsworksConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.opsworks import connect_to_region
        from boto.opsworks.layer1 import OpsWorksConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, OpsWorksConnection)
        self.assertEqual(
            connection.host, 'opsworks.us-east-1.amazonaws.com')


class TestRdsConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.rds import connect_to_region
        from boto.rds import RDSConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, RDSConnection)
        self.assertEqual(
            connection.host, 'rds.amazonaws.com')


class TestRds2Connection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.rds2 import connect_to_region
        from boto.rds2.layer1 import RDSConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, RDSConnection)
        self.assertEqual(
            connection.host, 'rds.amazonaws.com')


class TestRedshiftConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.redshift import connect_to_region
        from boto.redshift.layer1 import RedshiftConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, RedshiftConnection)
        self.assertEqual(
            connection.host, 'redshift.us-east-1.amazonaws.com')


class TestRoute53Connection(unittest.TestCase):
    def assert_connection(self, region, host):
        from boto.route53 import connect_to_region
        from boto.route53.connection import Route53Connection
        connection = connect_to_region(region, aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Route53Connection)
        self.assertEqual(connection.host, host)

    def test_connect_to_region(self):
        self.assert_connection('us-east-1', 'route53.amazonaws.com')

    def test_connect_to_universal_region(self):
        self.assert_connection('universal', 'route53.amazonaws.com')


class TestRoute53DomainsConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.route53.domains import connect_to_region
        from boto.route53.domains.layer1 import Route53DomainsConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Route53DomainsConnection)
        self.assertEqual(
            connection.host, 'route53domains.us-east-1.amazonaws.com')


class TestS3Connection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.s3 import connect_to_region
        from boto.s3.connection import S3Connection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, S3Connection)
        self.assertEqual(connection.host, 's3.amazonaws.com')

    def test_connect_to_custom_host(self):
        from boto.s3 import connect_to_region
        from boto.s3.connection import S3Connection
        host = 'mycustomhost.example.com'
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar', host=host)
        self.assertIsInstance(connection, S3Connection)
        self.assertEqual(connection.host, host)


class TestSdbConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.sdb import connect_to_region
        from boto.sdb.connection import SDBConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, SDBConnection)
        self.assertEqual(connection.host, 'sdb.amazonaws.com')


class TestSesConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.ses import connect_to_region
        from boto.ses.connection import SESConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, SESConnection)
        self.assertEqual(connection.host, 'email.us-east-1.amazonaws.com')


class TestSnsConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.sns import connect_to_region
        from boto.sns.connection import SNSConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, SNSConnection)
        self.assertEqual(connection.host, 'sns.us-east-1.amazonaws.com')


class TestSqsConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.sqs import connect_to_region
        from boto.sqs.connection import SQSConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, SQSConnection)
        self.assertEqual(connection.host, 'queue.amazonaws.com')


class TestStsConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.sts import connect_to_region
        from boto.sts.connection import STSConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, STSConnection)
        self.assertEqual(connection.host, 'sts.amazonaws.com')


class TestSupportConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.support import connect_to_region
        from boto.support.layer1 import SupportConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, SupportConnection)
        self.assertEqual(connection.host, 'support.us-east-1.amazonaws.com')


class TestSwfConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.swf import connect_to_region
        from boto.swf.layer1 import Layer1
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, Layer1)
        self.assertEqual(connection.host, 'swf.us-east-1.amazonaws.com')


class TestVpcConnection(unittest.TestCase):
    def test_connect_to_region(self):
        from boto.vpc import connect_to_region
        from boto.vpc import VPCConnection
        connection = connect_to_region('us-east-1', aws_access_key_id='foo',
                                       aws_secret_access_key='bar')
        self.assertIsInstance(connection, VPCConnection)
        self.assertEqual(connection.host, 'ec2.us-east-1.amazonaws.com')
