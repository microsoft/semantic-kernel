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
High-level abstraction of an EC2 server
"""

import boto
import boto.utils
from boto.compat import StringIO
from boto.mashups.iobject import IObject
from boto.pyami.config import Config, BotoConfigPath
from boto.mashups.interactive import interactive_shell
from boto.sdb.db.model import Model
from boto.sdb.db.property import StringProperty
import os


class ServerSet(list):

    def __getattr__(self, name):
        results = []
        is_callable = False
        for server in self:
            try:
                val = getattr(server, name)
                if callable(val):
                    is_callable = True
                results.append(val)
            except:
                results.append(None)
        if is_callable:
            self.map_list = results
            return self.map
        return results

    def map(self, *args):
        results = []
        for fn in self.map_list:
            results.append(fn(*args))
        return results

class Server(Model):

    @property
    def ec2(self):
        if self._ec2 is None:
            self._ec2 = boto.connect_ec2()
        return self._ec2

    @classmethod
    def Inventory(cls):
        """
        Returns a list of Server instances, one for each Server object
        persisted in the db
        """
        l = ServerSet()
        rs = cls.find()
        for server in rs:
            l.append(server)
        return l

    @classmethod
    def Register(cls, name, instance_id, description=''):
        s = cls()
        s.name = name
        s.instance_id = instance_id
        s.description = description
        s.save()
        return s

    def __init__(self, id=None, **kw):
        super(Server, self).__init__(id, **kw)
        self._reservation = None
        self._instance = None
        self._ssh_client = None
        self._pkey = None
        self._config = None
        self._ec2 = None

    name = StringProperty(unique=True, verbose_name="Name")
    instance_id = StringProperty(verbose_name="Instance ID")
    config_uri = StringProperty()
    ami_id = StringProperty(verbose_name="AMI ID")
    zone = StringProperty(verbose_name="Availability Zone")
    security_group = StringProperty(verbose_name="Security Group", default="default")
    key_name = StringProperty(verbose_name="Key Name")
    elastic_ip = StringProperty(verbose_name="Elastic IP")
    instance_type = StringProperty(verbose_name="Instance Type")
    description = StringProperty(verbose_name="Description")
    log = StringProperty()

    def setReadOnly(self, value):
        raise AttributeError

    def getInstance(self):
        if not self._instance:
            if self.instance_id:
                try:
                    rs = self.ec2.get_all_reservations([self.instance_id])
                except:
                    return None
                if len(rs) > 0:
                    self._reservation = rs[0]
                    self._instance = self._reservation.instances[0]
        return self._instance

    instance = property(getInstance, setReadOnly, None, 'The Instance for the server')

    def getAMI(self):
        if self.instance:
            return self.instance.image_id

    ami = property(getAMI, setReadOnly, None, 'The AMI for the server')

    def getStatus(self):
        if self.instance:
            self.instance.update()
            return self.instance.state

    status = property(getStatus, setReadOnly, None,
                      'The status of the server')

    def getHostname(self):
        if self.instance:
            return self.instance.public_dns_name

    hostname = property(getHostname, setReadOnly, None,
                        'The public DNS name of the server')

    def getPrivateHostname(self):
        if self.instance:
            return self.instance.private_dns_name

    private_hostname = property(getPrivateHostname, setReadOnly, None,
                                'The private DNS name of the server')

    def getLaunchTime(self):
        if self.instance:
            return self.instance.launch_time

    launch_time = property(getLaunchTime, setReadOnly, None,
                           'The time the Server was started')

    def getConsoleOutput(self):
        if self.instance:
            return self.instance.get_console_output()

    console_output = property(getConsoleOutput, setReadOnly, None,
                              'Retrieve the console output for server')

    def getGroups(self):
        if self._reservation:
            return self._reservation.groups
        else:
            return None

    groups = property(getGroups, setReadOnly, None,
                      'The Security Groups controlling access to this server')

    def getConfig(self):
        if not self._config:
            remote_file = BotoConfigPath
            local_file = '%s.ini' % self.instance.id
            self.get_file(remote_file, local_file)
            self._config = Config(local_file)
        return self._config

    def setConfig(self, config):
        local_file = '%s.ini' % self.instance.id
        fp = open(local_file)
        config.write(fp)
        fp.close()
        self.put_file(local_file, BotoConfigPath)
        self._config = config

    config = property(getConfig, setConfig, None,
                      'The instance data for this server')

    def set_config(self, config):
        """
        Set SDB based config
        """
        self._config = config
        self._config.dump_to_sdb("botoConfigs", self.id)

    def load_config(self):
        self._config = Config(do_load=False)
        self._config.load_from_sdb("botoConfigs", self.id)

    def stop(self):
        if self.instance:
            self.instance.stop()

    def start(self):
        self.stop()
        ec2 = boto.connect_ec2()
        ami = ec2.get_all_images(image_ids = [str(self.ami_id)])[0]
        groups = ec2.get_all_security_groups(groupnames=[str(self.security_group)])
        if not self._config:
            self.load_config()
        if not self._config.has_section("Credentials"):
            self._config.add_section("Credentials")
            self._config.set("Credentials", "aws_access_key_id", ec2.aws_access_key_id)
            self._config.set("Credentials", "aws_secret_access_key", ec2.aws_secret_access_key)

        if not self._config.has_section("Pyami"):
            self._config.add_section("Pyami")

        if self._manager.domain:
            self._config.set('Pyami', 'server_sdb_domain', self._manager.domain.name)
            self._config.set("Pyami", 'server_sdb_name', self.name)

        cfg = StringIO()
        self._config.write(cfg)
        cfg = cfg.getvalue()
        r = ami.run(min_count=1,
                    max_count=1,
                    key_name=self.key_name,
                    security_groups = groups,
                    instance_type = self.instance_type,
                    placement = self.zone,
                    user_data = cfg)
        i = r.instances[0]
        self.instance_id = i.id
        self.put()
        if self.elastic_ip:
            ec2.associate_address(self.instance_id, self.elastic_ip)

    def reboot(self):
        if self.instance:
            self.instance.reboot()

    def get_ssh_client(self, key_file=None, host_key_file='~/.ssh/known_hosts',
                       uname='root'):
        import paramiko
        if not self.instance:
            print('No instance yet!')
            return
        if not self._ssh_client:
            if not key_file:
                iobject = IObject()
                key_file = iobject.get_filename('Path to OpenSSH Key file')
            self._pkey = paramiko.RSAKey.from_private_key_file(key_file)
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.load_system_host_keys()
            self._ssh_client.load_host_keys(os.path.expanduser(host_key_file))
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh_client.connect(self.instance.public_dns_name,
                                     username=uname, pkey=self._pkey)
        return self._ssh_client

    def get_file(self, remotepath, localpath):
        ssh_client = self.get_ssh_client()
        sftp_client = ssh_client.open_sftp()
        sftp_client.get(remotepath, localpath)

    def put_file(self, localpath, remotepath):
        ssh_client = self.get_ssh_client()
        sftp_client = ssh_client.open_sftp()
        sftp_client.put(localpath, remotepath)

    def listdir(self, remotepath):
        ssh_client = self.get_ssh_client()
        sftp_client = ssh_client.open_sftp()
        return sftp_client.listdir(remotepath)

    def shell(self, key_file=None):
        ssh_client = self.get_ssh_client(key_file)
        channel = ssh_client.invoke_shell()
        interactive_shell(channel)

    def bundle_image(self, prefix, key_file, cert_file, size):
        print('bundling image...')
        print('\tcopying cert and pk over to /mnt directory on server')
        ssh_client = self.get_ssh_client()
        sftp_client = ssh_client.open_sftp()
        path, name = os.path.split(key_file)
        remote_key_file = '/mnt/%s' % name
        self.put_file(key_file, remote_key_file)
        path, name = os.path.split(cert_file)
        remote_cert_file = '/mnt/%s' % name
        self.put_file(cert_file, remote_cert_file)
        print('\tdeleting %s' % BotoConfigPath)
        # delete the metadata.ini file if it exists
        try:
            sftp_client.remove(BotoConfigPath)
        except:
            pass
        command = 'sudo ec2-bundle-vol '
        command += '-c %s -k %s ' % (remote_cert_file, remote_key_file)
        command += '-u %s ' % self._reservation.owner_id
        command += '-p %s ' % prefix
        command += '-s %d ' % size
        command += '-d /mnt '
        if self.instance.instance_type == 'm1.small' or self.instance_type == 'c1.medium':
            command += '-r i386'
        else:
            command += '-r x86_64'
        print('\t%s' % command)
        t = ssh_client.exec_command(command)
        response = t[1].read()
        print('\t%s' % response)
        print('\t%s' % t[2].read())
        print('...complete!')

    def upload_bundle(self, bucket, prefix):
        print('uploading bundle...')
        command = 'ec2-upload-bundle '
        command += '-m /mnt/%s.manifest.xml ' % prefix
        command += '-b %s ' % bucket
        command += '-a %s ' % self.ec2.aws_access_key_id
        command += '-s %s ' % self.ec2.aws_secret_access_key
        print('\t%s' % command)
        ssh_client = self.get_ssh_client()
        t = ssh_client.exec_command(command)
        response = t[1].read()
        print('\t%s' % response)
        print('\t%s' % t[2].read())
        print('...complete!')

    def create_image(self, bucket=None, prefix=None, key_file=None, cert_file=None, size=None):
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
        self.bundle_image(prefix, key_file, cert_file, size)
        self.upload_bundle(bucket, prefix)
        print('registering image...')
        self.image_id = self.ec2.register_image('%s/%s.manifest.xml' % (bucket, prefix))
        return self.image_id

    def attach_volume(self, volume, device="/dev/sdp"):
        """
        Attach an EBS volume to this server

        :param volume: EBS Volume to attach
        :type volume: boto.ec2.volume.Volume

        :param device: Device to attach to (default to /dev/sdp)
        :type device: string
        """
        if hasattr(volume, "id"):
            volume_id = volume.id
        else:
            volume_id = volume
        return self.ec2.attach_volume(volume_id=volume_id, instance_id=self.instance_id, device=device)

    def detach_volume(self, volume):
        """
        Detach an EBS volume from this server

        :param volume: EBS Volume to detach
        :type volume: boto.ec2.volume.Volume
        """
        if hasattr(volume, "id"):
            volume_id = volume.id
        else:
            volume_id = volume
        return self.ec2.detach_volume(volume_id=volume_id, instance_id=self.instance_id)

    def install_package(self, package_name):
        print('installing %s...' % package_name)
        command = 'yum -y install %s' % package_name
        print('\t%s' % command)
        ssh_client = self.get_ssh_client()
        t = ssh_client.exec_command(command)
        response = t[1].read()
        print('\t%s' % response)
        print('\t%s' % t[2].read())
        print('...complete!')
