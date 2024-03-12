# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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
import boto.ec2
from boto.sdb.db.property import StringProperty, IntegerProperty
from boto.manage import propget
from boto.compat import six

InstanceTypes = ['m1.small', 'm1.large', 'm1.xlarge',
                 'c1.medium', 'c1.xlarge', 'm2.xlarge',
                 'm2.2xlarge', 'm2.4xlarge', 'cc1.4xlarge',
                 't1.micro']


class BuyReservation(object):

    def get_region(self, params):
        if not params.get('region', None):
            prop = StringProperty(name='region', verbose_name='EC2 Region',
                                  choices=boto.ec2.regions)
            params['region'] = propget.get(prop, choices=boto.ec2.regions)

    def get_instance_type(self, params):
        if not params.get('instance_type', None):
            prop = StringProperty(name='instance_type', verbose_name='Instance Type',
                                  choices=InstanceTypes)
            params['instance_type'] = propget.get(prop)

    def get_quantity(self, params):
        if not params.get('quantity', None):
            prop = IntegerProperty(name='quantity', verbose_name='Number of Instances')
            params['quantity'] = propget.get(prop)

    def get_zone(self, params):
        if not params.get('zone', None):
            prop = StringProperty(name='zone', verbose_name='EC2 Availability Zone',
                                  choices=self.ec2.get_all_zones)
            params['zone'] = propget.get(prop)

    def get(self, params):
        self.get_region(params)
        self.ec2 = params['region'].connect()
        self.get_instance_type(params)
        self.get_zone(params)
        self.get_quantity(params)

if __name__ == "__main__":
    obj = BuyReservation()
    params = {}
    obj.get(params)
    offerings = obj.ec2.get_all_reserved_instances_offerings(instance_type=params['instance_type'],
                                                             availability_zone=params['zone'].name)
    print('\nThe following Reserved Instances Offerings are available:\n')
    for offering in offerings:
        offering.describe()
    prop = StringProperty(name='offering', verbose_name='Offering',
                          choices=offerings)
    offering = propget.get(prop)
    print('\nYou have chosen this offering:')
    offering.describe()
    unit_price = float(offering.fixed_price)
    total_price = unit_price * params['quantity']
    print('!!! You are about to purchase %d of these offerings for a total of $%.2f !!!' % (params['quantity'], total_price))
    answer = six.moves.input('Are you sure you want to do this?  If so, enter YES: ')
    if answer.strip().lower() == 'yes':
        offering.purchase(params['quantity'])
    else:
        print('Purchase cancelled')
