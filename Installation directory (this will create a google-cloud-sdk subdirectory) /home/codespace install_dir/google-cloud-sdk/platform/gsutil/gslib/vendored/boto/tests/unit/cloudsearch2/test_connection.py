#!/usr/bin env python

from tests.unit import AWSMockServiceTestCase

from boto.cloudsearch2.domain import Domain
from boto.cloudsearch2.layer1 import CloudSearchConnection


class TestCloudSearchCreateDomain(AWSMockServiceTestCase):
    connection_class = CloudSearchConnection

    def default_body(self):
        return b"""
{
  "CreateDomainResponse": {
    "CreateDomainResult": {
      "DomainStatus": {
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
      }
    },
    "ResponseMetadata": {
      "RequestId": "00000000-0000-0000-0000-000000000000"
    }
  }
}
"""

    def test_create_domain(self):
        self.set_http_response(status_code=200)
        self.service_connection.create_domain('demo')

        self.assert_request_parameters({
            'Action': 'CreateDomain',
            'ContentType': 'JSON',
            'DomainName': 'demo',
            'Version': '2013-01-01',
        })

    def test_cloudsearch_connect_result_endpoints(self):
        """Check that endpoints & ARNs are correctly returned from AWS"""

        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response['CreateDomainResponse']
                                          ['CreateDomainResult']
                                          ['DomainStatus'])

        self.assertEqual(
            domain.doc_service_endpoint,
            "doc-demo.us-east-1.cloudsearch.amazonaws.com")
        self.assertEqual(domain.service_arn,
                         "arn:aws:cs:us-east-1:1234567890:domain/demo")
        self.assertEqual(
            domain.search_service_endpoint,
            "search-demo.us-east-1.cloudsearch.amazonaws.com")

    def test_cloudsearch_connect_result_statuses(self):
        """Check that domain statuses are correctly returned from AWS"""
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response['CreateDomainResponse']
                                          ['CreateDomainResult']
                                          ['DomainStatus'])

        self.assertEqual(domain.created, True)
        self.assertEqual(domain.processing, False)
        self.assertEqual(domain.requires_index_documents, False)
        self.assertEqual(domain.deleted, False)

    def test_cloudsearch_connect_result_details(self):
        """Check that the domain information is correctly returned from AWS"""
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response['CreateDomainResponse']
                                          ['CreateDomainResult']
                                          ['DomainStatus'])

        self.assertEqual(domain.id, "1234567890/demo")
        self.assertEqual(domain.name, "demo")

    def test_cloudsearch_documentservice_creation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response['CreateDomainResponse']
                                          ['CreateDomainResult']
                                          ['DomainStatus'])

        document = domain.get_document_service()

        self.assertEqual(
            document.endpoint,
            "doc-demo.us-east-1.cloudsearch.amazonaws.com")

    def test_cloudsearch_searchservice_creation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response['CreateDomainResponse']
                                          ['CreateDomainResult']
                                          ['DomainStatus'])

        search = domain.get_search_service()

        self.assertEqual(
            search.endpoint,
            "search-demo.us-east-1.cloudsearch.amazonaws.com")


class CloudSearchConnectionDeletionTest(AWSMockServiceTestCase):
    connection_class = CloudSearchConnection

    def default_body(self):
        return b"""
{
  "DeleteDomainResponse": {
    "DeleteDomainResult": {
      "DomainStatus": {
        "SearchInstanceType": null,
        "DomainId": "1234567890/demo",
        "DomainName": "test",
        "Deleted": true,
        "SearchInstanceCount": 0,
        "Created": true,
        "SearchService": {
          "Endpoint": null
        },
        "RequiresIndexDocuments": false,
        "Processing": false,
        "DocService": {
          "Endpoint": null
        },
        "ARN": "arn:aws:cs:us-east-1:1234567890:domain/demo",
        "SearchPartitionCount": 0
      }
    },
    "ResponseMetadata": {
      "RequestId": "00000000-0000-0000-0000-000000000000"
    }
  }
}
"""

    def test_cloudsearch_deletion(self):
        """
        Check that the correct arguments are sent to AWS when creating a
        cloudsearch connection.
        """
        self.set_http_response(status_code=200)
        self.service_connection.delete_domain('demo')

        self.assert_request_parameters({
            'Action': 'DeleteDomain',
            'ContentType': 'JSON',
            'DomainName': 'demo',
            'Version': '2013-01-01',
        })


class CloudSearchConnectionIndexDocumentTest(AWSMockServiceTestCase):
    connection_class = CloudSearchConnection

    def default_body(self):
        return b"""
{
  "IndexDocumentsResponse": {
    "IndexDocumentsResult": {
      "FieldNames": [
          "average_score",
          "brand_id",
          "colors",
          "context",
          "context_owner",
          "created_at",
          "creator_id",
          "description",
          "file_size",
          "format",
          "has_logo",
          "has_messaging",
          "height",
          "image_id",
          "ingested_from",
          "is_advertising",
          "is_photo",
          "is_reviewed",
          "modified_at",
          "subject_date",
          "tags",
          "title",
          "width"
      ]
    },
    "ResponseMetadata": {
      "RequestId": "42e618d9-c4d9-11e3-8242-c32da3041159"
    }
  }
}
"""

    def test_cloudsearch_index_documents(self):
        """
        Check that the correct arguments are sent to AWS when indexing a
        domain.
        """
        self.set_http_response(status_code=200)
        self.service_connection.index_documents('demo')

        self.assert_request_parameters({
            'Action': 'IndexDocuments',
            'ContentType': 'JSON',
            'DomainName': 'demo',
            'Version': '2013-01-01',
        })

    def test_cloudsearch_index_documents_resp(self):
        """
        Check that the AWS response is being parsed correctly when indexing a
        domain.
        """
        self.set_http_response(status_code=200)
        api_response = self.service_connection.index_documents('demo')

        fields = (api_response['IndexDocumentsResponse']
                              ['IndexDocumentsResult']
                              ['FieldNames'])

        self.assertEqual(fields, ['average_score', 'brand_id', 'colors',
                                  'context', 'context_owner',
                                  'created_at', 'creator_id',
                                  'description', 'file_size', 'format',
                                  'has_logo', 'has_messaging', 'height',
                                  'image_id', 'ingested_from',
                                  'is_advertising', 'is_photo',
                                  'is_reviewed', 'modified_at',
                                  'subject_date', 'tags', 'title',
                                  'width'])
