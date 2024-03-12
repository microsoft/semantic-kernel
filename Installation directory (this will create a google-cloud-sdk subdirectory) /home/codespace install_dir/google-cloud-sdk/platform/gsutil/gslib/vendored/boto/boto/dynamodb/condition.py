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
#

from boto.dynamodb.types import dynamize_value


class Condition(object):
    """
    Base class for conditions.  Doesn't do a darn thing but allows
    is to test if something is a Condition instance or not.
    """

    def __eq__(self, other):
        if isinstance(other, Condition):
            return self.to_dict() == other.to_dict()

class ConditionNoArgs(Condition):
    """
    Abstract class for Conditions that require no arguments, such
    as NULL or NOT_NULL.
    """

    def __repr__(self):
        return '%s' % self.__class__.__name__

    def to_dict(self):
        return {'ComparisonOperator': self.__class__.__name__}


class ConditionOneArg(Condition):
    """
    Abstract class for Conditions that require a single argument
    such as EQ or NE.
    """

    def __init__(self, v1):
        self.v1 = v1

    def __repr__(self):
        return '%s:%s' % (self.__class__.__name__, self.v1)

    def to_dict(self):
        return {'AttributeValueList': [dynamize_value(self.v1)],
                'ComparisonOperator': self.__class__.__name__}


class ConditionTwoArgs(Condition):
    """
    Abstract class for Conditions that require two arguments.
    The only example of this currently is BETWEEN.
    """

    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, self.v1, self.v2)

    def to_dict(self):
        values = (self.v1, self.v2)
        return {'AttributeValueList': [dynamize_value(v) for v in values],
                'ComparisonOperator': self.__class__.__name__}


class ConditionSeveralArgs(Condition):
    """
    Abstract class for conditions that require several argument (ex: IN).
    """

    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return '{0}({1})'.format(self.__class__.__name__,
                               ', '.join(self.values))

    def to_dict(self):
        return {'AttributeValueList': [dynamize_value(v) for v in self.values],
                'ComparisonOperator': self.__class__.__name__}


class EQ(ConditionOneArg):

    pass


class NE(ConditionOneArg):

    pass


class LE(ConditionOneArg):

    pass


class LT(ConditionOneArg):

    pass


class GE(ConditionOneArg):

    pass


class GT(ConditionOneArg):

    pass


class NULL(ConditionNoArgs):

    pass


class NOT_NULL(ConditionNoArgs):

    pass


class CONTAINS(ConditionOneArg):

    pass


class NOT_CONTAINS(ConditionOneArg):

    pass


class BEGINS_WITH(ConditionOneArg):

    pass


class IN(ConditionSeveralArgs):

    pass


class BEGINS_WITH(ConditionOneArg):

    pass


class BETWEEN(ConditionTwoArgs):

    pass
