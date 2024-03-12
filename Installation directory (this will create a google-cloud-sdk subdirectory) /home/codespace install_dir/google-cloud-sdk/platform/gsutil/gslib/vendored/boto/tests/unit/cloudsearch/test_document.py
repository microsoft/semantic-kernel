#!/usr/bin env python

from tests.unit import unittest
from httpretty import HTTPretty
from mock import MagicMock

import json

from boto.cloudsearch.document import DocumentServiceConnection
from boto.cloudsearch.document import CommitMismatchError, EncodingError, \
        ContentTooLongError, DocumentServiceConnection, SearchServiceException

import boto

class CloudSearchDocumentTest(unittest.TestCase):
    def setUp(self):
        HTTPretty.enable()
        HTTPretty.register_uri(
            HTTPretty.POST,
            ("http://doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com/"
             "2011-02-01/documents/batch"),
            body=json.dumps(self.response).encode('utf-8'),
            content_type="application/json")

    def tearDown(self):
        HTTPretty.disable()

class CloudSearchDocumentSingleTest(CloudSearchDocumentTest):

    response = {
        'status': 'success',
        'adds': 1,
        'deletes': 0,
    }

    def test_cloudsearch_add_basics(self):
        """
        Check that a simple add document actually sends an add document request
        to AWS.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})
        document.commit()

        args = json.loads(HTTPretty.last_request.body.decode('utf-8'))[0]

        self.assertEqual(args['lang'], 'en')
        self.assertEqual(args['type'], 'add')

    def test_cloudsearch_add_single_basic(self):
        """
        Check that a simple add document sends correct document metadata to
        AWS.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})
        document.commit()

        args = json.loads(HTTPretty.last_request.body.decode('utf-8'))[0]

        self.assertEqual(args['id'], '1234')
        self.assertEqual(args['version'], 10)
        self.assertEqual(args['type'], 'add')

    def test_cloudsearch_add_single_fields(self):
        """
        Check that a simple add document sends the actual document to AWS.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})
        document.commit()

        args = json.loads(HTTPretty.last_request.body.decode('utf-8'))[0]

        self.assertEqual(args['fields']['category'], ['cat_a', 'cat_b',
                                                      'cat_c'])
        self.assertEqual(args['fields']['id'], '1234')
        self.assertEqual(args['fields']['title'], 'Title 1')

    def test_cloudsearch_add_single_result(self):
        """
        Check that the reply from adding a single document is correctly parsed.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})
        doc = document.commit()

        self.assertEqual(doc.status, 'success')
        self.assertEqual(doc.adds, 1)
        self.assertEqual(doc.deletes, 0)

        self.assertEqual(doc.doc_service, document)


class CloudSearchDocumentMultipleAddTest(CloudSearchDocumentTest):

    response = {
        'status': 'success',
        'adds': 3,
        'deletes': 0,
    }

    objs = {
        '1234': {
            'version': 10, 'fields': {"id": "1234", "title": "Title 1",
                                      "category": ["cat_a", "cat_b",
                                                   "cat_c"]}},
        '1235': {
            'version': 11, 'fields': {"id": "1235", "title": "Title 2",
                                      "category": ["cat_b", "cat_c",
                                                   "cat_d"]}},
        '1236': {
            'version': 12, 'fields': {"id": "1236", "title": "Title 3",
                                      "category": ["cat_e", "cat_f",
                                                   "cat_g"]}},
        }


    def test_cloudsearch_add_basics(self):
        """Check that multiple documents are added correctly to AWS"""
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        for (key, obj) in self.objs.items():
            document.add(key, obj['version'], obj['fields'])
        document.commit()

        args = json.loads(HTTPretty.last_request.body.decode('utf-8'))

        for arg in args:
            self.assertTrue(arg['id'] in self.objs)
            self.assertEqual(arg['version'], self.objs[arg['id']]['version'])
            self.assertEqual(arg['fields']['id'],
                             self.objs[arg['id']]['fields']['id'])
            self.assertEqual(arg['fields']['title'],
                             self.objs[arg['id']]['fields']['title'])
            self.assertEqual(arg['fields']['category'],
                             self.objs[arg['id']]['fields']['category'])

    def test_cloudsearch_add_results(self):
        """
        Check that the result from adding multiple documents is parsed
        correctly.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        for (key, obj) in self.objs.items():
            document.add(key, obj['version'], obj['fields'])
        doc = document.commit()

        self.assertEqual(doc.status, 'success')
        self.assertEqual(doc.adds, len(self.objs))
        self.assertEqual(doc.deletes, 0)


class CloudSearchDocumentDelete(CloudSearchDocumentTest):

    response = {
        'status': 'success',
        'adds': 0,
        'deletes': 1,
    }

    def test_cloudsearch_delete(self):
        """
        Test that the request for a single document deletion is done properly.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.delete("5", "10")
        document.commit()
        args = json.loads(HTTPretty.last_request.body.decode('utf-8'))[0]

        self.assertEqual(args['version'], '10')
        self.assertEqual(args['type'], 'delete')
        self.assertEqual(args['id'], '5')

    def test_cloudsearch_delete_results(self):
        """
        Check that the result of a single document deletion is parsed properly.
        """
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.delete("5", "10")
        doc = document.commit()

        self.assertEqual(doc.status, 'success')
        self.assertEqual(doc.adds, 0)
        self.assertEqual(doc.deletes, 1)


