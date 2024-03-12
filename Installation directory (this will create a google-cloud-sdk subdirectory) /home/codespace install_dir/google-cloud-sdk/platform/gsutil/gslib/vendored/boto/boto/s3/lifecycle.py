# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.compat import six

class Rule(object):
    """
    A Lifecycle rule for an S3 bucket.

    :ivar id: Unique identifier for the rule. The value cannot be longer
        than 255 characters. This value is optional. The server will
        generate a unique value for the rule if no value is provided.

    :ivar prefix: Prefix identifying one or more objects to which the
        rule applies. If prefix is not provided, Boto generates a default
        prefix which will match all objects.

    :ivar status: If 'Enabled', the rule is currently being applied.
        If 'Disabled', the rule is not currently being applied.

    :ivar expiration: An instance of `Expiration`. This indicates
        the lifetime of the objects that are subject to the rule.

    :ivar transition: An instance of `Transition`.  This indicates
        when to transition to a different storage class.

    """
    def __init__(self, id=None, prefix=None, status=None, expiration=None,
                 transition=None):
        self.id = id
        self.prefix = '' if prefix is None else prefix
        self.status = status
        if isinstance(expiration, six.integer_types):
            # retain backwards compatibility???
            self.expiration = Expiration(days=expiration)
        else:
            # None or object
            self.expiration = expiration

        # retain backwards compatibility
        if isinstance(transition, Transition):
            self.transition = Transitions()
            self.transition.append(transition)
        elif transition:
            self.transition = transition
        else:
            self.transition = Transitions()

    def __repr__(self):
        return '<Rule: %s>' % self.id

    def startElement(self, name, attrs, connection):
        if name == 'Transition':
            return self.transition
        elif name == 'Expiration':
            self.expiration = Expiration()
            return self.expiration
        return None

    def endElement(self, name, value, connection):
        if name == 'ID':
            self.id = value
        elif name == 'Prefix':
            self.prefix = value
        elif name == 'Status':
            self.status = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = '<Rule>'
        if self.id is not None:
            s += '<ID>%s</ID>' % self.id
        s += '<Prefix>%s</Prefix>' % self.prefix
        s += '<Status>%s</Status>' % self.status
        if self.expiration is not None:
            s += self.expiration.to_xml()
        if self.transition is not None:
            s += self.transition.to_xml()
        s += '</Rule>'
        return s

class Expiration(object):
    """
    When an object will expire.

    :ivar days: The number of days until the object expires

    :ivar date: The date when the object will expire. Must be
        in ISO 8601 format.
    """
    def __init__(self, days=None, date=None):
        self.days = days
        self.date = date

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Days':
            self.days = int(value)
        elif name == 'Date':
            self.date = value

    def __repr__(self):
        if self.days is None:
            how_long = "on: %s" % self.date
        else:
            how_long = "in: %s days" % self.days
        return '<Expiration: %s>' % how_long

    def to_xml(self):
        s = '<Expiration>'
        if self.days is not None:
            s += '<Days>%s</Days>' % self.days
        elif self.date is not None:
            s += '<Date>%s</Date>' % self.date
        s += '</Expiration>'
        return s

class Transition(object):
    """
    A transition to a different storage class.

    :ivar days: The number of days until the object should be moved.

    :ivar date: The date when the object should be moved.  Should be
        in ISO 8601 format.

    :ivar storage_class: The storage class to transition to.  Valid
        values are GLACIER, STANDARD_IA.
    """
    def __init__(self, days=None, date=None, storage_class=None):
        self.days = days
        self.date = date
        self.storage_class = storage_class

    def __repr__(self):
        if self.days is None:
            how_long = "on: %s" % self.date
        else:
            how_long = "in: %s days" % self.days
        return '<Transition: %s, %s>' % (how_long, self.storage_class)

    def to_xml(self):
        s = '<Transition>'
        s += '<StorageClass>%s</StorageClass>' % self.storage_class
        if self.days is not None:
            s += '<Days>%s</Days>' % self.days
        elif self.date is not None:
            s += '<Date>%s</Date>' % self.date
        s += '</Transition>'
        return s

