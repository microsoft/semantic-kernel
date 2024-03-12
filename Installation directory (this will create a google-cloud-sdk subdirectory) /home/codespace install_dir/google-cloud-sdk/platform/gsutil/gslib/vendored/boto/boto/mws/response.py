# Copyright (c) 2012-2014 Andy Davidoff http://www.disruptek.com/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, dis- tribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the fol- lowing conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL- ITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
from decimal import Decimal
from boto.compat import filter, map


class ComplexType(dict):
    _value = 'Value'

    def __repr__(self):
        return '{0}{1}'.format(getattr(self, self._value, None), self.copy())

    def __str__(self):
        return str(getattr(self, self._value, ''))


class DeclarativeType(object):
    def __init__(self, _hint=None, **kw):
        self._value = None
        if _hint is not None:
            self._hint = _hint
            return

        class JITResponse(ResponseElement):
            pass
        self._hint = JITResponse
        self._hint.__name__ = 'JIT_{0}/{1}'.format(self.__class__.__name__,
                                                   hex(id(self._hint))[2:])
        for name, value in kw.items():
            setattr(self._hint, name, value)

    def __repr__(self):
        parent = getattr(self, '_parent', None)
        return '<{0}_{1}/{2}_{3}>'.format(self.__class__.__name__,
                                          parent and parent._name or '?',
                                          getattr(self, '_name', '?'),
                                          hex(id(self.__class__)))

    def setup(self, parent, name, *args, **kw):
        self._parent = parent
        self._name = name
        self._clone = self.__class__(_hint=self._hint)
        self._clone._parent = parent
        self._clone._name = name
        setattr(self._parent, self._name, self._clone)

    def start(self, *args, **kw):
        raise NotImplementedError

    def end(self, *args, **kw):
        raise NotImplementedError

    def teardown(self, *args, **kw):
        setattr(self._parent, self._name, self._value)


class Element(DeclarativeType):
    def start(self, *args, **kw):
        self._value = self._hint(parent=self._parent, **kw)
        return self._value

    def end(self, *args, **kw):
        pass


class SimpleList(DeclarativeType):
    def __init__(self, *args, **kw):
        super(SimpleList, self).__init__(*args, **kw)
        self._value = []

    def start(self, *args, **kw):
        return None

    def end(self, name, value, *args, **kw):
        self._value.append(value)


class ElementList(SimpleList):
    def start(self, *args, **kw):
        value = self._hint(parent=self._parent, **kw)
        self._value.append(value)
        return value

    def end(self, *args, **kw):
        pass


class MemberList(Element):
    def __init__(self, _member=None, _hint=None, *args, **kw):
        message = 'Invalid `member` specification in {0}'.format(self.__class__.__name__)
        assert 'member' not in kw, message
        if _member is None:
            if _hint is None:
                super(MemberList, self).__init__(*args, member=ElementList(**kw))
            else:
                super(MemberList, self).__init__(_hint=_hint)
        else:
            if _hint is None:
                if issubclass(_member, DeclarativeType):
                    member = _member(**kw)
                else:
                    member = ElementList(_member, **kw)
                super(MemberList, self).__init__(*args, member=member)
            else:
                message = 'Nonsensical {0} hint {1!r}'.format(self.__class__.__name__,
                                                              _hint)
                raise AssertionError(message)

    def teardown(self, *args, **kw):
        if self._value is None:
            self._value = []
        else:
            if isinstance(self._value.member, DeclarativeType):
                self._value.member = []
            self._value = self._value.member
        super(MemberList, self).teardown(*args, **kw)


class ResponseFactory(object):
    def __init__(self, scopes=None):
        self.scopes = [] if scopes is None else scopes

    def element_factory(self, name, parent):
        class DynamicElement(parent):
            _name = name
        setattr(DynamicElement, '__name__', str(name))
        return DynamicElement

    def search_scopes(self, key):
        for scope in self.scopes:
            if hasattr(scope, key):
                return getattr(scope, key)
            if hasattr(scope, '__getitem__'):
                if key in scope:
                    return scope[key]

    def find_element(self, action, suffix, parent):
        element = self.search_scopes(action + suffix)
        if element is not None:
            return element
        if action.endswith('ByNextToken'):
            element = self.search_scopes(action[:-len('ByNextToken')] + suffix)
            if element is not None:
                return self.element_factory(action + suffix, element)
        return self.element_factory(action + suffix, parent)

    def __call__(self, action, connection=None):
        response = self.find_element(action, 'Response', Response)
        if not hasattr(response, action + 'Result'):
            result = self.find_element(action, 'Result', ResponseElement)
            setattr(response, action + 'Result', Element(result))
        return response(connection=connection)


