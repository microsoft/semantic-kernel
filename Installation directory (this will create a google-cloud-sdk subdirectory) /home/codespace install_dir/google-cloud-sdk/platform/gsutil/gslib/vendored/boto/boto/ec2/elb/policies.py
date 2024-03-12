# Copyright (c) 2010 Reza Lotun http://reza.lotun.name
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

from boto.resultset import ResultSet


class AppCookieStickinessPolicy(object):
    def __init__(self, connection=None):
        self.cookie_name = None
        self.policy_name = None

    def __repr__(self):
        return 'AppCookieStickiness(%s, %s)' % (self.policy_name,
                                                self.cookie_name)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'CookieName':
            self.cookie_name = value
        elif name == 'PolicyName':
            self.policy_name = value


class LBCookieStickinessPolicy(object):
    def __init__(self, connection=None):
        self.policy_name = None
        self.cookie_expiration_period = None

    def __repr__(self):
        return 'LBCookieStickiness(%s, %s)' % (self.policy_name,
                                               self.cookie_expiration_period)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'CookieExpirationPeriod':
            self.cookie_expiration_period = value
        elif name == 'PolicyName':
            self.policy_name = value


class OtherPolicy(object):
    def __init__(self, connection=None):
        self.policy_name = None

    def __repr__(self):
        return 'OtherPolicy(%s)' % (self.policy_name)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        self.policy_name = value


class Policies(object):
    """
    ELB Policies
    """
    def __init__(self, connection=None):
        self.connection = connection
        self.app_cookie_stickiness_policies = None
        self.lb_cookie_stickiness_policies = None
        self.other_policies = None

    def __repr__(self):
        app = 'AppCookieStickiness%s' % self.app_cookie_stickiness_policies
        lb = 'LBCookieStickiness%s' % self.lb_cookie_stickiness_policies
        other = 'Other%s' % self.other_policies
        return 'Policies(%s,%s,%s)' % (app, lb, other)

    def startElement(self, name, attrs, connection):
        if name == 'AppCookieStickinessPolicies':
            rs = ResultSet([('member', AppCookieStickinessPolicy)])
            self.app_cookie_stickiness_policies = rs
            return rs
        elif name == 'LBCookieStickinessPolicies':
            rs = ResultSet([('member', LBCookieStickinessPolicy)])
            self.lb_cookie_stickiness_policies = rs
            return rs
        elif name == 'OtherPolicies':
            rs = ResultSet([('member', OtherPolicy)])
            self.other_policies = rs
            return rs

    def endElement(self, name, value, connection):
        return
