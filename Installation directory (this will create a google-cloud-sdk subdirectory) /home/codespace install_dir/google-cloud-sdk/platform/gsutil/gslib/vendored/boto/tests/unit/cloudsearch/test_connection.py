#!/usr/bin env python

from tests.unit import AWSMockServiceTestCase

from boto.cloudsearch.domain import Domain
from boto.cloudsearch.layer1 import Layer1

class TestCloudSearchCreateDomain(AWSMockServiceTestCase):
    connection_class = Layer1

    def default_body(self):
        return b"""
<CreateDomainResponse xmlns="http://cloudsearch.amazonaws.com/doc/2011-02-01">
  <CreateDomainResult>
    <DomainStatus>
      <SearchPartitionCount>0</SearchPartitionCount>
      <SearchService>
        <Arn>arn:aws:cs:us-east-1:1234567890:search/demo</Arn>
        <Endpoint>search-demo-userdomain.us-east-1.cloudsearch.amazonaws.com</Endpoint>
      </SearchService>
      <NumSearchableDocs>0</NumSearchableDocs>
      <Created>true</Created>
      <DomainId>1234567890/demo</DomainId>
      <Processing>false</Processing>
      <SearchInstanceCount>0</SearchInstanceCount>
      <DomainName>demo</DomainName>
      <RequiresIndexDocuments>false</RequiresIndexDocuments>
      <Deleted>false</Deleted>
      <DocService>
        <Arn>arn:aws:cs:us-east-1:1234567890:doc/demo</Arn>
        <Endpoint>doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com</Endpoint>
      </DocService>
    </DomainStatus>
  </CreateDomainResult>
  <ResponseMetadata>
    <RequestId>00000000-0000-0000-0000-000000000000</RequestId>
  </ResponseMetadata>
</CreateDomainResponse>
"""

    def test_create_domain(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')

        self.assert_request_parameters({
            'Action': 'CreateDomain',
            'DomainName': 'demo',
            'Version': '2011-02-01',
        })

    def test_cloudsearch_connect_result_endpoints(self):
        """Check that endpoints & ARNs are correctly returned from AWS"""

        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response)

        self.assertEqual(domain.doc_service_arn,
                         "arn:aws:cs:us-east-1:1234567890:doc/demo")
        self.assertEqual(
            domain.doc_service_endpoint,
            "doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        self.assertEqual(domain.search_service_arn,
                         "arn:aws:cs:us-east-1:1234567890:search/demo")
        self.assertEqual(
            domain.search_service_endpoint,
            "search-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")

    def test_cloudsearch_connect_result_statuses(self):
        """Check that domain statuses are correctly returned from AWS"""
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response)

        self.assertEqual(domain.created, True)
        self.assertEqual(domain.processing, False)
        self.assertEqual(domain.requires_index_documents, False)
        self.assertEqual(domain.deleted, False)

    def test_cloudsearch_connect_result_details(self):
        """Check that the domain information is correctly returned from AWS"""
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response)

        self.assertEqual(domain.id, "1234567890/demo")
        self.assertEqual(domain.name, "demo")

    def test_cloudsearch_documentservice_creation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response)

        document = domain.get_document_service()

        self.assertEqual(
            document.endpoint,
            "doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")

    def test_cloudsearch_searchservice_creation(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.create_domain('demo')
        domain = Domain(self, api_response)

        search = domain.get_search_service()

        self.assertEqual(
            search.endpoint,
            "search-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")


class CloudSearchConnectionDeletionTest(AWSMockServiceTestCase):
    connection_class = Layer1

    def default_body(self):
        return b"""
<DeleteDomainResponse xmlns="http://cloudsearch.amazonaws.com/doc/2011-02-01">
  <DeleteDomainResult>
    <DomainStatus>
      <SearchPartitionCount>0</SearchPartitionCount>
      <SearchService>
        <Arn>arn:aws:cs:us-east-1:1234567890:search/demo</Arn>
        <Endpoint>search-demo-userdomain.us-east-1.cloudsearch.amazonaws.com</Endpoint>
      </SearchService>
      <NumSearchableDocs>0</NumSearchableDocs>
      <Created>true</Created>
      <DomainId>1234567890/demo</DomainId>
      <Processing>false</Processing>
      <SearchInstanceCount>0</SearchInstanceCount>
      <DomainName>demo</DomainName>
      <RequiresIndexDocuments>false</RequiresIndexDocuments>
      <Deleted>false</Deleted>
      <DocService>
        <Arn>arn:aws:cs:us-east-1:1234567890:doc/demo</Arn>
        <Endpoint>doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com</Endpoint>
      </DocService>
    </DomainStatus>
  </DeleteDomainResult>
  <ResponseMetadata>
    <RequestId>00000000-0000-0000-0000-000000000000</RequestId>
  </ResponseMetadata>
</DeleteDomainResponse>
"""

    def test_cloudsearch_deletion(self):
        """
        Check that the correct arguments are sent to AWS when creating a
        cloudsearch connection.
        """
        self.set_http_response(status_code=200)
        api_response = self.service_connection.delete_domain('demo')

        self.assert_request_parameters({
            'Action': 'DeleteDomain',
            'DomainName': 'demo',
            'Version': '2011-02-01',
        })


class CloudSearchConnectionIndexDocumentTest(AWSMockServiceTestCase):
    connection_class = Layer1

    def default_body(self):
        return b"""
<IndexDocumentsResponse xmlns="http://cloudsearch.amazonaws.com/doc/2011-02-01">
  <IndexDocumentsResult>
    <FieldNames>
      <member>average_score</member>
      <member>brand_id</member>
      <member>colors</member>
      <member>context</member>
      <member>context_owner</member>
      <member>created_at</member>
      <member>creator_id</member>
      <member>description</member>
      <member>file_size</member>
      <member>format</member>
      <member>has_logo</member>
      <member>has_messaging</member>
      <member>height</member>
      <member>image_id</member>
      <member>ingested_from</member>
      <member>is_advertising</member>
      <member>is_photo</member>
      <member>is_reviewed</member>
      <member>modified_at</member>
      <member>subject_date</member>
      <member>tags</member>
      <member>title</member>
      <member>width</member>
    </FieldNames>
  </IndexDocumentsResult>
  <ResponseMetadata>
    <RequestId>eb2b2390-6bbd-11e2-ab66-93f3a90dcf2a</RequestId>
  </ResponseMetadata>
</IndexDocumentsResponse>
"""

    def test_cloudsearch_index_documents(self):
        """
        Check that the correct arguments are sent to AWS when indexing a
        domain.
        """
        self.set_http_response(status_code=200)
        api_response = self.service_connection.index_documents('demo')

        self.assert_request_parameters({
            'Action': 'IndexDocuments',
            'DomainName': 'demo',
            'Version': '2011-02-01',
        })

    def test_cloudsearch_index_documents_resp(self):
        """
        Check that the AWS response is being parsed correctly when indexing a
        domain.
        """
        self.set_http_response(status_code=200)
        api_response = self.service_connection.index_documents('demo')

        self.assertEqual(api_response, ['average_score', 'brand_id', 'colors',
                                        'context', 'context_owner',
                                        'created_at', 'creator_id',
                                        'description', 'file_size', 'format',
                                        'has_logo', 'has_messaging', 'height',
                                        'image_id', 'ingested_from',
                                        'is_advertising', 'is_photo',
                                        'is_reviewed', 'modified_at',
                                        'subject_date', 'tags', 'title',
                                        'width'])
