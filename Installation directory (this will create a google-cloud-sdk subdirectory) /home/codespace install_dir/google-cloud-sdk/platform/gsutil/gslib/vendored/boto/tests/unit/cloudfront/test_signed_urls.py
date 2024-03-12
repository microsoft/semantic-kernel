import tempfile
import unittest
from boto.compat import StringIO, six, json
from textwrap import dedent

from boto.cloudfront.distribution import Distribution

class CloudfrontSignedUrlsTest(unittest.TestCase):

    cloudfront = True
    notdefault = True

    def setUp(self):
        self.pk_str = dedent("""
            -----BEGIN RSA PRIVATE KEY-----
            MIICXQIBAAKBgQDA7ki9gI/lRygIoOjV1yymgx6FYFlzJ+z1ATMaLo57nL57AavW
            hb68HYY8EA0GJU9xQdMVaHBogF3eiCWYXSUZCWM/+M5+ZcdQraRRScucmn6g4EvY
            2K4W2pxbqH8vmUikPxir41EeBPLjMOzKvbzzQy9e/zzIQVREKSp/7y1mywIDAQAB
            AoGABc7mp7XYHynuPZxChjWNJZIq+A73gm0ASDv6At7F8Vi9r0xUlQe/v0AQS3yc
            N8QlyR4XMbzMLYk3yjxFDXo4ZKQtOGzLGteCU2srANiLv26/imXA8FVidZftTAtL
            viWQZBVPTeYIA69ATUYPEq0a5u5wjGyUOij9OWyuy01mbPkCQQDluYoNpPOekQ0Z
            WrPgJ5rxc8f6zG37ZVoDBiexqtVShIF5W3xYuWhW5kYb0hliYfkq15cS7t9m95h3
            1QJf/xI/AkEA1v9l/WN1a1N3rOK4VGoCokx7kR2SyTMSbZgF9IWJNOugR/WZw7HT
            njipO3c9dy1Ms9pUKwUF46d7049ck8HwdQJARgrSKuLWXMyBH+/l1Dx/I4tXuAJI
            rlPyo+VmiOc7b5NzHptkSHEPfR9s1OK0VqjknclqCJ3Ig86OMEtEFBzjZQJBAKYz
            470hcPkaGk7tKYAgP48FvxRsnzeooptURW5E+M+PQ2W9iDPPOX9739+Xi02hGEWF
            B0IGbQoTRFdE4VVcPK0CQQCeS84lODlC0Y2BZv2JxW3Osv/WkUQ4dslfAQl1T303
            7uwwr7XTroMv8dIFQIPreoPhRKmd/SbJzbiKfS/4QDhU
            -----END RSA PRIVATE KEY-----
            """)
        self.pk_id = "PK123456789754"
        self.dist = Distribution()
        self.canned_policy = (
            '{"Statement":[{"Resource":'
            '"http://d604721fxaaqy9.cloudfront.net/horizon.jpg'
            '?large=yes&license=yes",'
            '"Condition":{"DateLessThan":{"AWS:EpochTime":1258237200}}}]}')
        self.custom_policy_1 = (
            '{ \n'
            '   "Statement": [{ \n'
            '      "Resource":"http://d604721fxaaqy9.cloudfront.net/training/*", \n'
            '      "Condition":{ \n'
            '         "IpAddress":{"AWS:SourceIp":"145.168.143.0/24"}, \n'
            '         "DateLessThan":{"AWS:EpochTime":1258237200}      \n'
            '      } \n'
            '   }] \n'
            '}\n')
        self.custom_policy_2 = (
            '{ \n'
            '   "Statement": [{ \n'
            '      "Resource":"http://*", \n'
            '      "Condition":{ \n'
            '         "IpAddress":{"AWS:SourceIp":"216.98.35.1/32"},\n'
            '         "DateGreaterThan":{"AWS:EpochTime":1241073790},\n'
            '         "DateLessThan":{"AWS:EpochTime":1255674716}\n'
            '      } \n'
            '   }] \n'
            '}\n')

    def test_encode_custom_policy_1(self):
        """
        Test base64 encoding custom policy 1 from Amazon's documentation.
        """
        expected = ("eyAKICAgIlN0YXRlbWVudCI6IFt7IAogICAgICAiUmVzb3VyY2Ui"
                    "OiJodHRwOi8vZDYwNDcyMWZ4YWFxeTkuY2xvdWRmcm9udC5uZXQv"
                    "dHJhaW5pbmcvKiIsIAogICAgICAiQ29uZGl0aW9uIjp7IAogICAg"
                    "ICAgICAiSXBBZGRyZXNzIjp7IkFXUzpTb3VyY2VJcCI6IjE0NS4x"
                    "NjguMTQzLjAvMjQifSwgCiAgICAgICAgICJEYXRlTGVzc1RoYW4i"
                    "OnsiQVdTOkVwb2NoVGltZSI6MTI1ODIzNzIwMH0gICAgICAKICAg"
                    "ICAgfSAKICAgfV0gCn0K")
        encoded = self.dist._url_base64_encode(self.custom_policy_1)
        self.assertEqual(expected, encoded)

    def test_encode_custom_policy_2(self):
        """
        Test base64 encoding custom policy 2 from Amazon's documentation.
        """
        expected = ("eyAKICAgIlN0YXRlbWVudCI6IFt7IAogICAgICAiUmVzb3VyY2Ui"
                    "OiJodHRwOi8vKiIsIAogICAgICAiQ29uZGl0aW9uIjp7IAogICAg"
                    "ICAgICAiSXBBZGRyZXNzIjp7IkFXUzpTb3VyY2VJcCI6IjIxNi45"
                    "OC4zNS4xLzMyIn0sCiAgICAgICAgICJEYXRlR3JlYXRlclRoYW4i"
                    "OnsiQVdTOkVwb2NoVGltZSI6MTI0MTA3Mzc5MH0sCiAgICAgICAg"
                    "ICJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTI1NTY3"
                    "NDcxNn0KICAgICAgfSAKICAgfV0gCn0K")
        encoded = self.dist._url_base64_encode(self.custom_policy_2)
        self.assertEqual(expected, encoded)

    def test_sign_canned_policy(self):
        """
        Test signing the canned policy from amazon's cloudfront documentation.
        """
        expected = ("Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyEXPDN"
                    "v0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4kXAJK6td"
                    "Nx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCMIYHIaiOB6~5j"
                    "t9w2EOwi6sIIqrg_")
        sig = self.dist._sign_string(self.canned_policy, private_key_string=self.pk_str)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_sign_canned_policy_pk_file(self):
        """
        Test signing the canned policy from amazon's cloudfront documentation
        with a file object.
        """
        expected = ("Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyEXPDN"
                    "v0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4kXAJK6td"
                    "Nx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCMIYHIaiOB6~5j"
                    "t9w2EOwi6sIIqrg_")
        pk_file = tempfile.TemporaryFile()
        pk_file.write(self.pk_str)
        pk_file.seek(0)
        sig = self.dist._sign_string(self.canned_policy, private_key_file=pk_file)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_sign_canned_policy_pk_file_name(self):
        """
        Test signing the canned policy from amazon's cloudfront documentation
        with a file name.
        """
        expected = ("Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyEXPDN"
                    "v0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4kXAJK6td"
                    "Nx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCMIYHIaiOB6~5j"
                    "t9w2EOwi6sIIqrg_")
        pk_file = tempfile.NamedTemporaryFile()
        pk_file.write(self.pk_str)
        pk_file.flush()
        sig = self.dist._sign_string(self.canned_policy, private_key_file=pk_file.name)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_sign_canned_policy_pk_file_like(self):
        """
        Test signing the canned policy from amazon's cloudfront documentation
        with a file-like object (not a subclass of 'file' type)
        """
        expected = ("Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyEXPDN"
                    "v0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4kXAJK6td"
                    "Nx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCMIYHIaiOB6~5j"
                    "t9w2EOwi6sIIqrg_")
        pk_file = StringIO()
        pk_file.write(self.pk_str)
        pk_file.seek(0)
        sig = self.dist._sign_string(self.canned_policy, private_key_file=pk_file)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_sign_canned_policy_unicode(self):
        """
        Test signing the canned policy from amazon's cloudfront documentation.
        """
        expected = ("Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyEXPDN"
                    "v0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4kXAJK6td"
                    "Nx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCMIYHIaiOB6~5j"
                    "t9w2EOwi6sIIqrg_")
        unicode_policy = six.text_type(self.canned_policy)
        sig = self.dist._sign_string(unicode_policy, private_key_string=self.pk_str)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_sign_custom_policy_1(self):
        """
        Test signing custom policy 1 from amazon's cloudfront documentation.
        """
        expected = ("cPFtRKvUfYNYmxek6ZNs6vgKEZP6G3Cb4cyVt~FjqbHOnMdxdT7e"
                    "T6pYmhHYzuDsFH4Jpsctke2Ux6PCXcKxUcTIm8SO4b29~1QvhMl-"
                    "CIojki3Hd3~Unxjw7Cpo1qRjtvrimW0DPZBZYHFZtiZXsaPt87yB"
                    "P9GWnTQoaVysMxQ_")
        sig = self.dist._sign_string(self.custom_policy_1, private_key_string=self.pk_str)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_sign_custom_policy_2(self):
        """
        Test signing custom policy 2 from amazon's cloudfront documentation.
        """
        expected = ("rc~5Qbbm8EJXjUTQ6Cn0LAxR72g1DOPrTmdtfbWVVgQNw0q~KHUA"
                    "mBa2Zv1Wjj8dDET4XSL~Myh44CLQdu4dOH~N9huH7QfPSR~O4tIO"
                    "S1WWcP~2JmtVPoQyLlEc8YHRCuN3nVNZJ0m4EZcXXNAS-0x6Zco2"
                    "SYx~hywTRxWR~5Q_")
        sig = self.dist._sign_string(self.custom_policy_2, private_key_string=self.pk_str)
        encoded_sig = self.dist._url_base64_encode(sig)
        self.assertEqual(expected, encoded_sig)

    def test_create_canned_policy(self):
        """
        Test that a canned policy is generated correctly.
        """
        url = "http://1234567.cloudfront.com/test_resource.mp3?dog=true"
        expires = 999999
        policy = self.dist._canned_policy(url, expires)
        policy = json.loads(policy)

        self.assertEqual(1, len(policy.keys()))
        statements = policy["Statement"]
        self.assertEqual(1, len(statements))
        statement = statements[0]
        resource = statement["Resource"]
        self.assertEqual(url, resource)
        condition = statement["Condition"]
        self.assertEqual(1, len(condition.keys()))
        date_less_than = condition["DateLessThan"]
        self.assertEqual(1, len(date_less_than.keys()))
        aws_epoch_time = date_less_than["AWS:EpochTime"]
        self.assertEqual(expires, aws_epoch_time)
        
    def test_custom_policy_expires_and_policy_url(self):
        """
        Test that a custom policy can be created with an expire time and an
        arbitrary URL.
        """
        url = "http://1234567.cloudfront.com/*"
        expires = 999999
        policy = self.dist._custom_policy(url, expires=expires)
        policy = json.loads(policy)

        self.assertEqual(1, len(policy.keys()))
        statements = policy["Statement"]
        self.assertEqual(1, len(statements))
        statement = statements[0]
        resource = statement["Resource"]
        self.assertEqual(url, resource)
        condition = statement["Condition"]
        self.assertEqual(1, len(condition.keys()))
        date_less_than = condition["DateLessThan"]
        self.assertEqual(1, len(date_less_than.keys()))
        aws_epoch_time = date_less_than["AWS:EpochTime"]
        self.assertEqual(expires, aws_epoch_time)

    def test_custom_policy_valid_after(self):
        """
        Test that a custom policy can be created with a valid-after time and
        an arbitrary URL.
        """
        url = "http://1234567.cloudfront.com/*"
        valid_after = 999999
        policy = self.dist._custom_policy(url, valid_after=valid_after)
        policy = json.loads(policy)

        self.assertEqual(1, len(policy.keys()))
        statements = policy["Statement"]
        self.assertEqual(1, len(statements))
        statement = statements[0]
        resource = statement["Resource"]
        self.assertEqual(url, resource)
        condition = statement["Condition"]
        self.assertEqual(2, len(condition.keys()))
        date_less_than = condition["DateLessThan"]
        date_greater_than = condition["DateGreaterThan"]
        self.assertEqual(1, len(date_greater_than.keys()))
        aws_epoch_time = date_greater_than["AWS:EpochTime"]
        self.assertEqual(valid_after, aws_epoch_time)

    def test_custom_policy_ip_address(self):
        """
        Test that a custom policy can be created with an IP address and
        an arbitrary URL.
        """
        url = "http://1234567.cloudfront.com/*"
        ip_range = "192.168.0.1"
        policy = self.dist._custom_policy(url, ip_address=ip_range)
        policy = json.loads(policy)

        self.assertEqual(1, len(policy.keys()))
        statements = policy["Statement"]
        self.assertEqual(1, len(statements))
        statement = statements[0]
        resource = statement["Resource"]
        self.assertEqual(url, resource)
        condition = statement["Condition"]
        self.assertEqual(2, len(condition.keys()))
        ip_address = condition["IpAddress"]
        self.assertTrue("DateLessThan" in condition)
        self.assertEqual(1, len(ip_address.keys()))
        source_ip = ip_address["AWS:SourceIp"]
        self.assertEqual("%s/32" % ip_range, source_ip)

    def test_custom_policy_ip_range(self):
        """
        Test that a custom policy can be created with an IP address and
        an arbitrary URL.
        """
        url = "http://1234567.cloudfront.com/*"
        ip_range = "192.168.0.0/24"
        policy = self.dist._custom_policy(url, ip_address=ip_range)
        policy = json.loads(policy)

        self.assertEqual(1, len(policy.keys()))
        statements = policy["Statement"]
        self.assertEqual(1, len(statements))
        statement = statements[0]
        resource = statement["Resource"]
        self.assertEqual(url, resource)
        condition = statement["Condition"]
        self.assertEqual(2, len(condition.keys()))
        self.assertTrue("DateLessThan" in condition)
        ip_address = condition["IpAddress"]
        self.assertEqual(1, len(ip_address.keys()))
        source_ip = ip_address["AWS:SourceIp"]
        self.assertEqual(ip_range, source_ip)

    def test_custom_policy_all(self):
        """
        Test that a custom policy can be created with an IP address and
        an arbitrary URL.
        """
        url = "http://1234567.cloudfront.com/test.txt"
        expires = 999999
        valid_after = 111111
        ip_range = "192.168.0.0/24"
        policy = self.dist._custom_policy(url, expires=expires,
                                          valid_after=valid_after,
                                          ip_address=ip_range)
        policy = json.loads(policy)

        self.assertEqual(1, len(policy.keys()))
        statements = policy["Statement"]
        self.assertEqual(1, len(statements))
        statement = statements[0]
        resource = statement["Resource"]
        self.assertEqual(url, resource)
        condition = statement["Condition"]
        self.assertEqual(3, len(condition.keys()))
        #check expires condition
        date_less_than = condition["DateLessThan"]
        self.assertEqual(1, len(date_less_than.keys()))
        aws_epoch_time = date_less_than["AWS:EpochTime"]
        self.assertEqual(expires, aws_epoch_time)
        #check valid_after condition
        date_greater_than = condition["DateGreaterThan"]
        self.assertEqual(1, len(date_greater_than.keys()))
        aws_epoch_time = date_greater_than["AWS:EpochTime"]
        self.assertEqual(valid_after, aws_epoch_time)
        #check source ip address condition
        ip_address = condition["IpAddress"]
        self.assertEqual(1, len(ip_address.keys()))
        source_ip = ip_address["AWS:SourceIp"]
        self.assertEqual(ip_range, source_ip)

    def test_params_canned_policy(self):
        """
        Test the correct params are generated for a canned policy.
        """
        url = "http://d604721fxaaqy9.cloudfront.net/horizon.jpg?large=yes&license=yes"
        expire_time = 1258237200
        expected_sig = ("Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyE"
                        "XPDNv0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4"
                        "kXAJK6tdNx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCM"
                        "IYHIaiOB6~5jt9w2EOwi6sIIqrg_")
        signed_url_params = self.dist._create_signing_params(url, self.pk_id, expire_time, private_key_string=self.pk_str)
        self.assertEqual(3, len(signed_url_params))
        self.assertEqual(signed_url_params["Expires"], "1258237200")
        self.assertEqual(signed_url_params["Signature"], expected_sig)
        self.assertEqual(signed_url_params["Key-Pair-Id"], "PK123456789754")

    def test_canned_policy(self):
        """
        Generate signed url from the Example Canned Policy in Amazon's
        documentation.
        """
        url = "http://d604721fxaaqy9.cloudfront.net/horizon.jpg?large=yes&license=yes"
        expire_time = 1258237200
        expected_url = "http://d604721fxaaqy9.cloudfront.net/horizon.jpg?large=yes&license=yes&Expires=1258237200&Signature=Nql641NHEUkUaXQHZINK1FZ~SYeUSoBJMxjdgqrzIdzV2gyEXPDNv0pYdWJkflDKJ3xIu7lbwRpSkG98NBlgPi4ZJpRRnVX4kXAJK6tdNx6FucDB7OVqzcxkxHsGFd8VCG1BkC-Afh9~lOCMIYHIaiOB6~5jt9w2EOwi6sIIqrg_&Key-Pair-Id=PK123456789754"
        signed_url = self.dist.create_signed_url(
            url, self.pk_id, expire_time, private_key_string=self.pk_str)
        self.assertEqual(expected_url, signed_url)

