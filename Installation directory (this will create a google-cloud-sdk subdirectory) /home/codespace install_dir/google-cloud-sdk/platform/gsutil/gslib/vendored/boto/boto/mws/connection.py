# Copyright (c) 2012-2014 Andy Davidoff http://www.disruptek.com/
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
from collections import abc
import xml.sax
import hashlib
import string
from boto.connection import AWSQueryConnection
from boto.exception import BotoServerError
import boto.mws.exception
import boto.mws.response
from boto.handler import XmlHandler
from boto.compat import filter, map, six, encodebytes

__all__ = ['MWSConnection']

api_version_path = {
    'Feeds':             ('2009-01-01', 'Merchant', '/'),
    'Reports':           ('2009-01-01', 'Merchant', '/'),
    'Orders':            ('2013-09-01', 'SellerId', '/Orders/2013-09-01'),
    'Products':          ('2011-10-01', 'SellerId', '/Products/2011-10-01'),
    'Sellers':           ('2011-07-01', 'SellerId', '/Sellers/2011-07-01'),
    'Inbound':           ('2010-10-01', 'SellerId',
                          '/FulfillmentInboundShipment/2010-10-01'),
    'Outbound':          ('2010-10-01', 'SellerId',
                          '/FulfillmentOutboundShipment/2010-10-01'),
    'Inventory':         ('2010-10-01', 'SellerId',
                          '/FulfillmentInventory/2010-10-01'),
    'Recommendations':   ('2013-04-01', 'SellerId',
                          '/Recommendations/2013-04-01'),
    'CustomerInfo':      ('2014-03-01', 'SellerId',
                          '/CustomerInformation/2014-03-01'),
    'CartInfo':          ('2014-03-01', 'SellerId',
                          '/CartInformation/2014-03-01'),
    'Subscriptions':     ('2013-07-01', 'SellerId',
                          '/Subscriptions/2013-07-01'),
    'OffAmazonPayments': ('2013-01-01', 'SellerId',
                          '/OffAmazonPayments/2013-01-01'),
}
content_md5 = lambda c: encodebytes(hashlib.md5(c).digest()).strip()
decorated_attrs = ('action', 'response', 'section',
                   'quota', 'restore', 'version')
api_call_map = {}


def add_attrs_from(func, to):
    for attr in decorated_attrs:
        setattr(to, attr, getattr(func, attr, None))
    to.__wrapped__ = func
    return to


def structured_lists(*fields):

    def decorator(func):

        def wrapper(self, *args, **kw):
            for key, acc in [f.split('.') for f in fields]:
                if key in kw:
                    newkey = key + '.' + acc + (acc and '.' or '')
                    for i in range(len(kw[key])):
                        kw[newkey + str(i + 1)] = kw[key][i]
                    kw.pop(key)
            return func(self, *args, **kw)
        wrapper.__doc__ = "{0}\nLists: {1}".format(func.__doc__,
                                                   ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def http_body(field):

    def decorator(func):

        def wrapper(*args, **kw):
            if any([f not in kw for f in (field, 'content_type')]):
                message = "{0} requires {1} and content_type arguments for " \
                          "building HTTP body".format(func.action, field)
                raise KeyError(message)
            kw['body'] = kw.pop(field)
            kw['headers'] = {
                'Content-Type': kw.pop('content_type'),
                'Content-MD5':  content_md5(kw['body']),
            }
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nRequired HTTP Body: " \
                          "{1}".format(func.__doc__, field)
        return add_attrs_from(func, to=wrapper)
    return decorator


def destructure_object(value, into, prefix, members=False):
    if isinstance(value, boto.mws.response.ResponseElement):
        destructure_object(value.__dict__, into, prefix, members=members)
    elif isinstance(value, abc.Mapping):
        for name in value:
            if name.startswith('_'):
                continue
            destructure_object(value[name], into, prefix + '.' + name,
                               members=members)
    elif isinstance(value, six.string_types):
        into[prefix] = value
    elif isinstance(value, abc.Iterable):
        for index, element in enumerate(value):
            suffix = (members and '.member.' or '.') + str(index + 1)
            destructure_object(element, into, prefix + suffix,
                               members=members)
    elif isinstance(value, bool):
        into[prefix] = str(value).lower()
    else:
        into[prefix] = value


def structured_objects(*fields, **kwargs):

    def decorator(func):

        def wrapper(*args, **kw):
            members = kwargs.get('members', False)
            for field in filter(lambda i: i in kw, fields):
                destructure_object(kw.pop(field), kw, field, members=members)
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nElement|Iter|Map: {1}\n" \
                          "(ResponseElement or anything iterable/dict-like)" \
                          .format(func.__doc__, ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def requires(*groups):

    def decorator(func):

        def requires(*args, **kw):
            hasgroup = lambda group: all(key in kw for key in group)
            if 1 != len(list(filter(hasgroup, groups))):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} requires {1} argument(s)" \
                          "".format(func.action, message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        requires.__doc__ = "{0}\nRequired: {1}".format(func.__doc__,
                                                       message)
        return add_attrs_from(func, to=requires)
    return decorator


