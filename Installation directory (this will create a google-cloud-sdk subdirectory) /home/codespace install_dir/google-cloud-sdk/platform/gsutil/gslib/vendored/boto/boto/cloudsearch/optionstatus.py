# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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

import time
from boto.compat import json


class OptionStatus(dict):
    """
    Presents a combination of status field (defined below) which are
    accessed as attributes and option values which are stored in the
    native Python dictionary.  In this class, the option values are
    merged from a JSON object that is stored as the Option part of
    the object.

    :ivar domain_name: The name of the domain this option is associated with.
    :ivar create_date: A timestamp for when this option was created.
    :ivar state: The state of processing a change to an option.
        Possible values:

        * RequiresIndexDocuments: the option's latest value will not
          be visible in searches until IndexDocuments has been called
          and indexing is complete.
        * Processing: the option's latest value is not yet visible in
          all searches but is in the process of being activated.
        * Active: the option's latest value is completely visible.

    :ivar update_date: A timestamp for when this option was updated.
    :ivar update_version: A unique integer that indicates when this
        option was last updated.
    """

    def __init__(self, domain, data=None, refresh_fn=None, save_fn=None):
        self.domain = domain
        self.refresh_fn = refresh_fn
        self.save_fn = save_fn
        self.refresh(data)

    def _update_status(self, status):
        self.creation_date = status['creation_date']
        self.status = status['state']
        self.update_date = status['update_date']
        self.update_version = int(status['update_version'])

    def _update_options(self, options):
        if options:
            self.update(json.loads(options))

    def refresh(self, data=None):
        """
        Refresh the local state of the object.  You can either pass
        new state data in as the parameter ``data`` or, if that parameter
        is omitted, the state data will be retrieved from CloudSearch.
        """
        if not data:
            if self.refresh_fn:
                data = self.refresh_fn(self.domain.name)
        if data:
            self._update_status(data['status'])
            self._update_options(data['options'])

    def to_json(self):
        """
        Return the JSON representation of the options as a string.
        """
        return json.dumps(self)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'CreationDate':
            self.created = value
        elif name == 'State':
            self.state = value
        elif name == 'UpdateDate':
            self.updated = value
        elif name == 'UpdateVersion':
            self.update_version = int(value)
        elif name == 'Options':
            self.update_from_json_doc(value)
        else:
            setattr(self, name, value)

    def save(self):
        """
        Write the current state of the local object back to the
        CloudSearch service.
        """
        if self.save_fn:
            data = self.save_fn(self.domain.name, self.to_json())
            self.refresh(data)

    def wait_for_state(self, state):
        """
        Performs polling of CloudSearch to wait for the ``state``
        of this object to change to the provided state.
        """
        while self.state != state:
            time.sleep(5)
            self.refresh()


class IndexFieldStatus(OptionStatus):

    def _update_options(self, options):
        self.update(options)

    def save(self):
        pass


class RankExpressionStatus(IndexFieldStatus):

    pass

class ServicePoliciesStatus(OptionStatus):

    def new_statement(self, arn, ip):
        """
        Returns a new policy statement that will allow
        access to the service described by ``arn`` by the
        ip specified in ``ip``.

        :type arn: string
        :param arn: The Amazon Resource Notation identifier for the
            service you wish to provide access to.  This would be
            either the search service or the document service.

        :type ip: string
        :param ip: An IP address or CIDR block you wish to grant access
            to.
        """
        return {
                    "Effect":"Allow",
                    "Action":"*",  # Docs say use GET, but denies unless *
                    "Resource": arn,
                    "Condition": {
                        "IpAddress": {
                            "aws:SourceIp": [ip]
                            }
                        }
                    }

    def _allow_ip(self, arn, ip):
        if 'Statement' not in self:
            s = self.new_statement(arn, ip)
            self['Statement'] = [s]
            self.save()
        else:
            add_statement = True
            for statement in self['Statement']:
                if statement['Resource'] == arn:
                    for condition_name in statement['Condition']:
                        if condition_name == 'IpAddress':
                            add_statement = False
                            condition = statement['Condition'][condition_name]
                            if ip not in condition['aws:SourceIp']:
                                condition['aws:SourceIp'].append(ip)

            if add_statement:
                s = self.new_statement(arn, ip)
                self['Statement'].append(s)
            self.save()

    def allow_search_ip(self, ip):
        """
        Add the provided ip address or CIDR block to the list of
        allowable address for the search service.

        :type ip: string
        :param ip: An IP address or CIDR block you wish to grant access
            to.
        """
        arn = self.domain.search_service_arn
        self._allow_ip(arn, ip)

    def allow_doc_ip(self, ip):
        """
        Add the provided ip address or CIDR block to the list of
        allowable address for the document service.

        :type ip: string
        :param ip: An IP address or CIDR block you wish to grant access
            to.
        """
        arn = self.domain.doc_service_arn
        self._allow_ip(arn, ip)

    def _disallow_ip(self, arn, ip):
        if 'Statement' not in self:
            return
        need_update = False
        for statement in self['Statement']:
            if statement['Resource'] == arn:
                for condition_name in statement['Condition']:
                    if condition_name == 'IpAddress':
                        condition = statement['Condition'][condition_name]
                        if ip in condition['aws:SourceIp']:
                            condition['aws:SourceIp'].remove(ip)
                            need_update = True
        if need_update:
            self.save()

    def disallow_search_ip(self, ip):
        """
        Remove the provided ip address or CIDR block from the list of
        allowable address for the search service.

        :type ip: string
        :param ip: An IP address or CIDR block you wish to grant access
            to.
        """
        arn = self.domain.search_service_arn
        self._disallow_ip(arn, ip)

    def disallow_doc_ip(self, ip):
        """
        Remove the provided ip address or CIDR block from the list of
        allowable address for the document service.

        :type ip: string
        :param ip: An IP address or CIDR block you wish to grant access
            to.
        """
        arn = self.domain.doc_service_arn
        self._disallow_ip(arn, ip)