class CloudSearchDocumentDeleteMultiple(CloudSearchDocumentTest):
    response = {
        'status': 'success',
        'adds': 0,
        'deletes': 2,
    }

    def test_cloudsearch_delete_multiples(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.delete("5", "10")
        document.delete("6", "11")
        document.commit()
        args = json.loads(HTTPretty.last_request.body.decode('utf-8'))

        self.assertEqual(len(args), 2)
        for arg in args:
            self.assertEqual(arg['type'], 'delete')

            if arg['id'] == '5':
                self.assertEqual(arg['version'], '10')
            elif arg['id'] == '6':
                self.assertEqual(arg['version'], '11')
            else: # Unknown result out of AWS that shouldn't be there
                self.assertTrue(False)


class CloudSearchSDFManipulation(CloudSearchDocumentTest):
    response = {
        'status': 'success',
        'adds': 1,
        'deletes': 0,
    }


    def test_cloudsearch_initial_sdf_is_blank(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")

        self.assertEqual(document.get_sdf(), '[]')

    def test_cloudsearch_single_document_sdf(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")

        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})

        self.assertNotEqual(document.get_sdf(), '[]')

        document.clear_sdf()

        self.assertEqual(document.get_sdf(), '[]')

class CloudSearchBadSDFTesting(CloudSearchDocumentTest):
    response = {
        'status': 'success',
        'adds': 1,
        'deletes': 0,
    }

    def test_cloudsearch_erroneous_sdf(self):
        original = boto.log.error
        boto.log.error = MagicMock()
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")

        document.add("1234", 10, {"id": "1234", "title": None,
                                  "category": ["cat_a", "cat_b", "cat_c"]})

        document.commit()
        self.assertNotEqual(len(boto.log.error.call_args_list), 1)

        boto.log.error = original


class CloudSearchDocumentErrorBadUnicode(CloudSearchDocumentTest):
    response = {
        'status': 'error',
        'adds': 0,
        'deletes': 0,
        'errors': [{'message': 'Illegal Unicode character in document'}]
    }

    def test_fake_bad_unicode(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})
        self.assertRaises(EncodingError, document.commit)


class CloudSearchDocumentErrorDocsTooBig(CloudSearchDocumentTest):
    response = {
        'status': 'error',
        'adds': 0,
        'deletes': 0,
        'errors': [{'message': 'The Content-Length is too long'}]
    }

    def test_fake_docs_too_big(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})

        self.assertRaises(ContentTooLongError, document.commit)


class CloudSearchDocumentErrorMismatch(CloudSearchDocumentTest):
    response = {
            'status': 'error',
            'adds': 0,
            'deletes': 0,
            'errors': [{'message': 'Something went wrong'}]
            }

    def test_fake_failure(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")

        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})

        self.assertRaises(CommitMismatchError, document.commit)

class CloudSearchDocumentsErrorMissingAdds(CloudSearchDocumentTest):
    response = {
        'status': 'error',
        'deletes': 0,
        'errors': [{'message': 'Unknown error message'}]
        }

    def test_fake_failure(self):
        document = DocumentServiceConnection(
            endpoint="doc-demo-userdomain.us-east-1.cloudsearch.amazonaws.com")
        document.add("1234", 10, {"id": "1234", "title": "Title 1",
                                  "category": ["cat_a", "cat_b", "cat_c"]})
        self.assertRaises(SearchServiceException, document.commit)
