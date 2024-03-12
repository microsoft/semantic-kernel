# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved
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

import boto.exception
from boto.compat import json
import requests
import boto
from boto.cloudsearchdomain.layer1 import CloudSearchDomainConnection


class SearchServiceException(Exception):
    pass


class CommitMismatchError(Exception):
    # Let's do some extra work and let the user handle errors on his/her own.

    errors = None


class EncodingError(Exception):
    """
    Content sent for Cloud Search indexing was incorrectly encoded.

    This usually happens when a document is marked as unicode but non-unicode
    characters are present.
    """
    pass


class ContentTooLongError(Exception):
    """
    Content sent for Cloud Search indexing was too long

    This will usually happen when documents queued for indexing add up to more
    than the limit allowed per upload batch (5MB)

    """
    pass


class DocumentServiceConnection(object):
    """
    A CloudSearch document service.

    The DocumentServiceConection is used to add, remove and update documents in
    CloudSearch. Commands are uploaded to CloudSearch in SDF (Search Document
    Format).

    To generate an appropriate SDF, use :func:`add` to add or update documents,
    as well as :func:`delete` to remove documents.

    Once the set of documents is ready to be index, use :func:`commit` to send
    the commands to CloudSearch.

    If there are a lot of documents to index, it may be preferable to split the
    generation of SDF data and the actual uploading into CloudSearch. Retrieve
    the current SDF with :func:`get_sdf`. If this file is the uploaded into S3,
    it can be retrieved back afterwards for upload into CloudSearch using
    :func:`add_sdf_from_s3`.

    The SDF is not cleared after a :func:`commit`. If you wish to continue
    using the DocumentServiceConnection for another batch upload of commands,
    you will need to :func:`clear_sdf` first to stop the previous batch of
    commands from being uploaded again.

    """

    def __init__(self, domain=None, endpoint=None):
        self.domain = domain
        self.endpoint = endpoint
        if not self.endpoint:
            self.endpoint = domain.doc_service_endpoint
        self.documents_batch = []
        self._sdf = None

        # Copy proxy settings from connection and check if request should be signed
        self.proxy = {}
        self.sign_request = False
        if self.domain and self.domain.layer1:
            if self.domain.layer1.use_proxy:
                self.proxy = {'http': self.domain.layer1.get_proxy_url_with_auth()}

            self.sign_request = getattr(self.domain.layer1, 'sign_request', False)

            if self.sign_request:
                # Create a domain connection to send signed requests
                layer1 = self.domain.layer1
                self.domain_connection = CloudSearchDomainConnection(
                    host=self.endpoint,
                    aws_access_key_id=layer1.aws_access_key_id,
                    aws_secret_access_key=layer1.aws_secret_access_key,
                    region=layer1.region,
                    provider=layer1.provider
                )

    def add(self, _id, fields):
        """
        Add a document to be processed by the DocumentService

        The document will not actually be added until :func:`commit` is called

        :type _id: string
        :param _id: A unique ID used to refer to this document.

        :type fields: dict
        :param fields: A dictionary of key-value pairs to be uploaded .
        """

        d = {'type': 'add', 'id': _id, 'fields': fields}
        self.documents_batch.append(d)

    def delete(self, _id):
        """
        Schedule a document to be removed from the CloudSearch service

        The document will not actually be scheduled for removal until
        :func:`commit` is called

        :type _id: string
        :param _id: The unique ID of this document.
        """

        d = {'type': 'delete', 'id': _id}
        self.documents_batch.append(d)

    def get_sdf(self):
        """
        Generate the working set of documents in Search Data Format (SDF)

        :rtype: string
        :returns: JSON-formatted string of the documents in SDF
        """

        return self._sdf if self._sdf else json.dumps(self.documents_batch)

    def clear_sdf(self):
        """
        Clear the working documents from this DocumentServiceConnection

        This should be used after :func:`commit` if the connection will be
        reused for another set of documents.
        """

        self._sdf = None
        self.documents_batch = []

    def add_sdf_from_s3(self, key_obj):
        """
        Load an SDF from S3

        Using this method will result in documents added through
        :func:`add` and :func:`delete` being ignored.

        :type key_obj: :class:`boto.s3.key.Key`
        :param key_obj: An S3 key which contains an SDF
        """
        #@todo:: (lucas) would be nice if this could just take an s3://uri..."

        self._sdf = key_obj.get_contents_as_string()

    def _commit_with_auth(self, sdf, api_version):
        return self.domain_connection.upload_documents(sdf, 'application/json')

    def _commit_without_auth(self, sdf, api_version):
        url = "http://%s/%s/documents/batch" % (self.endpoint, api_version)

        # Keep-alive is automatic in a post-1.0 requests world.
        session = requests.Session()
        session.proxies = self.proxy
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=50,
            max_retries=5
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        resp = session.post(url, data=sdf, headers={'Content-Type': 'application/json'})
        return resp

    def commit(self):
        """
        Actually send an SDF to CloudSearch for processing

        If an SDF file has been explicitly loaded it will be used. Otherwise,
        documents added through :func:`add` and :func:`delete` will be used.

        :rtype: :class:`CommitResponse`
        :returns: A summary of documents added and deleted
        """

        sdf = self.get_sdf()

        if ': null' in sdf:
            boto.log.error('null value in sdf detected. This will probably '
                           'raise 500 error.')
            index = sdf.index(': null')
            boto.log.error(sdf[index - 100:index + 100])

        api_version = '2013-01-01'
        if self.domain and self.domain.layer1:
            api_version = self.domain.layer1.APIVersion

        if self.sign_request:
            r = self._commit_with_auth(sdf, api_version)
        else:
            r = self._commit_without_auth(sdf, api_version)

        return CommitResponse(r, self, sdf, signed_request=self.sign_request)