def strip_namespace(func):
    def wrapper(self, name, *args, **kw):
        if self._namespace is not None:
            if name.startswith(self._namespace + ':'):
                name = name[len(self._namespace + ':'):]
        return func(self, name, *args, **kw)
    return wrapper


class ResponseElement(dict):
    _override = {}
    _name = None
    _namespace = None

    def __init__(self, connection=None, name=None, parent=None, attrs=None):
        if parent is not None and self._namespace is None:
            self._namespace = parent._namespace
        if connection is not None:
            self._connection = connection
        self._name = name or self._name or self.__class__.__name__
        self._declared('setup', attrs=attrs)
        dict.__init__(self, attrs and attrs.copy() or {})

    def _declared(self, op, **kw):
        def inherit(obj):
            result = {}
            for cls in getattr(obj, '__bases__', ()):
                result.update(inherit(cls))
            result.update(obj.__dict__)
            return result

        scope = inherit(self.__class__)
        scope.update(self.__dict__)
        declared = lambda attr: isinstance(attr[1], DeclarativeType)
        for name, node in filter(declared, scope.items()):
            getattr(node, op)(self, name, parentname=self._name, **kw)

    @property
    def connection(self):
        return self._connection

    def __repr__(self):
        render = lambda pair: '{0!s}: {1!r}'.format(*pair)
        do_show = lambda pair: not pair[0].startswith('_')
        attrs = filter(do_show, self.__dict__.items())
        name = self.__class__.__name__
        if name.startswith('JIT_'):
            name = '^{0}^'.format(self._name or '')
        return '{0}{1!r}({2})'.format(
            name, self.copy(), ', '.join(map(render, attrs)))

    def _type_for(self, name, attrs):
        return self._override.get(name, globals().get(name, ResponseElement))

    @strip_namespace
    def startElement(self, name, attrs, connection):
        attribute = getattr(self, name, None)
        if isinstance(attribute, DeclarativeType):
            return attribute.start(name=name, attrs=attrs,
                                   connection=connection)
        elif attrs.getLength():
            setattr(self, name, ComplexType(attrs.copy()))
        else:
            return None

    @strip_namespace
    def endElement(self, name, value, connection):
        attribute = getattr(self, name, None)
        if name == self._name:
            self._declared('teardown')
        elif isinstance(attribute, DeclarativeType):
            attribute.end(name=name, value=value, connection=connection)
        elif isinstance(attribute, ComplexType):
            setattr(attribute, attribute._value, value)
        else:
            setattr(self, name, value)


class Response(ResponseElement):
    ResponseMetadata = Element()

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name == self._name:
            self.update(attrs)
        else:
            return super(Response, self).startElement(name, attrs, connection)

    @property
    def _result(self):
        return getattr(self, self._action + 'Result', None)

    @property
    def _action(self):
        return (self._name or self.__class__.__name__)[:-len('Response')]


class ResponseResultList(Response):
    _ResultClass = ResponseElement

    def __init__(self, *args, **kw):
        setattr(self, self._action + 'Result', ElementList(self._ResultClass))
        super(ResponseResultList, self).__init__(*args, **kw)


class FeedSubmissionInfo(ResponseElement):
    pass


class SubmitFeedResult(ResponseElement):
    FeedSubmissionInfo = Element(FeedSubmissionInfo)


class GetFeedSubmissionListResult(ResponseElement):
    FeedSubmissionInfo = ElementList(FeedSubmissionInfo)


class GetFeedSubmissionCountResult(ResponseElement):
    pass


class CancelFeedSubmissionsResult(GetFeedSubmissionListResult):
    pass


class GetServiceStatusResult(ResponseElement):
    Messages = Element(Messages=ElementList())


class ReportRequestInfo(ResponseElement):
    pass


class RequestReportResult(ResponseElement):
    ReportRequestInfo = Element()


class GetReportRequestListResult(RequestReportResult):
    ReportRequestInfo = ElementList()


class CancelReportRequestsResult(RequestReportResult):
    pass


class GetReportListResult(ResponseElement):
    ReportInfo = ElementList()