def exclusive(*groups):

    def decorator(func):

        def wrapper(*args, **kw):
            hasgroup = lambda group: all(key in kw for key in group)
            if len(list(filter(hasgroup, groups))) not in (0, 1):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} requires either {1}" \
                          "".format(func.action, message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        wrapper.__doc__ = "{0}\nEither: {1}".format(func.__doc__,
                                                    message)
        return add_attrs_from(func, to=wrapper)
    return decorator


def dependent(field, *groups):

    def decorator(func):

        def wrapper(*args, **kw):
            hasgroup = lambda group: all(key in kw for key in group)
            if field in kw and not any(hasgroup(g) for g in groups):
                message = ' OR '.join(['+'.join(g) for g in groups])
                message = "{0} argument {1} requires {2}" \
                          "".format(func.action, field, message)
                raise KeyError(message)
            return func(*args, **kw)
        message = ' OR '.join(['+'.join(g) for g in groups])
        wrapper.__doc__ = "{0}\n{1} requires: {2}".format(func.__doc__,
                                                          field,
                                                          message)
        return add_attrs_from(func, to=wrapper)
    return decorator


def requires_some_of(*fields):

    def decorator(func):

        def requires(*args, **kw):
            if not any(i in kw for i in fields):
                message = "{0} requires at least one of {1} argument(s)" \
                          "".format(func.action, ', '.join(fields))
                raise KeyError(message)
            return func(*args, **kw)
        requires.__doc__ = "{0}\nSome Required: {1}".format(func.__doc__,
                                                            ', '.join(fields))
        return add_attrs_from(func, to=requires)
    return decorator


def boolean_arguments(*fields):

    def decorator(func):

        def wrapper(*args, **kw):
            for field in [f for f in fields if isinstance(kw.get(f), bool)]:
                kw[field] = str(kw[field]).lower()
            return func(*args, **kw)
        wrapper.__doc__ = "{0}\nBooleans: {1}".format(func.__doc__,
                                                      ', '.join(fields))
        return add_attrs_from(func, to=wrapper)
    return decorator


def api_action(section, quota, restore, *api):

    def decorator(func, quota=int(quota), restore=float(restore)):
        version, accesskey, path = api_version_path[section]
        action = ''.join(api or map(str.capitalize, func.__name__.split('_')))

        def wrapper(self, *args, **kw):
            kw.setdefault(accesskey, getattr(self, accesskey, None))
            if kw[accesskey] is None:
                message = "{0} requires {1} argument. Set the " \
                          "MWSConnection.{2} attribute?" \
                          "".format(action, accesskey, accesskey)
                raise KeyError(message)
            kw['Action'] = action
            kw['Version'] = version
            response = self._response_factory(action, connection=self)
            request = dict(path=path, quota=quota, restore=restore)
            return func(self, request, response, *args, **kw)
        for attr in decorated_attrs:
            setattr(wrapper, attr, locals().get(attr))
        wrapper.__doc__ = "MWS {0}/{1} API call; quota={2} restore={3:.2f}\n" \
                          "{4}".format(action, version, quota, restore,
                                       func.__doc__)
        api_call_map[action] = func.__name__
        return wrapper
    return decorator


