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
"""
High-level abstraction of an EC2 order for servers
"""

import boto
import boto.ec2
from boto.mashups.server import Server, ServerSet
from boto.mashups.iobject import IObject
from boto.pyami.config import Config
from boto.sdb.persist import get_domain, set_domain
import time
from boto.compat import StringIO

InstanceTypes = ['m1.small', 'm1.large', 'm1.xlarge', 'c1.medium', 'c1.xlarge']

class Item(IObject):
    
    def __init__(self):
        self.region = None
        self.name = None
        self.instance_type = None
        self.quantity = 0
        self.zone = None
        self.ami = None
        self.groups = []
        self.key = None
        self.ec2 = None
        self.config = None

    def set_userdata(self, key, value):
        self.userdata[key] = value

    def get_userdata(self, key):
        return self.userdata[key]

    def set_region(self, region=None):
        if region:
            self.region = region
        else:
            l = [(r, r.name, r.endpoint) for r in boto.ec2.regions()]
            self.region = self.choose_from_list(l, prompt='Choose Region')

    def set_name(self, name=None):
        if name:
            self.name = name
        else:
            self.name = self.get_string('Name')

    def set_instance_type(self, instance_type=None):
        if instance_type:
            self.instance_type = instance_type
        else:
            self.instance_type = self.choose_from_list(InstanceTypes, 'Instance Type')

    def set_quantity(self, n=0):
        if n > 0:
            self.quantity = n
        else:
            self.quantity = self.get_int('Quantity')

    def set_zone(self, zone=None):
        if zone:
            self.zone = zone
        else:
            l = [(z, z.name, z.state) for z in self.ec2.get_all_zones()]
            self.zone = self.choose_from_list(l, prompt='Choose Availability Zone')
            
    def set_ami(self, ami=None):
        if ami:
            self.ami = ami
        else:
            l = [(a, a.id, a.location) for a in self.ec2.get_all_images()]
            self.ami = self.choose_from_list(l, prompt='Choose AMI')

    def add_group(self, group=None):
        if group:
            self.groups.append(group)
        else:
            l = [(s, s.name, s.description) for s in self.ec2.get_all_security_groups()]
            self.groups.append(self.choose_from_list(l, prompt='Choose Security Group'))

    def set_key(self, key=None):
        if key:
            self.key = key
        else:
            l = [(k, k.name, '') for k in self.ec2.get_all_key_pairs()]
            self.key = self.choose_from_list(l, prompt='Choose Keypair')

    def update_config(self):
        if not self.config.has_section('Credentials'):
            self.config.add_section('Credentials')
            self.config.set('Credentials', 'aws_access_key_id', self.ec2.aws_access_key_id)
            self.config.set('Credentials', 'aws_secret_access_key', self.ec2.aws_secret_access_key)
        if not self.config.has_section('Pyami'):
            self.config.add_section('Pyami')
        sdb_domain = get_domain()
        if sdb_domain:
            self.config.set('Pyami', 'server_sdb_domain', sdb_domain)
            self.config.set('Pyami', 'server_sdb_name', self.name)

    def set_config(self, config_path=None):
        if not config_path:
            config_path = self.get_filename('Specify Config file')
        self.config = Config(path=config_path)

    def get_userdata_string(self):
        s = StringIO()
        self.config.write(s)
        return s.getvalue()

    def enter(self, **params):
        self.region = params.get('region', self.region)
        if not self.region:
            self.set_region()
        self.ec2 = self.region.connect()
        self.name = params.get('name', self.name)
        if not self.name:
            self.set_name()
        self.instance_type = params.get('instance_type', self.instance_type)
        if not self.instance_type:
            self.set_instance_type()
        self.zone = params.get('zone', self.zone)
        if not self.zone:
            self.set_zone()
        self.quantity = params.get('quantity', self.quantity)
        if not self.quantity:
            self.set_quantity()
        self.ami = params.get('ami', self.ami)
        if not self.ami:
            self.set_ami()
        self.groups = params.get('groups', self.groups)
        if not self.groups:
            self.add_group()
        self.key = params.get('key', self.key)
        if not self.key:
            self.set_key()
        self.config = params.get('config', self.config)
        if not self.config:
            self.set_config()
        self.update_config()

class Order(IObject):

    def __init__(self):
        self.items = []
        self.reservation = None

    def add_item(self, **params):
        item = Item()
        item.enter(**params)
        self.items.append(item)

    def display(self):
        print('This Order consists of the following items')
        print() 
        print('QTY\tNAME\tTYPE\nAMI\t\tGroups\t\t\tKeyPair')
        for item in self.items:
            print('%s\t%s\t%s\t%s\t%s\t%s' % (item.quantity, item.name, item.instance_type,
                                              item.ami.id, item.groups, item.key.name))

    def place(self, block=True):
        if get_domain() is None:
            print('SDB Persistence Domain not set')
            domain_name = self.get_string('Specify SDB Domain')
            set_domain(domain_name)
        s = ServerSet()
        for item in self.items:
            r = item.ami.run(min_count=1, max_count=item.quantity,
                             key_name=item.key.name, user_data=item.get_userdata_string(),
                             security_groups=item.groups, instance_type=item.instance_type,
                             placement=item.zone.name)
            if block:
                states = [i.state for i in r.instances]
                if states.count('running') != len(states):
                    print(states)
                    time.sleep(15)
                    states = [i.update() for i in r.instances]
            for i in r.instances:
                server = Server()
                server.name = item.name
                server.instance_id = i.id
                server.reservation = r
                server.save()
                s.append(server)
        if len(s) == 1:
            return s[0]
        else:
            return s
        

    
