# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import boto
from boto.compat import json
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.route53.domains import exceptions


class Route53DomainsConnection(AWSQueryConnection):
    """
    
    """
    APIVersion = "2014-05-15"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "route53domains.us-east-1.amazonaws.com"
    ServiceName = "Route53Domains"
    TargetPrefix = "Route53Domains_v20140515"
    ResponseError = JSONResponseError

    _faults = {
        "DuplicateRequest": exceptions.DuplicateRequest,
        "DomainLimitExceeded": exceptions.DomainLimitExceeded,
        "InvalidInput": exceptions.InvalidInput,
        "OperationLimitExceeded": exceptions.OperationLimitExceeded,
        "UnsupportedTLD": exceptions.UnsupportedTLD,
        "TLDRulesViolation": exceptions.TLDRulesViolation,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(Route53DomainsConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def check_domain_availability(self, domain_name, idn_lang_code=None):
        """
        This operation checks the availability of one domain name. You
        can access this API without authenticating. Note that if the
        availability status of a domain is pending, you must submit
        another request to determine the availability of the domain
        name.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        :type idn_lang_code: string
        :param idn_lang_code: Reserved for future use.

        """
        params = {'DomainName': domain_name, }
        if idn_lang_code is not None:
            params['IdnLangCode'] = idn_lang_code
        return self.make_request(action='CheckDomainAvailability',
                                 body=json.dumps(params))

    def disable_domain_transfer_lock(self, domain_name):
        """
        This operation removes the transfer lock on the domain
        (specifically the `clientTransferProhibited` status) to allow
        domain transfers. We recommend you refrain from performing
        this action unless you intend to transfer the domain to a
        different registrar. Successful submission returns an
        operation ID that you can use to track the progress and
        completion of the action. If the request is not completed
        successfully, the domain registrant will be notified by email.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        """
        params = {'DomainName': domain_name, }
        return self.make_request(action='DisableDomainTransferLock',
                                 body=json.dumps(params))

    def enable_domain_transfer_lock(self, domain_name):
        """
        This operation sets the transfer lock on the domain
        (specifically the `clientTransferProhibited` status) to
        prevent domain transfers. Successful submission returns an
        operation ID that you can use to track the progress and
        completion of the action. If the request is not completed
        successfully, the domain registrant will be notified by email.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        """
        params = {'DomainName': domain_name, }
        return self.make_request(action='EnableDomainTransferLock',
                                 body=json.dumps(params))

    def get_domain_detail(self, domain_name):
        """
        This operation returns detailed information about the domain.
        The domain's contact information is also returned as part of
        the output.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        """
        params = {'DomainName': domain_name, }
        return self.make_request(action='GetDomainDetail',
                                 body=json.dumps(params))

    def get_operation_detail(self, operation_id):
        """
        This operation returns the current status of an operation that
        is not completed.

        :type operation_id: string
        :param operation_id: The identifier for the operation for which you
            want to get the status. Amazon Route 53 returned the identifier in
            the response to the original request.
        Type: String

        Default: None

        Required: Yes

        """
        params = {'OperationId': operation_id, }
        return self.make_request(action='GetOperationDetail',
                                 body=json.dumps(params))

    def list_domains(self, marker=None, max_items=None):
        """
        This operation returns all the domain names registered with
        Amazon Route 53 for the current AWS account.

        :type marker: string
        :param marker: For an initial request for a list of domains, omit this
            element. If the number of domains that are associated with the
            current AWS account is greater than the value that you specified
            for `MaxItems`, you can use `Marker` to return additional domains.
            Get the value of `NextPageMarker` from the previous response, and
            submit another request that includes the value of `NextPageMarker`
            in the `Marker` element.
        Type: String

        Default: None

        Constraints: The marker must match the value specified in the previous
            request.

        Required: No

        :type max_items: integer
        :param max_items: Number of domains to be returned.
        Type: Integer

        Default: 20

        Constraints: A numeral between 1 and 100.

        Required: No

        """
        params = {}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.make_request(action='ListDomains',
                                 body=json.dumps(params))

    def list_operations(self, marker=None, max_items=None):
        """
        This operation returns the operation IDs of operations that
        are not yet complete.

        :type marker: string
        :param marker: For an initial request for a list of operations, omit
            this element. If the number of operations that are not yet complete
            is greater than the value that you specified for `MaxItems`, you
            can use `Marker` to return additional operations. Get the value of
            `NextPageMarker` from the previous response, and submit another
            request that includes the value of `NextPageMarker` in the `Marker`
            element.
        Type: String

        Default: None

        Required: No

        :type max_items: integer
        :param max_items: Number of domains to be returned.
        Type: Integer

        Default: 20

        Constraints: A value between 1 and 100.

        Required: No

        """
        params = {}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.make_request(action='ListOperations',
                                 body=json.dumps(params))

    def register_domain(self, domain_name, duration_in_years, admin_contact,
                        registrant_contact, tech_contact, idn_lang_code=None,
                        auto_renew=None, privacy_protect_admin_contact=None,
                        privacy_protect_registrant_contact=None,
                        privacy_protect_tech_contact=None):
        """
        This operation registers a domain. Domains are registered by
        the AWS registrar partner, Gandi. For some top-level domains
        (TLDs), this operation requires extra parameters.

        When you register a domain, Amazon Route 53 does the
        following:


        + Creates a Amazon Route 53 hosted zone that has the same name
          as the domain. Amazon Route 53 assigns four name servers to
          your hosted zone and automatically updates your domain
          registration with the names of these name servers.
        + Enables autorenew, so your domain registration will renew
          automatically each year. We'll notify you in advance of the
          renewal date so you can choose whether to renew the
          registration.
        + Optionally enables privacy protection, so WHOIS queries
          return contact information for our registrar partner, Gandi,
          instead of the information you entered for registrant, admin,
          and tech contacts.
        + If registration is successful, returns an operation ID that
          you can use to track the progress and completion of the
          action. If the request is not completed successfully, the
          domain registrant is notified by email.
        + Charges your AWS account an amount based on the top-level
          domain. For more information, see `Amazon Route 53 Pricing`_.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        :type idn_lang_code: string
        :param idn_lang_code: Reserved for future use.

        :type duration_in_years: integer
        :param duration_in_years: The number of years the domain will be
            registered. Domains are registered for a minimum of one year. The
            maximum period depends on the top-level domain.
        Type: Integer

        Default: 1

        Valid values: Integer from 1 to 10

        Required: Yes

        :type auto_renew: boolean
        :param auto_renew: Indicates whether the domain will be automatically
            renewed ( `True`) or not ( `False`). Autorenewal only takes effect
            after the account is charged.
        Type: Boolean

        Valid values: `True` | `False`

        Default: `True`

        Required: No

        :type admin_contact: dict
        :param admin_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type registrant_contact: dict
        :param registrant_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type tech_contact: dict
        :param tech_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type privacy_protect_admin_contact: boolean
        :param privacy_protect_admin_contact: Whether you want to conceal
            contact information from WHOIS queries. If you specify true, WHOIS
            ("who is") queries will return contact information for our
            registrar partner, Gandi, instead of the contact information that
            you enter.
        Type: Boolean

        Default: `True`

        Valid values: `True` | `False`

        Required: No

        :type privacy_protect_registrant_contact: boolean
        :param privacy_protect_registrant_contact: Whether you want to conceal
            contact information from WHOIS queries. If you specify true, WHOIS
            ("who is") queries will return contact information for our
            registrar partner, Gandi, instead of the contact information that
            you enter.
        Type: Boolean

        Default: `True`

        Valid values: `True` | `False`

        Required: No

        :type privacy_protect_tech_contact: boolean
        :param privacy_protect_tech_contact: Whether you want to conceal
            contact information from WHOIS queries. If you specify true, WHOIS
            ("who is") queries will return contact information for our
            registrar partner, Gandi, instead of the contact information that
            you enter.
        Type: Boolean

        Default: `True`

        Valid values: `True` | `False`

        Required: No

        """
        params = {
            'DomainName': domain_name,
            'DurationInYears': duration_in_years,
            'AdminContact': admin_contact,
            'RegistrantContact': registrant_contact,
            'TechContact': tech_contact,
        }
        if idn_lang_code is not None:
            params['IdnLangCode'] = idn_lang_code
        if auto_renew is not None:
            params['AutoRenew'] = auto_renew
        if privacy_protect_admin_contact is not None:
            params['PrivacyProtectAdminContact'] = privacy_protect_admin_contact
        if privacy_protect_registrant_contact is not None:
            params['PrivacyProtectRegistrantContact'] = privacy_protect_registrant_contact
        if privacy_protect_tech_contact is not None:
            params['PrivacyProtectTechContact'] = privacy_protect_tech_contact
        return self.make_request(action='RegisterDomain',
                                 body=json.dumps(params))

    def retrieve_domain_auth_code(self, domain_name):
        """
        This operation returns the AuthCode for the domain. To
        transfer a domain to another registrar, you provide this value
        to the new registrar.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        """
        params = {'DomainName': domain_name, }
        return self.make_request(action='RetrieveDomainAuthCode',
                                 body=json.dumps(params))

    def transfer_domain(self, domain_name, duration_in_years, nameservers,
                        admin_contact, registrant_contact, tech_contact,
                        idn_lang_code=None, auth_code=None, auto_renew=None,
                        privacy_protect_admin_contact=None,
                        privacy_protect_registrant_contact=None,
                        privacy_protect_tech_contact=None):
        """
        This operation transfers a domain from another registrar to
        Amazon Route 53. Domains are registered by the AWS registrar,
        Gandi upon transfer.

        To transfer a domain, you need to meet all the domain transfer
        criteria, including the following:


        + You must supply nameservers to transfer a domain.
        + You must disable the domain transfer lock (if any) before
          transferring the domain.
        + A minimum of 60 days must have elapsed since the domain's
          registration or last transfer.


        We recommend you use the Amazon Route 53 as the DNS service
        for your domain. You can create a hosted zone in Amazon Route
        53 for your current domain before transferring your domain.

        Note that upon transfer, the domain duration is extended for a
        year if not otherwise specified. Autorenew is enabled by
        default.

        If the transfer is successful, this method returns an
        operation ID that you can use to track the progress and
        completion of the action. If the request is not completed
        successfully, the domain registrant will be notified by email.

        Transferring domains charges your AWS account an amount based
        on the top-level domain. For more information, see `Amazon
        Route 53 Pricing`_.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        :type idn_lang_code: string
        :param idn_lang_code: Reserved for future use.

        :type duration_in_years: integer
        :param duration_in_years: The number of years the domain will be
            registered. Domains are registered for a minimum of one year. The
            maximum period depends on the top-level domain.
        Type: Integer

        Default: 1

        Valid values: Integer from 1 to 10

        Required: Yes

        :type nameservers: list
        :param nameservers: Contains details for the host and glue IP
            addresses.
        Type: Complex

        Children: `GlueIps`, `Name`

        :type auth_code: string
        :param auth_code: The authorization code for the domain. You get this
            value from the current registrar.
        Type: String

        Required: Yes

        :type auto_renew: boolean
        :param auto_renew: Indicates whether the domain will be automatically
            renewed (true) or not (false). Autorenewal only takes effect after
            the account is charged.
        Type: Boolean

        Valid values: `True` | `False`

        Default: true

        Required: No

        :type admin_contact: dict
        :param admin_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type registrant_contact: dict
        :param registrant_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type tech_contact: dict
        :param tech_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type privacy_protect_admin_contact: boolean
        :param privacy_protect_admin_contact: Whether you want to conceal
            contact information from WHOIS queries. If you specify true, WHOIS
            ("who is") queries will return contact information for our
            registrar partner, Gandi, instead of the contact information that
            you enter.
        Type: Boolean

        Default: `True`

        Valid values: `True` | `False`

        Required: No

        :type privacy_protect_registrant_contact: boolean
        :param privacy_protect_registrant_contact: Whether you want to conceal
            contact information from WHOIS queries. If you specify true, WHOIS
            ("who is") queries will return contact information for our
            registrar partner, Gandi, instead of the contact information that
            you enter.
        Type: Boolean

        Default: `True`

        Valid values: `True` | `False`

        Required: No

        :type privacy_protect_tech_contact: boolean
        :param privacy_protect_tech_contact: Whether you want to conceal
            contact information from WHOIS queries. If you specify true, WHOIS
            ("who is") queries will return contact information for our
            registrar partner, Gandi, instead of the contact information that
            you enter.
        Type: Boolean

        Default: `True`

        Valid values: `True` | `False`

        Required: No

        """
        params = {
            'DomainName': domain_name,
            'DurationInYears': duration_in_years,
            'Nameservers': nameservers,
            'AdminContact': admin_contact,
            'RegistrantContact': registrant_contact,
            'TechContact': tech_contact,
        }
        if idn_lang_code is not None:
            params['IdnLangCode'] = idn_lang_code
        if auth_code is not None:
            params['AuthCode'] = auth_code
        if auto_renew is not None:
            params['AutoRenew'] = auto_renew
        if privacy_protect_admin_contact is not None:
            params['PrivacyProtectAdminContact'] = privacy_protect_admin_contact
        if privacy_protect_registrant_contact is not None:
            params['PrivacyProtectRegistrantContact'] = privacy_protect_registrant_contact
        if privacy_protect_tech_contact is not None:
            params['PrivacyProtectTechContact'] = privacy_protect_tech_contact
        return self.make_request(action='TransferDomain',
                                 body=json.dumps(params))

    def update_domain_contact(self, domain_name, admin_contact=None,
                              registrant_contact=None, tech_contact=None):
        """
        This operation updates the contact information for a
        particular domain. Information for at least one contact
        (registrant, administrator, or technical) must be supplied for
        update.

        If the update is successful, this method returns an operation
        ID that you can use to track the progress and completion of
        the action. If the request is not completed successfully, the
        domain registrant will be notified by email.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        :type admin_contact: dict
        :param admin_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type registrant_contact: dict
        :param registrant_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        :type tech_contact: dict
        :param tech_contact: Provides detailed contact information.
        Type: Complex

        Children: `FirstName`, `MiddleName`, `LastName`, `ContactType`,
            `OrganizationName`, `AddressLine1`, `AddressLine2`, `City`,
            `State`, `CountryCode`, `ZipCode`, `PhoneNumber`, `Email`, `Fax`,
            `ExtraParams`

        Required: Yes

        """
        params = {'DomainName': domain_name, }
        if admin_contact is not None:
            params['AdminContact'] = admin_contact
        if registrant_contact is not None:
            params['RegistrantContact'] = registrant_contact
        if tech_contact is not None:
            params['TechContact'] = tech_contact
        return self.make_request(action='UpdateDomainContact',
                                 body=json.dumps(params))

    def update_domain_contact_privacy(self, domain_name, admin_privacy=None,
                                      registrant_privacy=None,
                                      tech_privacy=None):
        """
        This operation updates the specified domain contact's privacy
        setting. When the privacy option is enabled, personal
        information such as postal or email address is hidden from the
        results of a public WHOIS query. The privacy services are
        provided by the AWS registrar, Gandi. For more information,
        see the `Gandi privacy features`_.

        This operation only affects the privacy of the specified
        contact type (registrant, administrator, or tech). Successful
        acceptance returns an operation ID that you can use with
        GetOperationDetail to track the progress and completion of the
        action. If the request is not completed successfully, the
        domain registrant will be notified by email.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        :type admin_privacy: boolean
        :param admin_privacy: Whether you want to conceal contact information
            from WHOIS queries. If you specify true, WHOIS ("who is") queries
            will return contact information for our registrar partner, Gandi,
            instead of the contact information that you enter.
        Type: Boolean

        Default: None

        Valid values: `True` | `False`

        Required: No

        :type registrant_privacy: boolean
        :param registrant_privacy: Whether you want to conceal contact
            information from WHOIS queries. If you specify true, WHOIS ("who
            is") queries will return contact information for our registrar
            partner, Gandi, instead of the contact information that you enter.
        Type: Boolean

        Default: None

        Valid values: `True` | `False`

        Required: No

        :type tech_privacy: boolean
        :param tech_privacy: Whether you want to conceal contact information
            from WHOIS queries. If you specify true, WHOIS ("who is") queries
            will return contact information for our registrar partner, Gandi,
            instead of the contact information that you enter.
        Type: Boolean

        Default: None

        Valid values: `True` | `False`

        Required: No

        """
        params = {'DomainName': domain_name, }
        if admin_privacy is not None:
            params['AdminPrivacy'] = admin_privacy
        if registrant_privacy is not None:
            params['RegistrantPrivacy'] = registrant_privacy
        if tech_privacy is not None:
            params['TechPrivacy'] = tech_privacy
        return self.make_request(action='UpdateDomainContactPrivacy',
                                 body=json.dumps(params))

    def update_domain_nameservers(self, domain_name, nameservers):
        """
        This operation replaces the current set of name servers for
        the domain with the specified set of name servers. If you use
        Amazon Route 53 as your DNS service, specify the four name
        servers in the delegation set for the hosted zone for the
        domain.

        If successful, this operation returns an operation ID that you
        can use to track the progress and completion of the action. If
        the request is not completed successfully, the domain
        registrant will be notified by email.

        :type domain_name: string
        :param domain_name: The name of a domain.
        Type: String

        Default: None

        Constraints: The domain name can contain only the letters a through z,
            the numbers 0 through 9, and hyphen (-). Internationalized Domain
            Names are not supported.

        Required: Yes

        :type nameservers: list
        :param nameservers: A list of new name servers for the domain.
        Type: Complex

        Children: `Name`, `GlueIps`

        Required: Yes

        """
        params = {
            'DomainName': domain_name,
            'Nameservers': nameservers,
        }
        return self.make_request(action='UpdateDomainNameservers',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

