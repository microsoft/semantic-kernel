# Copyright (c) 2011 Blue Pines Technologies LLC, Brad Carleton
# www.bluepines.org
# Copyright (c) 2012 42 Lines Inc., Jim Browne
# All rights reserved.
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

default_ttl = 60

import copy
from boto.exception import TooManyRecordsException
from boto.route53.record import ResourceRecordSets
from boto.route53.status import Status


class Zone(object):
    """
    A Route53 Zone.

    :ivar route53connection: A :class:`boto.route53.connection.Route53Connection` connection
    :ivar id: The ID of the hosted zone
    """
    def __init__(self, route53connection, zone_dict):
        self.route53connection = route53connection
        for key in zone_dict:
            if key == 'Id':
                self.id = zone_dict['Id'].replace('/hostedzone/', '')
            else:
                self.__setattr__(key.lower(), zone_dict[key])

    def __repr__(self):
        return '<Zone:%s>' % self.name

    def _commit(self, changes):
        """
        Commit a set of changes and return the ChangeInfo portion of
        the response.

        :type changes: ResourceRecordSets
        :param changes: changes to be committed
        """
        response = changes.commit()
        return response['ChangeResourceRecordSetsResponse']['ChangeInfo']

    def _new_record(self, changes, resource_type, name, value, ttl, identifier,
                    comment=""):
        """
        Add a CREATE change record to an existing ResourceRecordSets

        :type changes: ResourceRecordSets
        :param changes: change set to append to

        :type name: str
        :param name: The name of the resource record you want to
            perform the action on.

        :type resource_type: str
        :param resource_type: The DNS record type

        :param value: Appropriate value for resource_type

        :type ttl: int
        :param ttl: The resource record cache time to live (TTL), in seconds.

        :type identifier: tuple
        :param identifier: A tuple for setting WRR or LBR attributes.  Valid
           forms are:

           * (str, int): WRR record [e.g. ('foo',10)]
           * (str, str): LBR record [e.g. ('foo','us-east-1')

        :type comment: str
        :param comment: A comment that will be stored with the change.
        """
        weight = None
        region = None
        if identifier is not None:
            try:
                int(identifier[1])
                weight = identifier[1]
                identifier = identifier[0]
            except:
                region = identifier[1]
                identifier = identifier[0]
        change = changes.add_change("CREATE", name, resource_type, ttl,
                                    identifier=identifier, weight=weight,
                                    region=region)
        if type(value) in [list, tuple, set]:
            for record in value:
                change.add_value(record)
        else:
            change.add_value(value)

    def add_record(self, resource_type, name, value, ttl=60, identifier=None,
                   comment=""):
        """
        Add a new record to this Zone.  See _new_record for parameter
        documentation.  Returns a Status object.
        """
        changes = ResourceRecordSets(self.route53connection, self.id, comment)
        self._new_record(changes, resource_type, name, value, ttl, identifier,
                         comment)
        return Status(self.route53connection, self._commit(changes))

    def update_record(self, old_record, new_value, new_ttl=None,
                      new_identifier=None, comment=""):
        """
        Update an existing record in this Zone.  Returns a Status object.

        :type old_record: ResourceRecord
        :param old_record: A ResourceRecord (e.g. returned by find_records)

        See _new_record for additional parameter documentation.
        """
        new_ttl = new_ttl or default_ttl
        record = copy.copy(old_record)
        changes = ResourceRecordSets(self.route53connection, self.id, comment)
        changes.add_change_record("DELETE", record)
        self._new_record(changes, record.type, record.name,
                         new_value, new_ttl, new_identifier, comment)
        return Status(self.route53connection, self._commit(changes))

    def delete_record(self, record, comment=""):
        """
        Delete one or more records from this Zone.  Returns a Status object.

        :param record: A ResourceRecord (e.g. returned by
           find_records) or list, tuple, or set of ResourceRecords.

        :type comment: str
        :param comment: A comment that will be stored with the change.
        """
        changes = ResourceRecordSets(self.route53connection, self.id, comment)
        if type(record) in [list, tuple, set]:
            for r in record:
                changes.add_change_record("DELETE", r)
        else:
            changes.add_change_record("DELETE", record)
        return Status(self.route53connection, self._commit(changes))

    def add_cname(self, name, value, ttl=None, identifier=None, comment=""):
        """
        Add a new CNAME record to this Zone.  See _new_record for
        parameter documentation.  Returns a Status object.
        """
        ttl = ttl or default_ttl
        name = self.route53connection._make_qualified(name)
        value = self.route53connection._make_qualified(value)
        return self.add_record(resource_type='CNAME',
                               name=name,
                               value=value,
                               ttl=ttl,
                               identifier=identifier,
                               comment=comment)

    def add_a(self, name, value, ttl=None, identifier=None, comment=""):
        """
        Add a new A record to this Zone.  See _new_record for
        parameter documentation.  Returns a Status object.
        """
        ttl = ttl or default_ttl
        name = self.route53connection._make_qualified(name)
        return self.add_record(resource_type='A',
                               name=name,
                               value=value,
                               ttl=ttl,
                               identifier=identifier,
                               comment=comment)

    def add_mx(self, name, records, ttl=None, identifier=None, comment=""):
        """
        Add a new MX record to this Zone.  See _new_record for
        parameter documentation.  Returns a Status object.
        """
        ttl = ttl or default_ttl
        records = self.route53connection._make_qualified(records)
        return self.add_record(resource_type='MX',
                               name=name,
                               value=records,
                               ttl=ttl,
                               identifier=identifier,
                               comment=comment)

    def find_records(self, name, type, desired=1, all=False, identifier=None):
        """
        Search this Zone for records that match given parameters.
        Returns None if no results, a ResourceRecord if one result, or
        a ResourceRecordSets if more than one result.

        :type name: str
        :param name: The name of the records should match this parameter

        :type type: str
        :param type: The type of the records should match this parameter

        :type desired: int
        :param desired: The number of desired results.  If the number of
           matching records in the Zone exceeds the value of this parameter,
           throw TooManyRecordsException

        :type all: Boolean
        :param all: If true return all records that match name, type, and
          identifier parameters

        :type identifier: Tuple
        :param identifier: A tuple specifying WRR or LBR attributes.  Valid
           forms are:

           * (str, int): WRR record [e.g. ('foo',10)]
           * (str, str): LBR record [e.g. ('foo','us-east-1')

        """
        name = self.route53connection._make_qualified(name)
        returned = self.route53connection.get_all_rrsets(self.id, name=name,
                                                         type=type)

        # name/type for get_all_rrsets sets the starting record; they
        # are not a filter
        results = []
        for r in returned:
            if r.name == name and r.type == type:
                results.append(r)
            # Is at the end of the list of matched records. No need to continue
            # since the records are sorted by name and type.
            else:
                break

        weight = None
        region = None
        if identifier is not None:
            try:
                int(identifier[1])
                weight = identifier[1]
            except:
                region = identifier[1]

        if weight is not None:
            results = [r for r in results if (r.weight == weight and
                                              r.identifier == identifier[0])]
        if region is not None:
            results = [r for r in results if (r.region == region and
                                              r.identifier == identifier[0])]

        if ((not all) and (len(results) > desired)):
            message = "Search: name %s type %s" % (name, type)
            message += "\nFound: "
            message += ", ".join(["%s %s %s" % (r.name, r.type, r.to_print())
                                  for r in results])
            raise TooManyRecordsException(message)
        elif len(results) > 1:
            return results
        elif len(results) == 1:
            return results[0]
        else:
            return None

    def get_cname(self, name, all=False):
        """
        Search this Zone for CNAME records that match name.

        Returns a ResourceRecord.

        If there is more than one match return all as a
        ResourceRecordSets if all is True, otherwise throws
        TooManyRecordsException.
        """
        return self.find_records(name, 'CNAME', all=all)

    def get_a(self, name, all=False):
        """
        Search this Zone for A records that match name.

        Returns a ResourceRecord.

        If there is more than one match return all as a
        ResourceRecordSets if all is True, otherwise throws
        TooManyRecordsException.
        """
        return self.find_records(name, 'A', all=all)

    def get_mx(self, name, all=False):
        """
        Search this Zone for MX records that match name.

        Returns a ResourceRecord.

        If there is more than one match return all as a
        ResourceRecordSets if all is True, otherwise throws
        TooManyRecordsException.
        """
        return self.find_records(name, 'MX', all=all)

    def update_cname(self, name, value, ttl=None, identifier=None, comment=""):
        """
        Update the given CNAME record in this Zone to a new value, ttl,
        and identifier.  Returns a Status object.

        Will throw TooManyRecordsException is name, value does not match
        a single record.
        """
        name = self.route53connection._make_qualified(name)
        value = self.route53connection._make_qualified(value)
        old_record = self.get_cname(name)
        ttl = ttl or old_record.ttl
        return self.update_record(old_record,
                                  new_value=value,
                                  new_ttl=ttl,
                                  new_identifier=identifier,
                                  comment=comment)

    def update_a(self, name, value, ttl=None, identifier=None, comment=""):
        """
        Update the given A record in this Zone to a new value, ttl,
        and identifier.  Returns a Status object.

        Will throw TooManyRecordsException is name, value does not match
        a single record.
        """
        name = self.route53connection._make_qualified(name)
        old_record = self.get_a(name)
        ttl = ttl or old_record.ttl
        return self.update_record(old_record,
                                  new_value=value,
                                  new_ttl=ttl,
                                  new_identifier=identifier,
                                  comment=comment)

    def update_mx(self, name, value, ttl=None, identifier=None, comment=""):
        """
        Update the given MX record in this Zone to a new value, ttl,
        and identifier.  Returns a Status object.

        Will throw TooManyRecordsException is name, value does not match
        a single record.
        """
        name = self.route53connection._make_qualified(name)
        value = self.route53connection._make_qualified(value)
        old_record = self.get_mx(name)
        ttl = ttl or old_record.ttl
        return self.update_record(old_record,
                                  new_value=value,
                                  new_ttl=ttl,
                                  new_identifier=identifier,
                                  comment=comment)

    def delete_cname(self, name, identifier=None, all=False):
        """
        Delete a CNAME record matching name and identifier from
        this Zone.  Returns a Status object.

        If there is more than one match delete all matching records if
        all is True, otherwise throws TooManyRecordsException.
        """
        name = self.route53connection._make_qualified(name)
        record = self.find_records(name, 'CNAME', identifier=identifier,
                                   all=all)
        return self.delete_record(record)

    def delete_a(self, name, identifier=None, all=False):
        """
        Delete an A record matching name and identifier from this
        Zone.  Returns a Status object.

        If there is more than one match delete all matching records if
        all is True, otherwise throws TooManyRecordsException.
        """
        name = self.route53connection._make_qualified(name)
        record = self.find_records(name, 'A', identifier=identifier,
                                   all=all)
        return self.delete_record(record)

    def delete_mx(self, name, identifier=None, all=False):
        """
        Delete an MX record matching name and identifier from this
        Zone.  Returns a Status object.

        If there is more than one match delete all matching records if
        all is True, otherwise throws TooManyRecordsException.
        """
        name = self.route53connection._make_qualified(name)
        record = self.find_records(name, 'MX', identifier=identifier,
                                   all=all)
        return self.delete_record(record)

    def get_records(self):
        """
        Return a ResourceRecordsSets for all of the records in this zone.
        """
        return self.route53connection.get_all_rrsets(self.id)

    def delete(self):
        """
        Request that this zone be deleted by Amazon.
        """
        self.route53connection.delete_hosted_zone(self.id)

    def get_nameservers(self):
        """ Get the list of nameservers for this zone."""
        ns = self.find_records(self.name, 'NS')
        if ns is not None:
            ns = ns.resource_records
        return ns
