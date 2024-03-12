#!/usr/bin/env python

import unittest
from boto.s3.cors import CORSConfiguration

CORS_BODY_1 = (
    '<CORSConfiguration>'
    '<CORSRule>'
    '<AllowedMethod>PUT</AllowedMethod>'
    '<AllowedMethod>POST</AllowedMethod>'
    '<AllowedMethod>DELETE</AllowedMethod>'
    '<AllowedOrigin>http://www.example.com</AllowedOrigin>'
    '<AllowedHeader>*</AllowedHeader>'
    '<ExposeHeader>x-amz-server-side-encryption</ExposeHeader>'
    '<MaxAgeSeconds>3000</MaxAgeSeconds>'
    '<ID>foobar_rule</ID>'
    '</CORSRule>'
    '</CORSConfiguration>')

CORS_BODY_2 = (
    '<CORSConfiguration>'
    '<CORSRule>'
    '<AllowedMethod>PUT</AllowedMethod>'
    '<AllowedMethod>POST</AllowedMethod>'
    '<AllowedMethod>DELETE</AllowedMethod>'
    '<AllowedOrigin>http://www.example.com</AllowedOrigin>'
    '<AllowedHeader>*</AllowedHeader>'
    '<ExposeHeader>x-amz-server-side-encryption</ExposeHeader>'
    '<MaxAgeSeconds>3000</MaxAgeSeconds>'
    '</CORSRule>'
    '<CORSRule>'
    '<AllowedMethod>GET</AllowedMethod>'
    '<AllowedOrigin>*</AllowedOrigin>'
    '<AllowedHeader>*</AllowedHeader>'
    '<MaxAgeSeconds>3000</MaxAgeSeconds>'
    '</CORSRule>'
    '</CORSConfiguration>')

CORS_BODY_3 = (
    '<CORSConfiguration>'
    '<CORSRule>'
    '<AllowedMethod>GET</AllowedMethod>'
    '<AllowedOrigin>*</AllowedOrigin>'
    '</CORSRule>'
    '</CORSConfiguration>')


class TestCORSConfiguration(unittest.TestCase):

    def test_one_rule_with_id(self):
        cfg = CORSConfiguration()
        cfg.add_rule(['PUT', 'POST', 'DELETE'],
                     'http://www.example.com',
                     allowed_header='*',
                     max_age_seconds=3000,
                     expose_header='x-amz-server-side-encryption',
                     id='foobar_rule')
        self.assertEqual(cfg.to_xml(), CORS_BODY_1)

    def test_two_rules(self):
        cfg = CORSConfiguration()
        cfg.add_rule(['PUT', 'POST', 'DELETE'],
                     'http://www.example.com',
                     allowed_header='*',
                     max_age_seconds=3000,
                     expose_header='x-amz-server-side-encryption')
        cfg.add_rule('GET', '*', allowed_header='*', max_age_seconds=3000)
        self.assertEqual(cfg.to_xml(), CORS_BODY_2)

    def test_minimal(self):
        cfg = CORSConfiguration()
        cfg.add_rule('GET', '*')
        self.assertEqual(cfg.to_xml(), CORS_BODY_3)


if __name__ == "__main__":
    unittest.main()
