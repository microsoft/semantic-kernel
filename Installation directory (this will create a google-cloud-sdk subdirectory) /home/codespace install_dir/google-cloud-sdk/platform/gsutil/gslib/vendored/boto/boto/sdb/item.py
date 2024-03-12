# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
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

import base64

class Item(dict):
    """
    A ``dict`` sub-class that serves as an object representation of a
    SimpleDB item. An item in SDB is similar to a row in a relational
    database. Items belong to a :py:class:`Domain <boto.sdb.domain.Domain>`,
    which is similar to a table in a relational database.

    The keys on instances of this object correspond to attributes that are
    stored on the SDB item.

    .. tip:: While it is possible to instantiate this class directly, you may
        want to use the convenience methods on :py:class:`boto.sdb.domain.Domain`
        for that purpose. For example, :py:meth:`boto.sdb.domain.Domain.get_item`.
    """
    def __init__(self, domain, name='', active=False):
        """
        :type domain: :py:class:`boto.sdb.domain.Domain`
        :param domain: The domain that this item belongs to.

        :param str name: The name of this item. This name will be used when
            querying for items using methods like
            :py:meth:`boto.sdb.domain.Domain.get_item`
        """
        dict.__init__(self)
        self.domain = domain
        self.name = name
        self.active = active
        self.request_id = None
        self.encoding = None
        self.in_attribute = False
        self.converter = self.domain.connection.converter

    def startElement(self, name, attrs, connection):
        if name == 'Attribute':
            self.in_attribute = True
        self.encoding = attrs.get('encoding', None)
        return None

    def decode_value(self, value):
        if self.encoding == 'base64':
            self.encoding = None
            return base64.decodestring(value)
        else:
            return value

    def endElement(self, name, value, connection):
        if name == 'ItemName':
            self.name = self.decode_value(value)
        elif name == 'Name':
            if self.in_attribute:
                self.last_key = self.decode_value(value)
            else:
                self.name = self.decode_value(value)
        elif name == 'Value':
            if self.last_key in self:
                if not isinstance(self[self.last_key], list):
                    self[self.last_key] = [self[self.last_key]]
                value = self.decode_value(value)
                if self.converter:
                    value = self.converter.decode(value)
                self[self.last_key].append(value)
            else:
                value = self.decode_value(value)
                if self.converter:
                    value = self.converter.decode(value)
                self[self.last_key] = value
        elif name == 'BoxUsage':
            try:
                connection.box_usage += float(value)
            except:
                pass
        elif name == 'RequestId':
            self.request_id = value
        elif name == 'Attribute':
            self.in_attribute = False
        else:
            setattr(self, name, value)

    def load(self):
        """
        Loads or re-loads this item's attributes from SDB.

        .. warning::
            If you have changed attribute values on an Item instance,
            this method will over-write the values if they are different in
            SDB. For any local attributes that don't yet exist in SDB,
            they will be safe.
        """
        self.domain.get_attributes(self.name, item=self)

    def save(self, replace=True):
        """
        Saves this item to SDB.

        :param bool replace: If ``True``, delete any attributes on the remote
            SDB item that have a ``None`` value on this object.
        """
        self.domain.put_attributes(self.name, self, replace)
        # Delete any attributes set to "None"
        if replace:
            del_attrs = []
            for name in self:
                if self[name] is None:
                    del_attrs.append(name)
            if len(del_attrs) > 0:
                self.domain.delete_attributes(self.name, del_attrs)

    def add_value(self, key, value):
        """
        Helps set or add to attributes on this item. If you are adding a new
        attribute that has yet to be set, it will simply create an attribute
        named ``key`` with your given ``value`` as its value. If you are
        adding a value to an existing attribute, this method will convert the
        attribute to a list (if it isn't already) and append your new value
        to said list.

        For clarification, consider the following interactive session:

        .. code-block:: python

            >>> item = some_domain.get_item('some_item')
            >>> item.has_key('some_attr')
            False
            >>> item.add_value('some_attr', 1)
            >>> item['some_attr']
            1
            >>> item.add_value('some_attr', 2)
            >>> item['some_attr']
            [1, 2]

        :param str key: The attribute to add a value to.
        :param object value: The value to set or append to the attribute.
        """
        if key in self:
            # We already have this key on the item.
            if not isinstance(self[key], list):
                # The key isn't already a list, take its current value and
                # convert it to a list with the only member being the
                # current value.
                self[key] = [self[key]]
            # Add the new value to the list.
            self[key].append(value)
        else:
            # This is a new attribute, just set it.
            self[key] = value

    def delete(self):
        """
        Deletes this item in SDB.

        .. note:: This local Python object remains in its current state
            after deletion, this only deletes the remote item in SDB.
        """
        self.domain.delete_item(self)