class CommitResponse(object):
    """Wrapper for response to Cloudsearch document batch commit.

    :type response: :class:`requests.models.Response`
    :param response: Response from Cloudsearch /documents/batch API

    :type doc_service: :class:`boto.cloudsearch2.document.DocumentServiceConnection`
    :param doc_service: Object containing the documents posted and methods to
        retry

    :raises: :class:`boto.exception.BotoServerError`
    :raises: :class:`boto.cloudsearch2.document.SearchServiceException`
    :raises: :class:`boto.cloudsearch2.document.EncodingError`
    :raises: :class:`boto.cloudsearch2.document.ContentTooLongError`
    """
    def __init__(self, response, doc_service, sdf, signed_request=False):
        self.response = response
        self.doc_service = doc_service
        self.sdf = sdf
        self.signed_request = signed_request

        if self.signed_request:
            self.content = response
        else:
            _body = response.content.decode('utf-8')

            try:
                self.content = json.loads(_body)
            except:
                boto.log.error('Error indexing documents.\nResponse Content:\n{0}'
                               '\n\nSDF:\n{1}'.format(_body, self.sdf))
                raise boto.exception.BotoServerError(self.response.status_code, '',
                                                     body=_body)

        self.status = self.content['status']
        if self.status == 'error':
            self.errors = [e.get('message') for e in self.content.get('errors',
                                                                      [])]
            for e in self.errors:
                if "Illegal Unicode character" in e:
                    raise EncodingError("Illegal Unicode character in document")
                elif e == "The Content-Length is too long":
                    raise ContentTooLongError("Content was too long")
        else:
            self.errors = []

        self.adds = self.content['adds']
        self.deletes = self.content['deletes']
        self._check_num_ops('add', self.adds)
        self._check_num_ops('delete', self.deletes)

    def _check_num_ops(self, type_, response_num):
        """Raise exception if number of ops in response doesn't match commit

        :type type_: str
        :param type_: Type of commit operation: 'add' or 'delete'

        :type response_num: int
        :param response_num: Number of adds or deletes in the response.

        :raises: :class:`boto.cloudsearch2.document.CommitMismatchError`
        """
        commit_num = len([d for d in self.doc_service.documents_batch
                          if d['type'] == type_])

        if response_num != commit_num:
            if self.signed_request:
                boto.log.debug(self.response)
            else:
                boto.log.debug(self.response.content)
            # There will always be a commit mismatch error if there is any
            # errors on cloudsearch. self.errors gets lost when this
            # CommitMismatchError is raised. Whoever is using boto has no idea
            # why their commit failed. They can't even notify the user of the
            # cause by parsing the error messages from amazon. So let's
            # attach the self.errors to the exceptions if we already spent
            # time and effort collecting them out of the response.
            exc = CommitMismatchError(
                'Incorrect number of {0}s returned. Commit: {1} Response: {2}'
                .format(type_, commit_num, response_num)
            )
            exc.errors = self.errors
            raise exc
