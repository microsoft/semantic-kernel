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
#
"""
This installer will install mysql-server on an Ubuntu machine.
In addition to the normal installation done by apt-get, it will
also configure the new MySQL server to store it's data files in
a different location.  By default, this is /mnt but that can be
configured in the [MySQL] section of the boto config file passed
to the instance.
"""
from boto.pyami.installers.ubuntu.installer import Installer
import os
import boto
from boto.utils import ShellCommand
from boto.compat import ConfigParser
import time

ConfigSection = """
[MySQL]
root_password = <will be used as MySQL root password, default none>
data_dir = <new data dir for MySQL, default is /mnt>
"""

class MySQL(Installer):

    def install(self):
        self.run('apt-get update')
        self.run('apt-get -y install mysql-server', notify=True, exit_on_error=True)

#    def set_root_password(self, password=None):
#        if not password:
#            password = boto.config.get('MySQL', 'root_password')
#        if password:
#            self.run('mysqladmin -u root password %s' % password)
#        return password

    def change_data_dir(self, password=None):
        data_dir = boto.config.get('MySQL', 'data_dir', '/mnt')
        fresh_install = False
        is_mysql_running_command = ShellCommand('mysqladmin ping') # exit status 0 if mysql is running
        is_mysql_running_command.run()
        if is_mysql_running_command.getStatus() == 0:
            # mysql is running. This is the state apt-get will leave it in. If it isn't running,
            # that means mysql was already installed on the AMI and there's no need to stop it,
            # saving 40 seconds on instance startup.
            time.sleep(10) #trying to stop mysql immediately after installing it fails
            # We need to wait until mysql creates the root account before we kill it
            # or bad things will happen
            i = 0
            while self.run("echo 'quit' | mysql -u root") != 0 and i < 5:
                time.sleep(5)
                i = i + 1
            self.run('/etc/init.d/mysql stop')
            self.run("pkill -9 mysql")

        mysql_path = os.path.join(data_dir, 'mysql')
        if not os.path.exists(mysql_path):
            self.run('mkdir %s' % mysql_path)
            fresh_install = True
        self.run('chown -R mysql:mysql %s' % mysql_path)
        fp = open('/etc/mysql/conf.d/use_mnt.cnf', 'w')
        fp.write('# created by pyami\n')
        fp.write('# use the %s volume for data\n' % data_dir)
        fp.write('[mysqld]\n')
        fp.write('datadir = %s\n' % mysql_path)
        fp.write('log_bin = %s\n' % os.path.join(mysql_path, 'mysql-bin.log'))
        fp.close()
        if fresh_install:
            self.run('cp -pr /var/lib/mysql/* %s/' % mysql_path)
            self.start('mysql')
        else:
            #get the password ubuntu expects to use:
            config_parser = ConfigParser()
            config_parser.read('/etc/mysql/debian.cnf')
            password = config_parser.get('client', 'password')
            # start the mysql deamon, then mysql with the required grant statement piped into it:
            self.start('mysql')
            time.sleep(10) #time for mysql to start
            grant_command = "echo \"GRANT ALL PRIVILEGES ON *.* TO 'debian-sys-maint'@'localhost' IDENTIFIED BY '%s' WITH GRANT OPTION;\" | mysql" % password
            while self.run(grant_command) != 0:
                time.sleep(5)
            # leave mysqld running

    def main(self):
        self.install()
        # change_data_dir runs 'mysql -u root' which assumes there is no mysql password, i
        # and changing that is too ugly to be worth it:
        #self.set_root_password()
        self.change_data_dir()
