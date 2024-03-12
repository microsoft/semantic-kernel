# Copyright (c) 2010 Chris Moyer http://coredumped.org/
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

import boto
from boto.connection import AWSQueryConnection, AWSAuthConnection
from boto.exception import BotoServerError
import time
import urllib
import xml.sax
from boto.ecs.item import ItemSet
from boto import handler

class ECSConnection(AWSQueryConnection):
    """
    ECommerce Connection

    For more information on how to use this module see:

    http://blog.coredumped.org/2010/09/search-for-books-on-amazon-using-boto.html
    """

    APIVersion = '2010-11-01'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, host='ecs.amazonaws.com',
                 debug=0, https_connection_factory=None, path='/',
                 security_token=None, profile_name=None):
        super(ECSConnection, self).__init__(aws_access_key_id, aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port, proxy_user, proxy_pass,
                                    host, debug, https_connection_factory, path,
                                    security_token=security_token,
                                    profile_name=profile_name)

    def _required_auth_capability(self):
        return ['ecs']

    def get_response(self, action, params, page=0, itemSet=None):
        """
        Utility method to handle calls to ECS and parsing of responses.
        """
        params['Service'] = "AWSECommerceService"
        params['Operation'] = action
        if page:
            params['ItemPage'] = page
        response = self.make_request(None, params, "/onca/xml")
        body = response.read().decode('utf-8')
        boto.log.debug(body)

        if response.status != 200:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise BotoServerError(response.status, response.reason, body)

        if itemSet is None:
            rs = ItemSet(self, action, params, page)
        else:
            rs = itemSet
        h = handler.XmlHandler(rs, self)
        xml.sax.parseString(body.encode('utf-8'), h)
        if not rs.is_valid:
            raise BotoServerError(response.status, '{Code}: {Message}'.format(**rs.errors[0]))
        return rs

    #
    # Group methods
    #

    def item_search(self, search_index, **params):
        """
        Returns items that satisfy the search criteria, including one or more search
        indices.

        For a full list of search terms,
        :see: http://docs.amazonwebservices.com/AWSECommerceService/2010-09-01/DG/index.html?ItemSearch.html
        """
        params['SearchIndex'] = search_index
        return self.get_response('ItemSearch', params)

    def item_lookup(self, **params):
        """
        Returns items that satisfy the lookup query.

        For a full list of parameters, see:
        http://s3.amazonaws.com/awsdocs/Associates/2011-08-01/prod-adv-api-dg-2011-08-01.pdf
        """
        return self.get_response('ItemLookup', params)