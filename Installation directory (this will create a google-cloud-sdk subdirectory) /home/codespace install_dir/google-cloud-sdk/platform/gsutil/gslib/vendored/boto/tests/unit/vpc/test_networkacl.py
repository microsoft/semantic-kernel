from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.vpc import VPCConnection


class TestDescribeNetworkAcls(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DescribeNetworkAclsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <networkAclSet>
               <item>
                 <networkAclId>acl-5566953c</networkAclId>
                 <vpcId>vpc-5266953b</vpcId>
                 <default>true</default>
                 <entrySet>
                   <item>
                     <ruleNumber>100</ruleNumber>
                     <protocol>all</protocol>
                     <ruleAction>allow</ruleAction>
                     <egress>true</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                   </item>
                   <item>
                     <ruleNumber>32767</ruleNumber>
                     <protocol>all</protocol>
                     <ruleAction>deny</ruleAction>
                     <egress>true</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                   </item>
                   <item>
                     <ruleNumber>100</ruleNumber>
                     <protocol>all</protocol>
                     <ruleAction>allow</ruleAction>
                     <egress>false</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                   </item>
                   <item>
                     <ruleNumber>32767</ruleNumber>
                     <protocol>all</protocol>
                     <ruleAction>deny</ruleAction>
                     <egress>false</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                   </item>
                 </entrySet>
                 <associationSet/>
                 <tagSet/>
               </item>
               <item>
                 <networkAclId>acl-5d659634</networkAclId>
                 <vpcId>vpc-5266953b</vpcId>
                 <default>false</default>
                 <entrySet>
                   <item>
                     <ruleNumber>110</ruleNumber>
                     <protocol>6</protocol>
                     <ruleAction>allow</ruleAction>
                     <egress>true</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                     <portRange>
                       <from>49152</from>
                       <to>65535</to>
                     </portRange>
                   </item>
                   <item>
                     <ruleNumber>32767</ruleNumber>
                     <protocol>all</protocol>
                     <ruleAction>deny</ruleAction>
                     <egress>true</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                   </item>
                   <item>
                     <ruleNumber>110</ruleNumber>
                     <protocol>6</protocol>
                     <ruleAction>allow</ruleAction>
                     <egress>false</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                     <portRange>
                       <from>80</from>
                       <to>80</to>
                     </portRange>
                   </item>
                   <item>
                     <ruleNumber>120</ruleNumber>
                     <protocol>6</protocol>
                     <ruleAction>allow</ruleAction>
                     <egress>false</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                     <portRange>
                       <from>443</from>
                       <to>443</to>
                     </portRange>
                   </item>
                   <item>
                     <ruleNumber>32767</ruleNumber>
                     <protocol>all</protocol>
                     <ruleAction>deny</ruleAction>
                     <egress>false</egress>
                     <cidrBlock>0.0.0.0/0</cidrBlock>
                   </item>
                 </entrySet>
                 <associationSet>
                   <item>
                     <networkAclAssociationId>aclassoc-5c659635</networkAclAssociationId>
                     <networkAclId>acl-5d659634</networkAclId>
                     <subnetId>subnet-ff669596</subnetId>
                   </item>
                   <item>
                     <networkAclAssociationId>aclassoc-c26596ab</networkAclAssociationId>
                     <networkAclId>acl-5d659634</networkAclId>
                     <subnetId>subnet-f0669599</subnetId>
                   </item>
                 </associationSet>
                 <tagSet/>
               </item>
             </networkAclSet>
            </DescribeNetworkAclsResponse>
        """

    def test_get_all_network_acls(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_network_acls(['acl-5566953c', 'acl-5d659634'],
                                                                [('vpc-id', 'vpc-5266953b')])
        self.assert_request_parameters({
            'Action': 'DescribeNetworkAcls',
            'NetworkAclId.1': 'acl-5566953c',
            'NetworkAclId.2': 'acl-5d659634',
            'Filter.1.Name': 'vpc-id',
            'Filter.1.Value.1': 'vpc-5266953b'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(response), 2)


class TestReplaceNetworkAclAssociation(AWSMockServiceTestCase):

    connection_class = VPCConnection

    get_all_network_acls_vpc_body = b"""
        <DescribeNetworkAclsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
           <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
           <networkAclSet>
           <item>
             <networkAclId>acl-5566953c</networkAclId>
             <vpcId>vpc-5266953b</vpcId>
             <default>true</default>
             <entrySet>
               <item>
                 <ruleNumber>100</ruleNumber>
                 <protocol>all</protocol>
                 <ruleAction>allow</ruleAction>
                 <egress>true</egress>
                 <cidrBlock>0.0.0.0/0</cidrBlock>
               </item>
               <item>
                 <ruleNumber>32767</ruleNumber>
                 <protocol>all</protocol>
                 <ruleAction>deny</ruleAction>
                 <egress>true</egress>
                 <cidrBlock>0.0.0.0/0</cidrBlock>
               </item>
               <item>
                 <ruleNumber>100</ruleNumber>
                 <protocol>all</protocol>
                 <ruleAction>allow</ruleAction>
                 <egress>false</egress>
                 <cidrBlock>0.0.0.0/0</cidrBlock>
               </item>
               <item>
                 <ruleNumber>32767</ruleNumber>
                 <protocol>all</protocol>
                 <ruleAction>deny</ruleAction>
                 <egress>false</egress>
                 <cidrBlock>0.0.0.0/0</cidrBlock>
               </item>
             </entrySet>
             <associationSet/>
             <tagSet/>
           </item>

         </networkAclSet>
        </DescribeNetworkAclsResponse>
    """

    get_all_network_acls_subnet_body = b"""
        <DescribeNetworkAclsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
            <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
            <networkAclSet>
            <item>
              <networkAclId>acl-5d659634</networkAclId>
              <vpcId>vpc-5266953b</vpcId>
              <default>false</default>
              <entrySet>
                <item>
                  <ruleNumber>110</ruleNumber>
                  <protocol>6</protocol>
                  <ruleAction>allow</ruleAction>
                  <egress>true</egress>
                  <cidrBlock>0.0.0.0/0</cidrBlock>
                  <portRange>
                    <from>49152</from>
                    <to>65535</to>
                  </portRange>
                </item>
              </entrySet>
              <associationSet>
                <item>
                  <networkAclAssociationId>aclassoc-c26596ab</networkAclAssociationId>
                  <networkAclId>acl-5d659634</networkAclId>
                  <subnetId>subnet-f0669599</subnetId>
                </item>
                <item>
                  <networkAclAssociationId>aclassoc-5c659635</networkAclAssociationId>
                  <networkAclId>acl-5d659634</networkAclId>
                  <subnetId>subnet-ff669596</subnetId>
                </item>
              </associationSet>
              <tagSet/>
            </item>
          </networkAclSet>
        </DescribeNetworkAclsResponse>
    """

    def default_body(self):
        return b"""
            <ReplaceNetworkAclAssociationResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <newAssociationId>aclassoc-17b85d7e</newAssociationId>
            </ReplaceNetworkAclAssociationResponse>
        """

    def test_associate_network_acl(self):
        self.https_connection.getresponse.side_effect = [
            self.create_response(status_code=200, body=self.get_all_network_acls_subnet_body),
            self.create_response(status_code=200)
        ]
        response = self.service_connection.associate_network_acl('acl-5fb85d36', 'subnet-ff669596')
        # Note: Not testing proper call to get_all_network_acls!
        self.assert_request_parameters({
            'Action': 'ReplaceNetworkAclAssociation',
            'NetworkAclId': 'acl-5fb85d36',
            'AssociationId': 'aclassoc-5c659635'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, 'aclassoc-17b85d7e')

    def test_disassociate_network_acl(self):
        self.https_connection.getresponse.side_effect = [
            self.create_response(status_code=200, body=self.get_all_network_acls_vpc_body),
            self.create_response(status_code=200, body=self.get_all_network_acls_subnet_body),
            self.create_response(status_code=200)
        ]
        response = self.service_connection.disassociate_network_acl('subnet-ff669596',
                                                                    'vpc-5266953b')
        # Note: Not testing proper call to either call to get_all_network_acls!
        self.assert_request_parameters({
            'Action': 'ReplaceNetworkAclAssociation',
            'NetworkAclId': 'acl-5566953c',
            'AssociationId': 'aclassoc-5c659635'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, 'aclassoc-17b85d7e')


class TestCreateNetworkAcl(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateNetworkAclResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <networkAcl>
                  <networkAclId>acl-5fb85d36</networkAclId>
                  <vpcId>vpc-11ad4878</vpcId>
                  <default>false</default>
                  <entrySet>
                     <item>
                        <ruleNumber>32767</ruleNumber>
                        <protocol>all</protocol>
                        <ruleAction>deny</ruleAction>
                        <egress>true</egress>
                        <cidrBlock>0.0.0.0/0</cidrBlock>
                     </item>
                     <item>
                        <ruleNumber>32767</ruleNumber>
                        <protocol>all</protocol>
                        <ruleAction>deny</ruleAction>
                        <egress>false</egress>
                        <cidrBlock>0.0.0.0/0</cidrBlock>
                     </item>
                  </entrySet>
                  <associationSet/>
                  <tagSet/>
               </networkAcl>
            </CreateNetworkAclResponse>
        """

    def test_create_network_acl(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.create_network_acl('vpc-11ad4878')
        self.assert_request_parameters({
            'Action': 'CreateNetworkAcl',
            'VpcId': 'vpc-11ad4878'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response.id, 'acl-5fb85d36')


class DeleteCreateNetworkAcl(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteNetworkAclResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DeleteNetworkAclResponse>
        """

    def test_delete_network_acl(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.delete_network_acl('acl-2cb85d45')
        self.assert_request_parameters({
            'Action': 'DeleteNetworkAcl',
            'NetworkAclId': 'acl-2cb85d45'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, True)


class TestCreateNetworkAclEntry(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <CreateNetworkAclEntryResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </CreateNetworkAclEntryResponse>
        """

    def test_create_network_acl(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.create_network_acl_entry(
            'acl-2cb85d45', 110, 'udp', 'allow', '0.0.0.0/0', egress=False,
            port_range_from=53, port_range_to=53)
        self.assert_request_parameters({
            'Action': 'CreateNetworkAclEntry',
            'NetworkAclId': 'acl-2cb85d45',
            'RuleNumber': 110,
            'Protocol': 'udp',
            'RuleAction': 'allow',
            'Egress': 'false',
            'CidrBlock': '0.0.0.0/0',
            'PortRange.From': 53,
            'PortRange.To': 53},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, True)

    def test_create_network_acl_icmp(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.create_network_acl_entry(
            'acl-2cb85d45', 110, 'udp', 'allow', '0.0.0.0/0', egress='true',
            icmp_code=-1, icmp_type=8)
        self.assert_request_parameters({
            'Action': 'CreateNetworkAclEntry',
            'NetworkAclId': 'acl-2cb85d45',
            'RuleNumber': 110,
            'Protocol': 'udp',
            'RuleAction': 'allow',
            'Egress': 'true',
            'CidrBlock': '0.0.0.0/0',
            'Icmp.Code': -1,
            'Icmp.Type': 8},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, True)


class TestReplaceNetworkAclEntry(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <ReplaceNetworkAclEntryResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </ReplaceNetworkAclEntryResponse>
        """

    def test_replace_network_acl(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.replace_network_acl_entry(
            'acl-2cb85d45', 110, 'tcp', 'deny', '0.0.0.0/0', egress=False,
            port_range_from=139, port_range_to=139)
        self.assert_request_parameters({
            'Action': 'ReplaceNetworkAclEntry',
            'NetworkAclId': 'acl-2cb85d45',
            'RuleNumber': 110,
            'Protocol': 'tcp',
            'RuleAction': 'deny',
            'Egress': 'false',
            'CidrBlock': '0.0.0.0/0',
            'PortRange.From': 139,
            'PortRange.To': 139},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, True)

    def test_replace_network_acl_icmp(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.replace_network_acl_entry(
            'acl-2cb85d45', 110, 'tcp', 'deny', '0.0.0.0/0',
            icmp_code=-1, icmp_type=8)
        self.assert_request_parameters({
            'Action': 'ReplaceNetworkAclEntry',
            'NetworkAclId': 'acl-2cb85d45',
            'RuleNumber': 110,
            'Protocol': 'tcp',
            'RuleAction': 'deny',
            'CidrBlock': '0.0.0.0/0',
            'Icmp.Code': -1,
            'Icmp.Type': 8},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, True)


class TestDeleteNetworkAclEntry(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
            <DeleteNetworkAclEntryResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <return>true</return>
            </DeleteNetworkAclEntryResponse>
        """

    def test_delete_network_acl(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.delete_network_acl_entry('acl-2cb85d45', 100,
                                                                    egress=False)
        self.assert_request_parameters({
            'Action': 'DeleteNetworkAclEntry',
            'NetworkAclId': 'acl-2cb85d45',
            'RuleNumber': 100,
            'Egress': 'false'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(response, True)


class TestGetNetworkAclAssociations(AWSMockServiceTestCase):

    connection_class = VPCConnection

    def default_body(self):
        return b"""
        <DescribeNetworkAclsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
            <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
            <networkAclSet>
            <item>
              <networkAclId>acl-5d659634</networkAclId>
              <vpcId>vpc-5266953b</vpcId>
              <default>false</default>
              <entrySet>
                <item>
                  <ruleNumber>110</ruleNumber>
                  <protocol>6</protocol>
                  <ruleAction>allow</ruleAction>
                  <egress>true</egress>
                  <cidrBlock>0.0.0.0/0</cidrBlock>
                  <portRange>
                    <from>49152</from>
                    <to>65535</to>
                  </portRange>
                </item>
              </entrySet>
              <associationSet>
                <item>
                  <networkAclAssociationId>aclassoc-c26596ab</networkAclAssociationId>
                  <networkAclId>acl-5d659634</networkAclId>
                  <subnetId>subnet-f0669599</subnetId>
                </item>
              </associationSet>
              <tagSet/>
            </item>
          </networkAclSet>
        </DescribeNetworkAclsResponse>
    """

    def test_get_network_acl_associations(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.get_all_network_acls()
        association = api_response[0].associations[0]
        self.assertEqual(association.network_acl_id, 'acl-5d659634')


if __name__ == '__main__':
    unittest.main()