class MWSConnection(AWSQueryConnection):

    ResponseFactory = boto.mws.response.ResponseFactory
    ResponseErrorFactory = boto.mws.exception.ResponseErrorFactory

    def __init__(self, *args, **kw):
        kw.setdefault('host', 'mws.amazonservices.com')
        self._sandboxed = kw.pop('sandbox', False)
        self.Merchant = kw.pop('Merchant', None) or kw.get('SellerId')
        self.SellerId = kw.pop('SellerId', None) or self.Merchant
        kw = self._setup_factories(kw.pop('factory_scopes', []), **kw)
        super(MWSConnection, self).__init__(*args, **kw)

    def _setup_factories(self, extrascopes, **kw):
        for factory, (scope, Default) in {
            'response_factory':
                (boto.mws.response, self.ResponseFactory),
            'response_error_factory':
                (boto.mws.exception, self.ResponseErrorFactory),
        }.items():
            if factory in kw:
                setattr(self, '_' + factory, kw.pop(factory))
            else:
                scopes = extrascopes + [scope]
                setattr(self, '_' + factory, Default(scopes=scopes))
        return kw

    def _sandboxify(self, path):
        if not self._sandboxed:
            return path
        splat = path.split('/')
        splat[-2] += '_Sandbox'
        return '/'.join(splat)

    def _required_auth_capability(self):
        return ['mws']

    def _post_request(self, request, params, parser, body='', headers=None):
        """Make a POST request, optionally with a content body,
           and return the response, optionally as raw text.
        """
        headers = headers or {}
        path = self._sandboxify(request['path'])
        request = self.build_base_http_request('POST', path, None, data=body,
                                               params=params, headers=headers,
                                               host=self.host)
        try:
            response = self._mexe(request, override_num_retries=None)
        except BotoServerError as bs:
            raise self._response_error_factory(bs.status, bs.reason, bs.body)
        body = response.read()
        boto.log.debug(body)
        if not body:
            boto.log.error('Null body %s' % body)
            raise self._response_error_factory(response.status,
                                               response.reason, body)
        if response.status != 200:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self._response_error_factory(response.status,
                                               response.reason, body)
        digest = response.getheader('Content-MD5')
        if digest is not None:
            assert content_md5(body) == digest
        contenttype = response.getheader('Content-Type')
        return self._parse_response(parser, contenttype, body)

    def _parse_response(self, parser, contenttype, body):
        if not contenttype.startswith('text/xml'):
            return body
        handler = XmlHandler(parser, self)
        xml.sax.parseString(body, handler)
        return parser

    def method_for(self, name):
        """Return the MWS API method referred to in the argument.
           The named method can be in CamelCase or underlined_lower_case.
           This is the complement to MWSConnection.any_call.action
        """
        action = '_' in name and string.capwords(name, '_') or name
        if action in api_call_map:
            return getattr(self, api_call_map[action])
        return None

    def iter_call(self, call, *args, **kw):
        """Pass a call name as the first argument and a generator
           is returned for the initial response and any continuation
           call responses made using the NextToken.
        """
        method = self.method_for(call)
        assert method, 'No call named "{0}"'.format(call)
        return self.iter_response(method(*args, **kw))

    def iter_response(self, response):
        """Pass a call's response as the initial argument and a
           generator is returned for the initial response and any
           continuation call responses made using the NextToken.
        """
        yield response
        more = self.method_for(response._action + 'ByNextToken')
        while more and response._result.HasNext == 'true':
            response = more(NextToken=response._result.NextToken)
            yield response

    @requires(['FeedType'])
    @boolean_arguments('PurgeAndReplace')
    @http_body('FeedContent')
    @structured_lists('MarketplaceIdList.Id')
    @api_action('Feeds', 15, 120)
    def submit_feed(self, request, response, headers=None, body='', **kw):
        """Uploads a feed for processing by Amazon MWS.
        """
        headers = headers or {}
        return self._post_request(request, kw, response, body=body,
                                  headers=headers)

    @structured_lists('FeedSubmissionIdList.Id', 'FeedTypeList.Type',
                      'FeedProcessingStatusList.Status')
    @api_action('Feeds', 10, 45)
    def get_feed_submission_list(self, request, response, **kw):
        """Returns a list of all feed submissions submitted in the
           previous 90 days.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Feeds', 0, 0)
    def get_feed_submission_list_by_next_token(self, request, response, **kw):
        """Returns a list of feed submissions using the NextToken parameter.
        """
        return self._post_request(request, kw, response)

    @structured_lists('FeedTypeList.Type', 'FeedProcessingStatusList.Status')
    @api_action('Feeds', 10, 45)
    def get_feed_submission_count(self, request, response, **kw):
        """Returns a count of the feeds submitted in the previous 90 days.
        """
        return self._post_request(request, kw, response)

    @structured_lists('FeedSubmissionIdList.Id', 'FeedTypeList.Type')
    @api_action('Feeds', 10, 45)
    def cancel_feed_submissions(self, request, response, **kw):
        """Cancels one or more feed submissions and returns a
           count of the feed submissions that were canceled.
        """
        return self._post_request(request, kw, response)

    @requires(['FeedSubmissionId'])
    @api_action('Feeds', 15, 60)
    def get_feed_submission_result(self, request, response, **kw):
        """Returns the feed processing report.
        """
        return self._post_request(request, kw, response)

    def get_service_status(self, **kw):
        """Instruct the user on how to get service status.
        """
        sections = ', '.join(map(str.lower, api_version_path.keys()))
        message = "Use {0}.get_(section)_service_status(), " \
                  "where (section) is one of the following: " \
                  "{1}".format(self.__class__.__name__, sections)
        raise AttributeError(message)

    @requires(['ReportType'])
    @structured_lists('MarketplaceIdList.Id')
    @boolean_arguments('ReportOptions=ShowSalesChannel')
    @api_action('Reports', 15, 60)
    def request_report(self, request, response, **kw):
        """Creates a report request and submits the request to Amazon MWS.
        """
        return self._post_request(request, kw, response)

    @structured_lists('ReportRequestIdList.Id', 'ReportTypeList.Type',
                      'ReportProcessingStatusList.Status')
    @api_action('Reports', 10, 45)
    def get_report_request_list(self, request, response, **kw):
        """Returns a list of report requests that you can use to get the
           ReportRequestId for a report.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Reports', 0, 0)
    def get_report_request_list_by_next_token(self, request, response, **kw):
        """Returns a list of report requests using the NextToken,
           which was supplied by a previous request to either
           GetReportRequestListByNextToken or GetReportRequestList, where
           the value of HasNext was true in that previous request.
        """
        return self._post_request(request, kw, response)

    @structured_lists('ReportTypeList.Type',
                      'ReportProcessingStatusList.Status')
    @api_action('Reports', 10, 45)
    def get_report_request_count(self, request, response, **kw):
        """Returns a count of report requests that have been submitted
           to Amazon MWS for processing.
        """
        return self._post_request(request, kw, response)

    @api_action('Reports', 10, 45)
    def cancel_report_requests(self, request, response, **kw):
        """Cancel one or more report requests, returning the count of the
           canceled report requests and the report request information.
        """
        return self._post_request(request, kw, response)

    @boolean_arguments('Acknowledged')
    @structured_lists('ReportRequestIdList.Id', 'ReportTypeList.Type')
    @api_action('Reports', 10, 60)
    def get_report_list(self, request, response, **kw):
        """Returns a list of reports that were created in the previous
           90 days that match the query parameters.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Reports', 0, 0)
    def get_report_list_by_next_token(self, request, response, **kw):
        """Returns a list of reports using the NextToken, which
           was supplied by a previous request to either
           GetReportListByNextToken or GetReportList, where the
           value of HasNext was true in the previous call.
        """
        return self._post_request(request, kw, response)

    @boolean_arguments('Acknowledged')
    @structured_lists('ReportTypeList.Type')
    @api_action('Reports', 10, 45)
    def get_report_count(self, request, response, **kw):
        """Returns a count of the reports, created in the previous 90 days,
           with a status of _DONE_ and that are available for download.
        """
        return self._post_request(request, kw, response)

    @requires(['ReportId'])
    @api_action('Reports', 15, 60)
    def get_report(self, request, response, **kw):
        """Returns the contents of a report.
        """
        return self._post_request(request, kw, response)

    @requires(['ReportType', 'Schedule'])
    @api_action('Reports', 10, 45)
    def manage_report_schedule(self, request, response, **kw):
        """Creates, updates, or deletes a report request schedule for
           a specified report type.
        """
        return self._post_request(request, kw, response)

    @structured_lists('ReportTypeList.Type')
    @api_action('Reports', 10, 45)
    def get_report_schedule_list(self, request, response, **kw):
        """Returns a list of order report requests that are scheduled
           to be submitted to Amazon MWS for processing.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Reports', 0, 0)
    def get_report_schedule_list_by_next_token(self, request, response, **kw):
        """Returns a list of report requests using the NextToken,
           which was supplied by a previous request to either
           GetReportScheduleListByNextToken or GetReportScheduleList,
           where the value of HasNext was true in that previous request.
        """
        return self._post_request(request, kw, response)

    @structured_lists('ReportTypeList.Type')
    @api_action('Reports', 10, 45)
    def get_report_schedule_count(self, request, response, **kw):
        """Returns a count of order report requests that are scheduled
           to be submitted to Amazon MWS.
        """
        return self._post_request(request, kw, response)

    @requires(['ReportIdList'])
    @boolean_arguments('Acknowledged')
    @structured_lists('ReportIdList.Id')
    @api_action('Reports', 10, 45)
    def update_report_acknowledgements(self, request, response, **kw):
        """Updates the acknowledged status of one or more reports.
        """
        return self._post_request(request, kw, response)

    @requires(['ShipFromAddress', 'InboundShipmentPlanRequestItems'])
    @structured_objects('ShipFromAddress', 'InboundShipmentPlanRequestItems')
    @api_action('Inbound', 30, 0.5)
    def create_inbound_shipment_plan(self, request, response, **kw):
        """Returns the information required to create an inbound shipment.
        """
        return self._post_request(request, kw, response)

    @requires(['ShipmentId', 'InboundShipmentHeader', 'InboundShipmentItems'])
    @structured_objects('InboundShipmentHeader', 'InboundShipmentItems')
    @api_action('Inbound', 30, 0.5)
    def create_inbound_shipment(self, request, response, **kw):
        """Creates an inbound shipment.
        """
        return self._post_request(request, kw, response)

    @requires(['ShipmentId'])
    @structured_objects('InboundShipmentHeader', 'InboundShipmentItems')
    @api_action('Inbound', 30, 0.5)
    def update_inbound_shipment(self, request, response, **kw):
        """Updates an existing inbound shipment.  Amazon documentation
           is ambiguous as to whether the InboundShipmentHeader and
           InboundShipmentItems arguments are required.
        """
        return self._post_request(request, kw, response)

    @requires_some_of('ShipmentIdList', 'ShipmentStatusList')
    @structured_lists('ShipmentIdList.Id', 'ShipmentStatusList.Status')
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipments(self, request, response, **kw):
        """Returns a list of inbound shipments based on criteria that
           you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipments_by_next_token(self, request, response, **kw):
        """Returns the next page of inbound shipments using the NextToken
           parameter.
        """
        return self._post_request(request, kw, response)

    @requires(['ShipmentId'], ['LastUpdatedAfter', 'LastUpdatedBefore'])
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipment_items(self, request, response, **kw):
        """Returns a list of items in a specified inbound shipment, or a
           list of items that were updated within a specified time frame.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Inbound', 30, 0.5)
    def list_inbound_shipment_items_by_next_token(self, request, response, **kw):
        """Returns the next page of inbound shipment items using the
           NextToken parameter.
        """
        return self._post_request(request, kw, response)

    @api_action('Inbound', 2, 300, 'GetServiceStatus')
    def get_inbound_service_status(self, request, response, **kw):
        """Returns the operational status of the Fulfillment Inbound
           Shipment API section.
        """
        return self._post_request(request, kw, response)

    @requires(['SellerSkus'], ['QueryStartDateTime'])
    @structured_lists('SellerSkus.member')
    @api_action('Inventory', 30, 0.5)
    def list_inventory_supply(self, request, response, **kw):
        """Returns information about the availability of a seller's
           inventory.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Inventory', 30, 0.5)
    def list_inventory_supply_by_next_token(self, request, response, **kw):
        """Returns the next page of information about the availability
           of a seller's inventory using the NextToken parameter.
        """
        return self._post_request(request, kw, response)

    @api_action('Inventory', 2, 300, 'GetServiceStatus')
    def get_inventory_service_status(self, request, response, **kw):
        """Returns the operational status of the Fulfillment Inventory
           API section.
        """
        return self._post_request(request, kw, response)

    @requires(['PackageNumber'])
    @api_action('Outbound', 30, 0.5)
    def get_package_tracking_details(self, request, response, **kw):
        """Returns delivery tracking information for a package in
           an outbound shipment for a Multi-Channel Fulfillment order.
        """
        return self._post_request(request, kw, response)

    @requires(['Address', 'Items'])
    @structured_objects('Address', 'Items')
    @api_action('Outbound', 30, 0.5)
    def get_fulfillment_preview(self, request, response, **kw):
        """Returns a list of fulfillment order previews based on items
           and shipping speed categories that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['SellerFulfillmentOrderId', 'DisplayableOrderId',
               'ShippingSpeedCategory',    'DisplayableOrderDateTime',
               'DestinationAddress',       'DisplayableOrderComment',
               'Items'])
    @structured_objects('DestinationAddress', 'Items')
    @api_action('Outbound', 30, 0.5)
    def create_fulfillment_order(self, request, response, **kw):
        """Requests that Amazon ship items from the seller's inventory
           to a destination address.
        """
        return self._post_request(request, kw, response)

    @requires(['SellerFulfillmentOrderId'])
    @api_action('Outbound', 30, 0.5)
    def get_fulfillment_order(self, request, response, **kw):
        """Returns a fulfillment order based on a specified
           SellerFulfillmentOrderId.
        """
        return self._post_request(request, kw, response)

    @api_action('Outbound', 30, 0.5)
    def list_all_fulfillment_orders(self, request, response, **kw):
        """Returns a list of fulfillment orders fulfilled after (or
           at) a specified date or by fulfillment method.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Outbound', 30, 0.5)
    def list_all_fulfillment_orders_by_next_token(self, request, response, **kw):
        """Returns the next page of inbound shipment items using the
           NextToken parameter.
        """
        return self._post_request(request, kw, response)

    @requires(['SellerFulfillmentOrderId'])
    @api_action('Outbound', 30, 0.5)
    def cancel_fulfillment_order(self, request, response, **kw):
        """Requests that Amazon stop attempting to fulfill an existing
           fulfillment order.
        """
        return self._post_request(request, kw, response)

    @api_action('Outbound', 2, 300, 'GetServiceStatus')
    def get_outbound_service_status(self, request, response, **kw):
        """Returns the operational status of the Fulfillment Outbound
           API section.
        """
        return self._post_request(request, kw, response)

    @requires(['CreatedAfter'], ['LastUpdatedAfter'])
    @requires(['MarketplaceId'])
    @exclusive(['CreatedAfter'], ['LastUpdatedAfter'])
    @dependent('CreatedBefore', ['CreatedAfter'])
    @exclusive(['LastUpdatedAfter'], ['BuyerEmail'], ['SellerOrderId'])
    @dependent('LastUpdatedBefore', ['LastUpdatedAfter'])
    @exclusive(['CreatedAfter'], ['LastUpdatedBefore'])
    @structured_objects('OrderTotal', 'ShippingAddress',
                        'PaymentExecutionDetail')
    @structured_lists('MarketplaceId.Id', 'OrderStatus.Status',
                      'FulfillmentChannel.Channel', 'PaymentMethod.')
    @api_action('Orders', 6, 60)
    def list_orders(self, request, response, **kw):
        """Returns a list of orders created or updated during a time
           frame that you specify.
        """
        toggle = set(('FulfillmentChannel.Channel.1',
                      'OrderStatus.Status.1', 'PaymentMethod.1',
                      'LastUpdatedAfter', 'LastUpdatedBefore'))
        for do, dont in {
            'BuyerEmail': toggle.union(['SellerOrderId']),
            'SellerOrderId': toggle.union(['BuyerEmail']),
        }.items():
            if do in kw and any(i in dont for i in kw):
                message = "Don't include {0} when specifying " \
                          "{1}".format(' or '.join(dont), do)
                raise AssertionError(message)
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Orders', 6, 60)
    def list_orders_by_next_token(self, request, response, **kw):
        """Returns the next page of orders using the NextToken value
           that was returned by your previous request to either
           ListOrders or ListOrdersByNextToken.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderId'])
    @structured_lists('AmazonOrderId.Id')
    @api_action('Orders', 6, 60)
    def get_order(self, request, response, **kw):
        """Returns an order for each AmazonOrderId that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderId'])
    @api_action('Orders', 30, 2)
    def list_order_items(self, request, response, **kw):
        """Returns order item information for an AmazonOrderId that
           you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Orders', 30, 2)
    def list_order_items_by_next_token(self, request, response, **kw):
        """Returns the next page of order items using the NextToken
           value that was returned by your previous request to either
           ListOrderItems or ListOrderItemsByNextToken.
        """
        return self._post_request(request, kw, response)

    @api_action('Orders', 2, 300, 'GetServiceStatus')
    def get_orders_service_status(self, request, response, **kw):
        """Returns the operational status of the Orders API section.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'Query'])
    @api_action('Products', 20, 20)
    def list_matching_products(self, request, response, **kw):
        """Returns a list of products and their attributes, ordered
           by relevancy, based on a search query that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 20)
    def get_matching_product(self, request, response, **kw):
        """Returns a list of products and their attributes, based on
           a list of ASIN values that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'IdType', 'IdList'])
    @structured_lists('IdList.Id')
    @api_action('Products', 20, 20)
    def get_matching_product_for_id(self, request, response, **kw):
        """Returns a list of products and their attributes, based on
           a list of Product IDs that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'SellerSKUList'])
    @structured_lists('SellerSKUList.SellerSKU')
    @api_action('Products', 20, 10, 'GetCompetitivePricingForSKU')
    def get_competitive_pricing_for_sku(self, request, response, **kw):
        """Returns the current competitive pricing of a product,
           based on the SellerSKUs and MarketplaceId that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 10, 'GetCompetitivePricingForASIN')
    def get_competitive_pricing_for_asin(self, request, response, **kw):
        """Returns the current competitive pricing of a product,
           based on the ASINs and MarketplaceId that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'SellerSKUList'])
    @structured_lists('SellerSKUList.SellerSKU')
    @api_action('Products', 20, 5, 'GetLowestOfferListingsForSKU')
    def get_lowest_offer_listings_for_sku(self, request, response, **kw):
        """Returns the lowest price offer listings for a specific
           product by item condition and SellerSKUs.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 5, 'GetLowestOfferListingsForASIN')
    def get_lowest_offer_listings_for_asin(self, request, response, **kw):
        """Returns the lowest price offer listings for a specific
           product by item condition and ASINs.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'SellerSKU'])
    @api_action('Products', 20, 20, 'GetProductCategoriesForSKU')
    def get_product_categories_for_sku(self, request, response, **kw):
        """Returns the product categories that a SellerSKU belongs to.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'ASIN'])
    @api_action('Products', 20, 20, 'GetProductCategoriesForASIN')
    def get_product_categories_for_asin(self, request, response, **kw):
        """Returns the product categories that an ASIN belongs to.
        """
        return self._post_request(request, kw, response)

    @api_action('Products', 2, 300, 'GetServiceStatus')
    def get_products_service_status(self, request, response, **kw):
        """Returns the operational status of the Products API section.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'SellerSKUList'])
    @structured_lists('SellerSKUList.SellerSKU')
    @api_action('Products', 20, 10, 'GetMyPriceForSKU')
    def get_my_price_for_sku(self, request, response, **kw):
        """Returns pricing information for your own offer listings, based on SellerSKU.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'ASINList'])
    @structured_lists('ASINList.ASIN')
    @api_action('Products', 20, 10, 'GetMyPriceForASIN')
    def get_my_price_for_asin(self, request, response, **kw):
        """Returns pricing information for your own offer listings, based on ASIN.
        """
        return self._post_request(request, kw, response)

    @api_action('Sellers', 15, 60)
    def list_marketplace_participations(self, request, response, **kw):
        """Returns a list of marketplaces that the seller submitting
           the request can sell in, and a list of participations that
           include seller-specific information in that marketplace.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Sellers', 15, 60)
    def list_marketplace_participations_by_next_token(self, request, response,
                                                      **kw):
        """Returns the next page of marketplaces and participations
           using the NextToken value that was returned by your
           previous request to either ListMarketplaceParticipations
           or ListMarketplaceParticipationsByNextToken.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId'])
    @api_action('Recommendations', 5, 2)
    def get_last_updated_time_for_recommendations(self, request, response,
                                                  **kw):
        """Checks whether there are active recommendations for each category
           for the given marketplace, and if there are, returns the time when
           recommendations were last updated for each category.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId'])
    @structured_lists('CategoryQueryList.CategoryQuery')
    @api_action('Recommendations', 5, 2)
    def list_recommendations(self, request, response, **kw):
        """Returns your active recommendations for a specific category or for
           all categories for a specific marketplace.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('Recommendations', 5, 2)
    def list_recommendations_by_next_token(self, request, response, **kw):
        """Returns the next page of recommendations using the NextToken
           parameter.
        """
        return self._post_request(request, kw, response)

    @api_action('Recommendations', 2, 300, 'GetServiceStatus')
    def get_recommendations_service_status(self, request, response, **kw):
        """Returns the operational status of the Recommendations API section.
        """
        return self._post_request(request, kw, response)

    @api_action('CustomerInfo', 15, 12)
    def list_customers(self, request, response, **kw):
        """Returns a list of customer accounts based on search criteria that
           you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('CustomerInfo', 50, 3)
    def list_customers_by_next_token(self, request, response, **kw):
        """Returns the next page of customers using the NextToken parameter.
        """
        return self._post_request(request, kw, response)

    @requires(['CustomerIdList'])
    @structured_lists('CustomerIdList.CustomerId')
    @api_action('CustomerInfo', 15, 12)
    def get_customers_for_customer_id(self, request, response, **kw):
        """Returns a list of customer accounts based on search criteria that
           you specify.
        """
        return self._post_request(request, kw, response)

    @api_action('CustomerInfo', 2, 300, 'GetServiceStatus')
    def get_customerinfo_service_status(self, request, response, **kw):
        """Returns the operational status of the Customer Information API
           section.
        """
        return self._post_request(request, kw, response)

    @requires(['DateRangeStart'])
    @api_action('CartInfo', 15, 12)
    def list_carts(self, request, response, **kw):
        """Returns a list of shopping carts in your Webstore that were last
           updated during the time range that you specify.
        """
        return self._post_request(request, kw, response)

    @requires(['NextToken'])
    @api_action('CartInfo', 50, 3)
    def list_carts_by_next_token(self, request, response, **kw):
        """Returns the next page of shopping carts using the NextToken
           parameter.
        """
        return self._post_request(request, kw, response)

    @requires(['CartIdList'])
    @structured_lists('CartIdList.CartId')
    @api_action('CartInfo', 15, 12)
    def get_carts(self, request, response, **kw):
        """Returns shopping carts based on the CartId values that you specify.
        """
        return self._post_request(request, kw, response)

    @api_action('CartInfo', 2, 300, 'GetServiceStatus')
    def get_cartinfo_service_status(self, request, response, **kw):
        """Returns the operational status of the Cart Information API section.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'Destination'])
    @structured_objects('Destination', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def register_destination(self, request, response, **kw):
        """Specifies a new destination where you want to receive notifications.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'Destination'])
    @structured_objects('Destination', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def deregister_destination(self, request, response, **kw):
        """Removes an existing destination from the list of registered
           destinations.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId'])
    @api_action('Subscriptions', 25, 0.5)
    def list_registered_destinations(self, request, response, **kw):
        """Lists all current destinations that you have registered.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'Destination'])
    @structured_objects('Destination', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def send_test_notification_to_destination(self, request, response, **kw):
        """Sends a test notification to an existing destination.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'Subscription'])
    @structured_objects('Subscription', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def create_subscription(self, request, response, **kw):
        """Creates a new subscription for the specified notification type
           and destination.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'NotificationType', 'Destination'])
    @structured_objects('Destination', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def get_subscription(self, request, response, **kw):
        """Gets the subscription for the specified notification type and
           destination.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'NotificationType', 'Destination'])
    @structured_objects('Destination', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def delete_subscription(self, request, response, **kw):
        """Deletes the subscription for the specified notification type and
           destination.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId'])
    @api_action('Subscriptions', 25, 0.5)
    def list_subscriptions(self, request, response, **kw):
        """Returns a list of all your current subscriptions.
        """
        return self._post_request(request, kw, response)

    @requires(['MarketplaceId', 'Subscription'])
    @structured_objects('Subscription', members=True)
    @api_action('Subscriptions', 25, 0.5)
    def update_subscription(self, request, response, **kw):
        """Updates the subscription for the specified notification type and
           destination.
        """
        return self._post_request(request, kw, response)

    @api_action('Subscriptions', 2, 300, 'GetServiceStatus')
    def get_subscriptions_service_status(self, request, response, **kw):
        """Returns the operational status of the Subscriptions API section.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderReferenceId', 'OrderReferenceAttributes'])
    @structured_objects('OrderReferenceAttributes')
    @api_action('OffAmazonPayments', 10, 1)
    def set_order_reference_details(self, request, response, **kw):
        """Sets order reference details such as the order total and a
           description for the order.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderReferenceId'])
    @api_action('OffAmazonPayments', 20, 2)
    def get_order_reference_details(self, request, response, **kw):
        """Returns details about the Order Reference object and its current
           state.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderReferenceId'])
    @api_action('OffAmazonPayments', 10, 1)
    def confirm_order_reference(self, request, response, **kw):
        """Confirms that the order reference is free of constraints and all
           required information has been set on the order reference.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderReferenceId'])
    @api_action('OffAmazonPayments', 10, 1)
    def cancel_order_reference(self, request, response, **kw):
        """Cancel an order reference; all authorizations associated with
           this order reference are also closed.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderReferenceId'])
    @api_action('OffAmazonPayments', 10, 1)
    def close_order_reference(self, request, response, **kw):
        """Confirms that an order reference has been fulfilled (fully
           or partially) and that you do not expect to create any new
           authorizations on this order reference.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonOrderReferenceId', 'AuthorizationReferenceId',
               'AuthorizationAmount'])
    @structured_objects('AuthorizationAmount')
    @api_action('OffAmazonPayments', 10, 1)
    def authorize(self, request, response, **kw):
        """Reserves a specified amount against the payment method(s) stored in
           the order reference.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonAuthorizationId'])
    @api_action('OffAmazonPayments', 20, 2)
    def get_authorization_details(self, request, response, **kw):
        """Returns the status of a particular authorization and the total
           amount captured on the authorization.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonAuthorizationId', 'CaptureReferenceId', 'CaptureAmount'])
    @structured_objects('CaptureAmount')
    @api_action('OffAmazonPayments', 10, 1)
    def capture(self, request, response, **kw):
        """Captures funds from an authorized payment instrument.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonCaptureId'])
    @api_action('OffAmazonPayments', 20, 2)
    def get_capture_details(self, request, response, **kw):
        """Returns the status of a particular capture and the total amount
           refunded on the capture.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonAuthorizationId'])
    @api_action('OffAmazonPayments', 10, 1)
    def close_authorization(self, request, response, **kw):
        """Closes an authorization.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonCaptureId', 'RefundReferenceId', 'RefundAmount'])
    @structured_objects('RefundAmount')
    @api_action('OffAmazonPayments', 10, 1)
    def refund(self, request, response, **kw):
        """Refunds a previously captured amount.
        """
        return self._post_request(request, kw, response)

    @requires(['AmazonRefundId'])
    @api_action('OffAmazonPayments', 20, 2)
    def get_refund_details(self, request, response, **kw):
        """Returns the status of a particular refund.
        """
        return self._post_request(request, kw, response)

    @api_action('OffAmazonPayments', 2, 300, 'GetServiceStatus')
    def get_offamazonpayments_service_status(self, request, response, **kw):
        """Returns the operational status of the Off-Amazon Payments API
           section.
        """
        return self._post_request(request, kw, response)
