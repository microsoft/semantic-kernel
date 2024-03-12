#!/usr/bin env python
import json
import mock
from tests.unit import AWSMockServiceTestCase
from boto.cloudsearch2.domain import Domain
from boto.cloudsearch2.layer1 import CloudSearchConnection
from boto.cloudsearchdomain.layer1 import CloudSearchDomainConnection


class CloudSearchDomainConnectionTest(AWSMockServiceTestCase):
    connection_class = CloudSearchDomainConnection

    domain_status = """{
        "SearchInstanceType": null,
        "DomainId": "1234567890/demo",
        "DomainName": "demo",
        "Deleted": false,
        "SearchInstanceCount": 0,
        "Created": true,
        "SearchService": {
          "Endpoint": "search-demo.us-east-1.cloudsearch.amazonaws.com"
        },
        "RequiresIndexDocuments": false,
        "Processing": false,
        "DocService": {
          "Endpoint": "doc-demo.us-east-1.cloudsearch.amazonaws.com"
        },
        "ARN": "arn:aws:cs:us-east-1:1234567890:domain/demo",
        "SearchPartitionCount": 0
      }"""

    def create_service_connection(self, **kwargs):
        if kwargs.get('host', None) is None:
            kwargs['host'] = 'search-demo.us-east-1.cloudsearch.amazonaws.com'
        return super(CloudSearchDomainConnectionTest, self).\
            create_service_connection(**kwargs)

    def test_get_search_service(self):
        layer1 = CloudSearchConnection(aws_access_key_id='aws_access_key_id',
                                       aws_secret_access_key='aws_secret_access_key',
                                       sign_request=True)
        domain = Domain(layer1=layer1, data=json.loads(self.domain_status))
        search_service = domain.get_search_service()

        self.assertEqual(search_service.sign_request, True)

    def test_get_document_service(self):
        layer1 = CloudSearchConnection(aws_access_key_id='aws_access_key_id',
                                       aws_secret_access_key='aws_secret_access_key',
                                       sign_request=True)
        domain = Domain(layer1=layer1, data=json.loads(self.domain_status))
        document_service = domain.get_document_service()

        self.assertEqual(document_service.sign_request, True)

    def test_search_with_auth(self):
        layer1 = CloudSearchConnection(aws_access_key_id='aws_access_key_id',
                                       aws_secret_access_key='aws_secret_access_key',
                                       sign_request=True)
        domain = Domain(layer1=layer1, data=json.loads(self.domain_status))
        search_service = domain.get_search_service()

        response = {
            'rank': '-text_relevance',
            'match-expr': "Test",
            'hits': {
                'found': 30,
                'start': 0,
                'hit': {
                    'id': '12341',
                    'fields': {
                        'title': 'Document 1',
                        'rank': 1
                    }
                }
            },
            'status': {
                'rid': 'b7c167f6c2da6d93531b9a7b314ad030b3a74803b4b7797edb905ba5a6a08',
                'time-ms': 2,
                'cpu-time-ms': 0
            }

        }

        self.set_http_response(status_code=200,
                               body=json.dumps(response).encode('utf-8'))
        search_service.domain_connection = self.service_connection
        resp = search_service.search()

        headers = self.actual_request.headers

        self.assertIsNotNone(headers.get('Authorization'))

    def test_upload_documents_with_auth(self):
        layer1 = CloudSearchConnection(aws_access_key_id='aws_access_key_id',
                                       aws_secret_access_key='aws_secret_access_key',
                                       sign_request=True)
        domain = Domain(layer1=layer1, data=json.loads(self.domain_status))
        document_service = domain.get_document_service()

        response = {
            'status': 'success',
            'adds': 1,
            'deletes': 0,
        }

        document = {
            "id": "1234",
            "title": "Title 1",
            "category": ["cat_a", "cat_b", "cat_c"]
        }

        self.set_http_response(status_code=200,
                               body=json.dumps(response).encode('utf-8'))
        document_service.domain_connection = self.service_connection
        document_service.add("1234", document)
        resp = document_service.commit()

        headers = self.actual_request.headers

        self.assertIsNotNone(headers.get('Authorization'))

    def test_no_host_provided(self):
        # A host must be provided or a error is thrown.
        with self.assertRaises(ValueError):
            CloudSearchDomainConnection(
                aws_access_key_id='aws_access_key_id',
                aws_secret_access_key='aws_secret_access_key'
            )