class ManageReportScheduleResult(ResponseElement):
    ReportSchedule = Element()


class GetReportScheduleListResult(ManageReportScheduleResult):
    pass


class UpdateReportAcknowledgementsResult(GetReportListResult):
    pass


class CreateInboundShipmentPlanResult(ResponseElement):
    InboundShipmentPlans = MemberList(ShipToAddress=Element(),
                                      Items=MemberList())


class ListInboundShipmentsResult(ResponseElement):
    ShipmentData = MemberList(ShipFromAddress=Element())


class ListInboundShipmentItemsResult(ResponseElement):
    ItemData = MemberList()


class ListInventorySupplyResult(ResponseElement):
    InventorySupplyList = MemberList(
        EarliestAvailability=Element(),
        SupplyDetail=MemberList(
            EarliestAvailableToPick=Element(),
            LatestAvailableToPick=Element(),
        )
    )


class ComplexAmount(ResponseElement):
    _amount = 'Value'

    def __repr__(self):
        return '{0} {1}'.format(self.CurrencyCode, getattr(self, self._amount))

    def __float__(self):
        return float(getattr(self, self._amount))

    def __str__(self):
        return str(getattr(self, self._amount))

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name not in ('CurrencyCode', self._amount):
            message = 'Unrecognized tag {0} in ComplexAmount'.format(name)
            raise AssertionError(message)
        return super(ComplexAmount, self).startElement(name, attrs, connection)

    @strip_namespace
    def endElement(self, name, value, connection):
        if name == self._amount:
            value = Decimal(value)
        super(ComplexAmount, self).endElement(name, value, connection)


class ComplexMoney(ComplexAmount):
    _amount = 'Amount'


class ComplexWeight(ResponseElement):
    def __repr__(self):
        return '{0} {1}'.format(self.Value, self.Unit)

    def __float__(self):
        return float(self.Value)

    def __str__(self):
        return str(self.Value)

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name not in ('Unit', 'Value'):
            message = 'Unrecognized tag {0} in ComplexWeight'.format(name)
            raise AssertionError(message)
        return super(ComplexWeight, self).startElement(name, attrs, connection)

    @strip_namespace
    def endElement(self, name, value, connection):
        if name == 'Value':
            value = Decimal(value)
        super(ComplexWeight, self).endElement(name, value, connection)


class Dimension(ComplexType):
    _value = 'Value'


class ComplexDimensions(ResponseElement):
    _dimensions = ('Height', 'Length', 'Width', 'Weight')

    def __repr__(self):
        values = [getattr(self, key, None) for key in self._dimensions]
        values = filter(None, values)
        return 'x'.join(map('{0.Value:0.2f}{0[Units]}'.format, values))

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name not in self._dimensions:
            message = 'Unrecognized tag {0} in ComplexDimensions'.format(name)
            raise AssertionError(message)
        setattr(self, name, Dimension(attrs.copy()))

    @strip_namespace
    def endElement(self, name, value, connection):
        if name in self._dimensions:
            value = Decimal(value or '0')
        ResponseElement.endElement(self, name, value, connection)


class FulfillmentPreviewItem(ResponseElement):
    EstimatedShippingWeight = Element(ComplexWeight)


class FulfillmentPreview(ResponseElement):
    EstimatedShippingWeight = Element(ComplexWeight)
    EstimatedFees = MemberList(Amount=Element(ComplexAmount))
    UnfulfillablePreviewItems = MemberList(FulfillmentPreviewItem)
    FulfillmentPreviewShipments = MemberList(
        FulfillmentPreviewItems=MemberList(FulfillmentPreviewItem),
    )


class GetFulfillmentPreviewResult(ResponseElement):
    FulfillmentPreviews = MemberList(FulfillmentPreview)


class FulfillmentOrder(ResponseElement):
    DestinationAddress = Element()
    NotificationEmailList = MemberList(SimpleList)


class GetFulfillmentOrderResult(ResponseElement):
    FulfillmentOrder = Element(FulfillmentOrder)
    FulfillmentShipment = MemberList(
        FulfillmentShipmentItem=MemberList(),
        FulfillmentShipmentPackage=MemberList(),
    )
    FulfillmentOrderItem = MemberList()


class ListAllFulfillmentOrdersResult(ResponseElement):
    FulfillmentOrders = MemberList(FulfillmentOrder)


