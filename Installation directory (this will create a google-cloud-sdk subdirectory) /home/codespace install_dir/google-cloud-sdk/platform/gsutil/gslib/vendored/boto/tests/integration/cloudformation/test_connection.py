#!/usr/bin/env python
import time
import json

from tests.unit import  unittest
from boto.cloudformation.connection import CloudFormationConnection


BASIC_EC2_TEMPLATE = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "AWS CloudFormation Sample Template EC2InstanceSample",
    "Parameters": {
        "Parameter1": {
          "Description": "Test Parameter 1", 
          "Type": "String"
        },
        "Parameter2": {
          "Description": "Test Parameter 2", 
          "Type": "String"
        }
    },
    "Mappings": {
        "RegionMap": {
            "us-east-1": {
                "AMI": "ami-7f418316"
            }
        }
    },
    "Resources": {
        "Ec2Instance": {
            "Type": "AWS::EC2::Instance",
            "Properties": {
                "ImageId": {
                    "Fn::FindInMap": [
                        "RegionMap",
                        {
                            "Ref": "AWS::Region"
                        },
                        "AMI"
                    ]
                },
                "UserData": {
                    "Fn::Base64": {
                           "Fn::Join":[
                                       "", 
                                       [{"Ref": "Parameter1"},
                                        {"Ref": "Parameter2"}]
                            ]
                    } 
                    
                }
            }
        }
    },
    "Outputs": {
        "InstanceId": {
            "Description": "InstanceId of the newly created EC2 instance",
            "Value": {
                "Ref": "Ec2Instance"
            }
        },
        "AZ": {
            "Description": "Availability Zone of the newly created EC2 instance",
            "Value": {
                "Fn::GetAtt": [
                    "Ec2Instance",
                    "AvailabilityZone"
                ]
            }
        },
        "PublicIP": {
            "Description": "Public IP address of the newly created EC2 instance",
            "Value": {
                "Fn::GetAtt": [
                    "Ec2Instance",
                    "PublicIp"
                ]
            }
        },
        "PrivateIP": {
            "Description": "Private IP address of the newly created EC2 instance",
            "Value": {
                "Fn::GetAtt": [
                    "Ec2Instance",
                    "PrivateIp"
                ]
            }
        },
        "PublicDNS": {
            "Description": "Public DNSName of the newly created EC2 instance",
            "Value": {
                "Fn::GetAtt": [
                    "Ec2Instance",
                    "PublicDnsName"
                ]
            }
        },
        "PrivateDNS": {
            "Description": "Private DNSName of the newly created EC2 instance",
            "Value": {
                "Fn::GetAtt": [
                    "Ec2Instance",
                    "PrivateDnsName"
                ]
            }
        }
    }
}


class TestCloudformationConnection(unittest.TestCase):
    def setUp(self):
        self.connection = CloudFormationConnection()
        self.stack_name = 'testcfnstack' + str(int(time.time()))

    def test_large_template_stack_size(self):
        # See https://github.com/boto/boto/issues/1037
        body = self.connection.create_stack(
            self.stack_name,
            template_body=json.dumps(BASIC_EC2_TEMPLATE),
            parameters=[('Parameter1', 'initial_value'),
                        ('Parameter2', 'initial_value')])
        self.addCleanup(self.connection.delete_stack, self.stack_name)

        # A newly created stack should have events
        events = self.connection.describe_stack_events(self.stack_name)
        self.assertTrue(events)

        # No policy should be set on the stack by default
        policy = self.connection.get_stack_policy(self.stack_name)
        self.assertEqual(None, policy)

        # Our new stack should show up in the stack list
        stacks = self.connection.describe_stacks(self.stack_name)
        stack = stacks[0]
        self.assertEqual(self.stack_name, stack.stack_name)
        
        params = [(p.key, p.value) for p in stack.parameters]
        self.assertEquals([('Parameter1', 'initial_value'),
                           ('Parameter2', 'initial_value')], params)
        
        for _ in range(30):
            stack.update()
            if stack.stack_status.find("PROGRESS") == -1:
                break
            time.sleep(5)
        
        body = self.connection.update_stack(
             self.stack_name,
             template_body=json.dumps(BASIC_EC2_TEMPLATE),
             parameters=[('Parameter1', '', True),
                         ('Parameter2', 'updated_value')])
        
        stacks = self.connection.describe_stacks(self.stack_name)
        stack = stacks[0]
        params = [(p.key, p.value) for p in stacks[0].parameters]
        self.assertEquals([('Parameter1', 'initial_value'),
                           ('Parameter2', 'updated_value')], params)

        # Waiting for the update to complete to unblock the delete_stack in the
        # cleanup.
        for _ in range(30):
            stack.update()
            if stack.stack_status.find("PROGRESS") == -1:
                break
            time.sleep(5)
        
if __name__ == '__main__':
    unittest.main()