class Transitions(list):
    """
    A container for the transitions associated with a Lifecycle's Rule configuration.
    """
    def __init__(self):
        self.transition_properties = 3
        self.current_transition_property = 1
        self.temp_days = None
        self.temp_date = None
        self.temp_storage_class = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Days':
            self.temp_days = int(value)
        elif name == 'Date':
            self.temp_date = value
        elif name == 'StorageClass':
            self.temp_storage_class = value

        # the XML does not contain a <Transitions> tag
        # but rather N number of <Transition> tags not
        # structured in any sort of hierarchy.
        if self.current_transition_property == self.transition_properties:
            self.append(Transition(self.temp_days, self.temp_date, self.temp_storage_class))
            self.temp_days = self.temp_date = self.temp_storage_class = None
            self.current_transition_property = 1
        else:
            self.current_transition_property += 1

    def to_xml(self):
        """
        Returns a string containing the XML version of the Lifecycle
        configuration as defined by S3.
        """
        s = ''
        for transition in self:
            s += transition.to_xml()
        return s

    def add_transition(self, days=None, date=None, storage_class=None):
        """
        Add a transition to this Lifecycle configuration.  This only adds
        the rule to the local copy.  To install the new rule(s) on
        the bucket, you need to pass this Lifecycle config object
        to the configure_lifecycle method of the Bucket object.

        :ivar days: The number of days until the object should be moved.

        :ivar date: The date when the object should be moved.  Should be
            in ISO 8601 format.

        :ivar storage_class: The storage class to transition to.  Valid
            values are GLACIER, STANDARD_IA.
        """
        transition = Transition(days, date, storage_class)
        self.append(transition)

    def __first_or_default(self, prop):
        for transition in self:
            return getattr(transition, prop)
        return None

    # maintain backwards compatibility so that we can continue utilizing
    # 'rule.transition.days' syntax
    @property
    def days(self):
        return self.__first_or_default('days')

    @property
    def date(self):
        return self.__first_or_default('date')

    @property
    def storage_class(self):
        return self.__first_or_default('storage_class')


class Lifecycle(list):
    """
    A container for the rules associated with a Lifecycle configuration.
    """

    def startElement(self, name, attrs, connection):
        if name == 'Rule':
            rule = Rule()
            self.append(rule)
            return rule
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

    def to_xml(self):
        """
        Returns a string containing the XML version of the Lifecycle
        configuration as defined by S3.
        """
        s = '<?xml version="1.0" encoding="UTF-8"?>'
        s += '<LifecycleConfiguration>'
        for rule in self:
            s += rule.to_xml()
        s += '</LifecycleConfiguration>'
        return s

    def add_rule(self, id=None, prefix='', status='Enabled',
                 expiration=None, transition=None):
        """
        Add a rule to this Lifecycle configuration.  This only adds
        the rule to the local copy.  To install the new rule(s) on
        the bucket, you need to pass this Lifecycle config object
        to the configure_lifecycle method of the Bucket object.

        :type id: str
        :param id: Unique identifier for the rule. The value cannot be longer
            than 255 characters. This value is optional. The server will
            generate a unique value for the rule if no value is provided.

        :type prefix: str
        :iparam prefix: Prefix identifying one or more objects to which the
            rule applies.

        :type status: str
        :param status: If 'Enabled', the rule is currently being applied.
            If 'Disabled', the rule is not currently being applied.

        :type expiration: int
        :param expiration: Indicates the lifetime, in days, of the objects
            that are subject to the rule. The value must be a non-zero
            positive integer. A Expiration object instance is also perfect.

        :type transition: Transitions
        :param transition: Indicates when an object transitions to a
            different storage class. 
        """
        rule = Rule(id, prefix, status, expiration, transition)
        self.append(rule)