class GetPackageTrackingDetailsResult(ResponseElement):
    ShipToAddress = Element()
    TrackingEvents = MemberList(EventAddress=Element())


class Image(ResponseElement):
    pass


class AttributeSet(ResponseElement):
    ItemDimensions = Element(ComplexDimensions)
    ListPrice = Element(ComplexMoney)
    PackageDimensions = Element(ComplexDimensions)
    SmallImage = Element(Image)


class ItemAttributes(AttributeSet):
    Languages = Element(Language=ElementList())

    def __init__(self, *args, **kw):
        names = ('Actor', 'Artist', 'Author', 'Creator', 'Director',
                 'Feature', 'Format', 'GemType', 'MaterialType',
                 'MediaType', 'OperatingSystem', 'Platform')
        for name in names:
            setattr(self, name, SimpleList())
        super(ItemAttributes, self).__init__(*args, **kw)


class VariationRelationship(ResponseElement):
    Identifiers = Element(MarketplaceASIN=Element(),
                          SKUIdentifier=Element())
    GemType = SimpleList()
    MaterialType = SimpleList()
    OperatingSystem = SimpleList()


class Price(ResponseElement):
    LandedPrice = Element(ComplexMoney)
    ListingPrice = Element(ComplexMoney)
    Shipping = Element(ComplexMoney)


class CompetitivePrice(ResponseElement):
    Price = Element(Price)


class CompetitivePriceList(ResponseElement):
    CompetitivePrice = ElementList(CompetitivePrice)


class CompetitivePricing(ResponseElement):
    CompetitivePrices = Element(CompetitivePriceList)
    NumberOfOfferListings = SimpleList()
    TradeInValue = Element(ComplexMoney)


class SalesRank(ResponseElement):
    pass


class LowestOfferListing(ResponseElement):
    Qualifiers = Element(ShippingTime=Element())
    Price = Element(Price)


class Offer(ResponseElement):
    BuyingPrice = Element(Price)
    RegularPrice = Element(ComplexMoney)


class Product(ResponseElement):
    _namespace = 'ns2'
    Identifiers = Element(MarketplaceASIN=Element(),
                          SKUIdentifier=Element())
    AttributeSets = Element(
        ItemAttributes=ElementList(ItemAttributes),
    )
    Relationships = Element(
        VariationParent=ElementList(VariationRelationship),
    )
    CompetitivePricing = ElementList(CompetitivePricing)
    SalesRankings = Element(
        SalesRank=ElementList(SalesRank),
    )
    LowestOfferListings = Element(
        LowestOfferListing=ElementList(LowestOfferListing),
    )
    Offers = Element(
        Offer=ElementList(Offer),
    )


class ListMatchingProductsResult(ResponseElement):
    Products = Element(Product=ElementList(Product))


class ProductsBulkOperationResult(ResponseElement):
    Product = Element(Product)
    Error = Element()


class ProductsBulkOperationResponse(ResponseResultList):
    _ResultClass = ProductsBulkOperationResult


class GetMatchingProductResponse(ProductsBulkOperationResponse):
    pass


class GetMatchingProductForIdResult(ListMatchingProductsResult):
    pass


class GetMatchingProductForIdResponse(ResponseResultList):
    _ResultClass = GetMatchingProductForIdResult


class GetCompetitivePricingForSKUResponse(ProductsBulkOperationResponse):
    pass


class GetCompetitivePricingForASINResponse(ProductsBulkOperationResponse):
    pass


class GetLowestOfferListingsForSKUResponse(ProductsBulkOperationResponse):
    pass


class GetLowestOfferListingsForASINResponse(ProductsBulkOperationResponse):
    pass


class GetMyPriceForSKUResponse(ProductsBulkOperationResponse):
    pass


class GetMyPriceForASINResponse(ProductsBulkOperationResponse):
    pass


class ProductCategory(ResponseElement):

    def __init__(self, *args, **kw):
        setattr(self, 'Parent', Element(ProductCategory))
        super(ProductCategory, self).__init__(*args, **kw)


class GetProductCategoriesResult(ResponseElement):
    Self = ElementList(ProductCategory)


class GetProductCategoriesForSKUResult(GetProductCategoriesResult):
    pass


class GetProductCategoriesForASINResult(GetProductCategoriesResult):
    pass


