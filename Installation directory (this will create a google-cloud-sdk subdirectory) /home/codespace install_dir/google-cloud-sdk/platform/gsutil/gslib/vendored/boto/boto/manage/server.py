# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010 Chris Moyer http://coredumped.org/
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
High-level abstraction of an EC2 server
"""

import boto.ec2
from boto.mashups.iobject import IObject
from boto.pyami.config import BotoConfigPath, Config
from boto.sdb.db.model import Model
from boto.sdb.db.property import StringProperty, IntegerProperty, BooleanProperty, CalculatedProperty
from boto.manage import propget
from boto.ec2.zone import Zone
from boto.ec2.keypair import KeyPair
import os, time
from contextlib import closing
from boto.exception import EC2ResponseError
from boto.compat import six, StringIO

InstanceTypes = ['m1.small', 'm1.large', 'm1.xlarge',
                 'c1.medium', 'c1.xlarge',
                 'm2.2xlarge', 'm2.4xlarge']

class Bundler(object):

    def __init__(self, server, uname='root'):
        from boto.manage.cmdshell import SSHClient
        self.server = server
        self.uname = uname
        self.ssh_client = SSHClient(server, uname=uname)

    def copy_x509(self, key_file, cert_file):
        print('\tcopying cert and pk over to /mnt directory on server')
        self.ssh_client.open_sftp()
        path, name = os.path.split(key_file)
        self.remote_key_file = '/mnt/%s' % name
        self.ssh_client.put_file(key_file, self.remote_key_file)
        path, name = os.path.split(cert_file)
        self.remote_cert_file = '/mnt/%s' % name
        self.ssh_client.put_file(cert_file, self.remote_cert_file)
        print('...complete!')

    def bundle_image(self, prefix, size, ssh_key):
        command = ""
        if self.uname != 'root':
            command = "sudo "
        command += 'ec2-bundle-vol '
        command += '-c %s -k %s ' % (self.remote_cert_file, self.remote_key_file)
        command += '-u %s ' % self.server._reservation.owner_id
        command += '-p %s ' % prefix
        command += '-s %d ' % size
        command += '-d /mnt '
        if self.server.instance_type == 'm1.small' or self.server.instance_type == 'c1.medium':
            command += '-r i386'
        else:
            command += '-r x86_64'
        return command

    def upload_bundle(self, bucket, prefix, ssh_key):
        command = ""
        if self.uname != 'root':
            command = "sudo "
        command += 'ec2-upload-bundle '
        command += '-m /mnt/%s.manifest.xml ' % prefix
        command += '-b %s ' % bucket
        command += '-a %s ' % self.server.ec2.aws_access_key_id
        command += '-s %s ' % self.server.ec2.aws_secret_access_key
        return command

    def bundle(self, bucket=None, prefix=None, key_file=None, cert_file=None,
               size=None, ssh_key=None, fp=None, clear_history=True):
        iobject = IObject()
        if not bucket:
            bucket = iobject.get_string('Name of S3 bucket')
        if not prefix:
            prefix = iobject.get_string('Prefix for AMI file')
        if not key_file:
            key_file = iobject.get_filename('Path to RSA private key file')
        if not cert_file:
            cert_file = iobject.get_filename('Path to RSA public cert file')
        if not size:
            size = iobject.get_int('Size (in MB) of bundled image')
        if not ssh_key:
            ssh_key = self.server.get_ssh_key_file()
        self.copy_x509(key_file, cert_file)
        if not fp:
            fp = StringIO()
        fp.write('sudo mv %s /mnt/boto.cfg; ' % BotoConfigPath)
        fp.write('mv ~/.ssh/authorized_keys /mnt/authorized_keys; ')
        if clear_history:
            fp.write('history -c; ')
        fp.write(self.bundle_image(prefix, size, ssh_key))
        fp.write('; ')
        fp.write(self.upload_bundle(bucket, prefix, ssh_key))
        fp.write('; ')
        fp.write('sudo mv /mnt/boto.cfg %s; ' % BotoConfigPath)
        fp.write('mv /mnt/authorized_keys ~/.ssh/authorized_keys')
        command = fp.getvalue()
        print('running the following command on the remote server:')
        print(command)
        t = self.ssh_client.run(command)
        print('\t%s' % t[0])
        print('\t%s' % t[1])
        print('...complete!')
        print('registering image...')
        self.image_id = self.server.ec2.register_image(name=prefix, image_location='%s/%s.manifest.xml' % (bucket, prefix))
        return self.image_id

class CommandLineGetter(object):

    def get_ami_list(self):
        my_amis = []
        for ami in self.ec2.get_all_images():
            # hack alert, need a better way to do this!
            if ami.location.find('pyami') >= 0:
                my_amis.append((ami.location, ami))
        return my_amis

    def get_region(self, params):
        region = params.get('region', None)
        if isinstance(region, basestring):
            region = boto.ec2.get_region(region)
            params['region'] = region
        if not region:
            prop = self.cls.find_property('region_name')
            params['region'] = propget.get(prop, choices=boto.ec2.regions)
        self.ec2 = params['region'].connect()

    def get_name(self, params):
        if not params.get('name', None):
            prop = self.cls.find_property('name')
            params['name'] = propget.get(prop)

    def get_description(self, params):
        if not params.get('description', None):
            prop = self.cls.find_property('description')
            params['description'] = propget.get(prop)

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

    def get_ami_id(self, params):
        valid = False
        while not valid:
            ami = params.get('ami', None)
            if not ami:
                prop = StringProperty(name='ami', verbose_name='AMI')
                ami = propget.get(prop)
            try:
                rs = self.ec2.get_all_images([ami])
                if len(rs) == 1:
                    valid = True
                    params['ami'] = rs[0]
            except EC2ResponseError:
                pass

    def get_group(self, params):
        group = params.get('group', None)
        if isinstance(group, basestring):
            group_list = self.ec2.get_all_security_groups()
            for g in group_list:
                if g.name == group:
                    group = g
                    params['group'] = g
        if not group:
            prop = StringProperty(name='group', verbose_name='EC2 Security Group',
                                  choices=self.ec2.get_all_security_groups)
            params['group'] = propget.get(prop)

    def get_key(self, params):
        keypair = params.get('keypair', None)
        if isinstance(keypair, basestring):
            key_list = self.ec2.get_all_key_pairs()
            for k in key_list:
                if k.name == keypair:
                    keypair = k.name
                    params['keypair'] = k.name
        if not keypair:
            prop = StringProperty(name='keypair', verbose_name='EC2 KeyPair',
                                  choices=self.ec2.get_all_key_pairs)
            params['keypair'] = propget.get(prop).name

    def get(self, cls, params):
        self.cls = cls
        self.get_region(params)
        self.ec2 = params['region'].connect()
        self.get_name(params)
        self.get_description(params)
        self.get_instance_type(params)
        self.get_zone(params)
        self.get_quantity(params)
        self.get_ami_id(params)
        self.get_group(params)
        self.get_key(params)

class Server(Model):

    #
    # The properties of this object consists of real properties for data that
    # is not already stored in EC2 somewhere (e.g. name, description) plus
    # calculated properties for all of the properties that are already in
    # EC2 (e.g. hostname, security groups, etc.)
    #
    name = StringProperty(unique=True, verbose_name="Name")
    description = StringProperty(verbose_name="Description")
    region_name = StringProperty(verbose_name="EC2 Region Name")
    instance_id = StringProperty(verbose_name="EC2 Instance ID")
    elastic_ip = StringProperty(verbose_name="EC2 Elastic IP Address")
    production = BooleanProperty(verbose_name="Is This Server Production", default=False)
    ami_id = CalculatedProperty(verbose_name="AMI ID", calculated_type=str, use_method=True)
    zone = CalculatedProperty(verbose_name="Availability Zone Name", calculated_type=str, use_method=True)
    hostname = CalculatedProperty(verbose_name="Public DNS Name", calculated_type=str, use_method=True)
    private_hostname = CalculatedProperty(verbose_name="Private DNS Name", calculated_type=str, use_method=True)
    groups = CalculatedProperty(verbose_name="Security Groups", calculated_type=list, use_method=True)
    security_group = CalculatedProperty(verbose_name="Primary Security Group Name", calculated_type=str, use_method=True)
    key_name = CalculatedProperty(verbose_name="Key Name", calculated_type=str, use_method=True)
    instance_type = CalculatedProperty(verbose_name="Instance Type", calculated_type=str, use_method=True)
    status = CalculatedProperty(verbose_name="Current Status", calculated_type=str, use_method=True)
    launch_time = CalculatedProperty(verbose_name="Server Launch Time", calculated_type=str, use_method=True)
    console_output = CalculatedProperty(verbose_name="Console Output", calculated_type=open, use_method=True)

    packages = []
    plugins = []

    @classmethod
    def add_credentials(cls, cfg, aws_access_key_id, aws_secret_access_key):
        if not cfg.has_section('Credentials'):
            cfg.add_section('Credentials')
        cfg.set('Credentials', 'aws_access_key_id', aws_access_key_id)
        cfg.set('Credentials', 'aws_secret_access_key', aws_secret_access_key)
        if not cfg.has_section('DB_Server'):
            cfg.add_section('DB_Server')
        cfg.set('DB_Server', 'db_type', 'SimpleDB')
        cfg.set('DB_Server', 'db_name', cls._manager.domain.name)

    @classmethod
    def create(cls, config_file=None, logical_volume = None, cfg = None, **params):
        """
        Create a new instance based on the specified configuration file or the specified
        configuration and the passed in parameters.

        If the config_file argument is not None, the configuration is read from there.
        Otherwise, the cfg argument is used.

        The config file may include other config files with a #import reference. The included
        config files must reside in the same directory as the specified file.

        The logical_volume argument, if supplied, will be used to get the current physical
        volume ID and use that as an override of the value specified in the config file. This
        may be useful for debugging purposes when you want to debug with a production config
        file but a test Volume.

        The dictionary argument may be used to override any EC2 configuration values in the
        config file.
        """
        if config_file:
            cfg = Config(path=config_file)
        if cfg.has_section('EC2'):
            # include any EC2 configuration values that aren't specified in params:
            for option in cfg.options('EC2'):
                if option not in params:
                    params[option] = cfg.get('EC2', option)
        getter = CommandLineGetter()
        getter.get(cls, params)
        region = params.get('region')
        ec2 = region.connect()
        cls.add_credentials(cfg, ec2.aws_access_key_id, ec2.aws_secret_access_key)
        ami = params.get('ami')
        kp = params.get('keypair')
        group = params.get('group')
        zone = params.get('zone')
        # deal with possibly passed in logical volume:
        if logical_volume != None:
           cfg.set('EBS', 'logical_volume_name', logical_volume.name)
        cfg_fp = StringIO()
        cfg.write(cfg_fp)
        # deal with the possibility that zone and/or keypair are strings read from the config file:
        if isinstance(zone, Zone):
            zone = zone.name
        if isinstance(kp, KeyPair):
            kp = kp.name
        reservation = ami.run(min_count=1,
                              max_count=params.get('quantity', 1),
                              key_name=kp,
                              security_groups=[group],
                              instance_type=params.get('instance_type'),
                              placement = zone,
                              user_data = cfg_fp.getvalue())
        l = []
        i = 0
        elastic_ip = params.get('elastic_ip')
        instances = reservation.instances
        if elastic_ip is not None and instances.__len__() > 0:
            instance = instances[0]
            print('Waiting for instance to start so we can set its elastic IP address...')
            # Sometimes we get a message from ec2 that says that the instance does not exist.
            # Hopefully the following delay will giv eec2 enough time to get to a stable state:
            time.sleep(5)
            while instance.update() != 'running':
                time.sleep(1)
            instance.use_ip(elastic_ip)
            print('set the elastic IP of the first instance to %s' % elastic_ip)
        for instance in instances:
            s = cls()
            s.ec2 = ec2
            s.name = params.get('name') + '' if i==0 else str(i)
            s.description = params.get('description')
            s.region_name = region.name
            s.instance_id = instance.id
            if elastic_ip and i == 0:
                s.elastic_ip = elastic_ip
            s.put()
            l.append(s)
            i += 1
        return l

    @classmethod
    def create_from_instance_id(cls, instance_id, name, description=''):
        regions = boto.ec2.regions()
        for region in regions:
            ec2 = region.connect()
            try:
                rs = ec2.get_all_reservations([instance_id])
            except:
                rs = []
            if len(rs) == 1:
                s = cls()
                s.ec2 = ec2
                s.name = name
                s.description = description
                s.region_name = region.name
                s.instance_id = instance_id
                s._reservation = rs[0]
                for instance in s._reservation.instances:
                    if instance.id == instance_id:
                        s._instance = instance
                s.put()
                return s
        return None

    @classmethod
    def create_from_current_instances(cls):
        servers = []
        regions = boto.ec2.regions()
        for region in regions:
            ec2 = region.connect()
            rs = ec2.get_all_reservations()
            for reservation in rs:
                for instance in reservation.instances:
                    try:
                        next(Server.find(instance_id=instance.id))
                        boto.log.info('Server for %s already exists' % instance.id)
                    except StopIteration:
                        s = cls()
                        s.ec2 = ec2
                        s.name = instance.id
                        s.region_name = region.name
                        s.instance_id = instance.id
                        s._reservation = reservation
                        s.put()
                        servers.append(s)
        return servers

    def __init__(self, id=None, **kw):
        super(Server, self).__init__(id, **kw)
        self.ssh_key_file = None
        self.ec2 = None
        self._cmdshell = None
        self._reservation = None
        self._instance = None
        self._setup_ec2()

    def _setup_ec2(self):
        if self.ec2 and self._instance and self._reservation:
            return
        if self.id:
            if self.region_name:
                for region in boto.ec2.regions():
                    if region.name == self.region_name:
                        self.ec2 = region.connect()
                        if self.instance_id and not self._instance:
                            try:
                                rs = self.ec2.get_all_reservations([self.instance_id])
                                if len(rs) >= 1:
                                    for instance in rs[0].instances:
                                        if instance.id == self.instance_id:
                                            self._reservation = rs[0]
                                            self._instance = instance
                            except EC2ResponseError:
                                pass

    def _status(self):
        status = ''
        if self._instance:
            self._instance.update()
            status = self._instance.state
        return status

    def _hostname(self):
        hostname = ''
        if self._instance:
            hostname = self._instance.public_dns_name
        return hostname

    def _private_hostname(self):
        hostname = ''
        if self._instance:
            hostname = self._instance.private_dns_name
        return hostname

    def _instance_type(self):
        it = ''
        if self._instance:
            it = self._instance.instance_type
        return it

    def _launch_time(self):
        lt = ''
        if self._instance:
            lt = self._instance.launch_time
        return lt

    def _console_output(self):
        co = ''
        if self._instance:
            co = self._instance.get_console_output()
        return co

    def _groups(self):
        gn = []
        if self._reservation:
            gn = self._reservation.groups
        return gn

    def _security_group(self):
        groups = self._groups()
        if len(groups) >= 1:
            return groups[0].id
        return ""

    def _zone(self):
        zone = None
        if self._instance:
            zone = self._instance.placement
        return zone

    def _key_name(self):
        kn = None
        if self._instance:
            kn = self._instance.key_name
        return kn

    def put(self):
        super(Server, self).put()
        self._setup_ec2()

    def delete(self):
        if self.production:
            raise ValueError("Can't delete a production server")
        #self.stop()
        super(Server, self).delete()

    def stop(self):
        if self.production:
            raise ValueError("Can't delete a production server")
        if self._instance:
            self._instance.stop()

    def terminate(self):
        if self.production:
            raise ValueError("Can't delete a production server")
        if self._instance:
            self._instance.terminate()

    def reboot(self):
        if self._instance:
            self._instance.reboot()

    def wait(self):
        while self.status != 'running':
            time.sleep(5)

    def get_ssh_key_file(self):
        if not self.ssh_key_file:
            ssh_dir = os.path.expanduser('~/.ssh')
            if os.path.isdir(ssh_dir):
                ssh_file = os.path.join(ssh_dir, '%s.pem' % self.key_name)
                if os.path.isfile(ssh_file):
                    self.ssh_key_file = ssh_file
            if not self.ssh_key_file:
                iobject = IObject()
                self.ssh_key_file = iobject.get_filename('Path to OpenSSH Key file')
        return self.ssh_key_file

    def get_cmdshell(self):
        if not self._cmdshell:
            from boto.manage import cmdshell
            self.get_ssh_key_file()
            self._cmdshell = cmdshell.start(self)
        return self._cmdshell

    def reset_cmdshell(self):
        self._cmdshell = None

    def run(self, command):
        with closing(self.get_cmdshell()) as cmd:
            status = cmd.run(command)
        return status

    def get_bundler(self, uname='root'):
        self.get_ssh_key_file()
        return Bundler(self, uname)

    def get_ssh_client(self, uname='root', ssh_pwd=None):
        from boto.manage.cmdshell import SSHClient
        self.get_ssh_key_file()
        return SSHClient(self, uname=uname, ssh_pwd=ssh_pwd)

    def install(self, pkg):
        return self.run('apt-get -y install %s' % pkg)



