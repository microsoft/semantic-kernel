# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from tests.unit import unittest
import xml.dom.minidom
import xml.sax

from boto.s3.website import WebsiteConfiguration
from boto.s3.website import RedirectLocation
from boto.s3.website import RoutingRules
from boto.s3.website import Condition
from boto.s3.website import RoutingRules
from boto.s3.website import RoutingRule
from boto.s3.website import Redirect
from boto import handler


def pretty_print_xml(text):
    text = ''.join(t.strip() for t in text.splitlines())
    x = xml.dom.minidom.parseString(text)
    return x.toprettyxml()


class TestS3WebsiteConfiguration(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_suffix_only(self):
        config = WebsiteConfiguration(suffix='index.html')
        xml = config.to_xml()
        self.assertIn(
            '<IndexDocument><Suffix>index.html</Suffix></IndexDocument>', xml)

    def test_suffix_and_error(self):
        config = WebsiteConfiguration(suffix='index.html',
                                      error_key='error.html')
        xml = config.to_xml()
        self.assertIn(
            '<ErrorDocument><Key>error.html</Key></ErrorDocument>', xml)

    def test_redirect_all_request_to_with_just_host(self):
        location = RedirectLocation(hostname='example.com')
        config = WebsiteConfiguration(redirect_all_requests_to=location)
        xml = config.to_xml()
        self.assertIn(
            ('<RedirectAllRequestsTo><HostName>'
             'example.com</HostName></RedirectAllRequestsTo>'), xml)

    def test_redirect_all_requests_with_protocol(self):
        location = RedirectLocation(hostname='example.com', protocol='https')
        config = WebsiteConfiguration(redirect_all_requests_to=location)
        xml = config.to_xml()
        self.assertIn(
            ('<RedirectAllRequestsTo><HostName>'
             'example.com</HostName><Protocol>https</Protocol>'
             '</RedirectAllRequestsTo>'), xml)

    def test_routing_rules_key_prefix(self):
        x = pretty_print_xml
        # This rule redirects requests for docs/* to documentation/*
        rules = RoutingRules()
        condition = Condition(key_prefix='docs/')
        redirect = Redirect(replace_key_prefix='documents/')
        rules.add_rule(RoutingRule(condition, redirect))
        config = WebsiteConfiguration(suffix='index.html', routing_rules=rules)
        xml = config.to_xml()

        expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <WebsiteConfiguration xmlns='http://s3.amazonaws.com/doc/2006-03-01/'>
              <IndexDocument>
                <Suffix>index.html</Suffix>
              </IndexDocument>
              <RoutingRules>
                <RoutingRule>
                <Condition>
                  <KeyPrefixEquals>docs/</KeyPrefixEquals>
                </Condition>
                <Redirect>
                  <ReplaceKeyPrefixWith>documents/</ReplaceKeyPrefixWith>
                </Redirect>
                </RoutingRule>
              </RoutingRules>
            </WebsiteConfiguration>
        """
        self.assertEqual(x(expected_xml), x(xml))

    def test_routing_rules_to_host_on_404(self):
        x = pretty_print_xml
        # Another example from the docs:
        # Redirect requests to a specific host in the event of a 404.
        # Also, the redirect inserts a report-404/.  For example,
        # if you request a page ExamplePage.html and it results
        # in a 404, the request is routed to a page report-404/ExamplePage.html
        rules = RoutingRules()
        condition = Condition(http_error_code=404)
        redirect = Redirect(hostname='example.com',
                            replace_key_prefix='report-404/')
        rules.add_rule(RoutingRule(condition, redirect))
        config = WebsiteConfiguration(suffix='index.html', routing_rules=rules)
        xml = config.to_xml()

        expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <WebsiteConfiguration xmlns='http://s3.amazonaws.com/doc/2006-03-01/'>
              <IndexDocument>
                <Suffix>index.html</Suffix>
              </IndexDocument>
              <RoutingRules>
                <RoutingRule>
                <Condition>
                  <HttpErrorCodeReturnedEquals>404</HttpErrorCodeReturnedEquals>
                </Condition>
                <Redirect>
                  <HostName>example.com</HostName>
                  <ReplaceKeyPrefixWith>report-404/</ReplaceKeyPrefixWith>
                </Redirect>
                </RoutingRule>
              </RoutingRules>
            </WebsiteConfiguration>
        """
        self.assertEqual(x(expected_xml), x(xml))

    def test_key_prefix(self):
        x = pretty_print_xml
        rules = RoutingRules()
        condition = Condition(key_prefix="images/")
        redirect = Redirect(replace_key='folderdeleted.html')
        rules.add_rule(RoutingRule(condition, redirect))
        config = WebsiteConfiguration(suffix='index.html', routing_rules=rules)
        xml = config.to_xml()

        expected_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <WebsiteConfiguration xmlns='http://s3.amazonaws.com/doc/2006-03-01/'>
              <IndexDocument>
                <Suffix>index.html</Suffix>
              </IndexDocument>
              <RoutingRules>
                <RoutingRule>
                <Condition>
                  <KeyPrefixEquals>images/</KeyPrefixEquals>
                </Condition>
                <Redirect>
                  <ReplaceKeyWith>folderdeleted.html</ReplaceKeyWith>
                </Redirect>
                </RoutingRule>
              </RoutingRules>
            </WebsiteConfiguration>
        """
        self.assertEqual(x(expected_xml), x(xml))

    def test_builders(self):
        x = pretty_print_xml
        # This is a more declarative way to create rules.
        # First the long way.
        rules = RoutingRules()
        condition = Condition(http_error_code=404)
        redirect = Redirect(hostname='example.com',
                            replace_key_prefix='report-404/')
        rules.add_rule(RoutingRule(condition, redirect))
        xml = rules.to_xml()

        # Then the more concise way.
        rules2 = RoutingRules().add_rule(
            RoutingRule.when(http_error_code=404).then_redirect(
                hostname='example.com', replace_key_prefix='report-404/'))
        xml2 = rules2.to_xml()
        self.assertEqual(x(xml), x(xml2))

    def test_parse_xml(self):
        x = pretty_print_xml
        xml_in = """<?xml version="1.0" encoding="UTF-8"?>
            <WebsiteConfiguration xmlns='http://s3.amazonaws.com/doc/2006-03-01/'>
              <IndexDocument>
                <Suffix>index.html</Suffix>
              </IndexDocument>
              <ErrorDocument>
                <Key>error.html</Key>
              </ErrorDocument>
              <RoutingRules>
                <RoutingRule>
                <Condition>
                  <KeyPrefixEquals>docs/</KeyPrefixEquals>
                </Condition>
                <Redirect>
                  <Protocol>https</Protocol>
                  <HostName>www.example.com</HostName>
                  <ReplaceKeyWith>documents/</ReplaceKeyWith>
                  <HttpRedirectCode>302</HttpRedirectCode>
                </Redirect>
                </RoutingRule>
                <RoutingRule>
                <Condition>
                  <HttpErrorCodeReturnedEquals>404</HttpErrorCodeReturnedEquals>
                </Condition>
                <Redirect>
                  <HostName>example.com</HostName>
                  <ReplaceKeyPrefixWith>report-404/</ReplaceKeyPrefixWith>
                </Redirect>
                </RoutingRule>
              </RoutingRules>
            </WebsiteConfiguration>
        """
        webconfig = WebsiteConfiguration()
        h = handler.XmlHandler(webconfig, None)
        xml.sax.parseString(xml_in.encode('utf-8'), h)
        xml_out = webconfig.to_xml()
        self.assertEqual(x(xml_in), x(xml_out))