class Order(ResponseElement):
    OrderTotal = Element(ComplexMoney)
    ShippingAddress = Element()
    PaymentExecutionDetail = Element(
        PaymentExecutionDetailItem=ElementList(
            PaymentExecutionDetailItem=Element(
                Payment=Element(ComplexMoney)
            )
        )
    )


class ListOrdersResult(ResponseElement):
    Orders = Element(Order=ElementList(Order))


class GetOrderResult(ListOrdersResult):
    pass


class OrderItem(ResponseElement):
    ItemPrice = Element(ComplexMoney)
    ShippingPrice = Element(ComplexMoney)
    GiftWrapPrice = Element(ComplexMoney)
    ItemTax = Element(ComplexMoney)
    ShippingTax = Element(ComplexMoney)
    GiftWrapTax = Element(ComplexMoney)
    ShippingDiscount = Element(ComplexMoney)
    PromotionDiscount = Element(ComplexMoney)
    PromotionIds = SimpleList()
    CODFee = Element(ComplexMoney)
    CODFeeDiscount = Element(ComplexMoney)


class ListOrderItemsResult(ResponseElement):
    OrderItems = Element(OrderItem=ElementList(OrderItem))


class ListMarketplaceParticipationsResult(ResponseElement):
    ListParticipations = Element(Participation=ElementList())
    ListMarketplaces = Element(Marketplace=ElementList())


class ListRecommendationsResult(ResponseElement):
    ListingQualityRecommendations = MemberList(ItemIdentifier=Element())


class Customer(ResponseElement):
    PrimaryContactInfo = Element()
    ShippingAddressList = Element(ShippingAddress=ElementList())
    AssociatedMarketplaces = Element(MarketplaceDomain=ElementList())


class ListCustomersResult(ResponseElement):
    CustomerList = Element(Customer=ElementList(Customer))


class GetCustomersForCustomerIdResult(ListCustomersResult):
    pass


class CartItem(ResponseElement):
    CurrentPrice = Element(ComplexMoney)
    SalePrice = Element(ComplexMoney)


class Cart(ResponseElement):
    ActiveCartItemList = Element(CartItem=ElementList(CartItem))
    SavedCartItemList = Element(CartItem=ElementList(CartItem))


class ListCartsResult(ResponseElement):
    CartList = Element(Cart=ElementList(Cart))


class GetCartsResult(ListCartsResult):
    pass


class Destination(ResponseElement):
    AttributeList = MemberList()


class ListRegisteredDestinationsResult(ResponseElement):
    DestinationList = MemberList(Destination)


class Subscription(ResponseElement):
    Destination = Element(Destination)


class GetSubscriptionResult(ResponseElement):
    Subscription = Element(Subscription)


class ListSubscriptionsResult(ResponseElement):
    SubscriptionList = MemberList(Subscription)


class OrderReferenceDetails(ResponseElement):
    Buyer = Element()
    OrderTotal = Element(ComplexMoney)
    Destination = Element(PhysicalDestination=Element())
    SellerOrderAttributes = Element()
    OrderReferenceStatus = Element()
    Constraints = ElementList()


class SetOrderReferenceDetailsResult(ResponseElement):
    OrderReferenceDetails = Element(OrderReferenceDetails)


class GetOrderReferenceDetailsResult(SetOrderReferenceDetailsResult):
    pass


class AuthorizationDetails(ResponseElement):
    AuthorizationAmount = Element(ComplexMoney)
    CapturedAmount = Element(ComplexMoney)
    AuthorizationFee = Element(ComplexMoney)
    AuthorizationStatus = Element()


class AuthorizeResult(ResponseElement):
    AuthorizationDetails = Element(AuthorizationDetails)


class GetAuthorizationDetailsResult(AuthorizeResult):
    pass


class CaptureDetails(ResponseElement):
    CaptureAmount = Element(ComplexMoney)
    RefundedAmount = Element(ComplexMoney)
    CaptureFee = Element(ComplexMoney)
    CaptureStatus = Element()


class CaptureResult(ResponseElement):
    CaptureDetails = Element(CaptureDetails)


class GetCaptureDetailsResult(CaptureResult):
    pass


class RefundDetails(ResponseElement):
    RefundAmount = Element(ComplexMoney)
    FeeRefunded = Element(ComplexMoney)
    RefundStatus = Element()


class RefundResult(ResponseElement):
    RefundDetails = Element(RefundDetails)


class GetRefundDetails(RefundResult):
    pass
