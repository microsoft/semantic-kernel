# Copyright (c) 2008 Chris Moyer http://coredumped.org
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
from boto.pyami.installers.ubuntu.installer import Installer
import boto
import os

class Trac(Installer):
    """
    Install Trac and DAV-SVN
    Sets up a Vhost pointing to [Trac]->home
    Using the config parameter [Trac]->hostname
    Sets up a trac environment for every directory found under [Trac]->data_dir

    [Trac]
    name = My Foo Server
    hostname = trac.foo.com
    home = /mnt/sites/trac
    data_dir = /mnt/trac
    svn_dir = /mnt/subversion
    server_admin = root@foo.com
    sdb_auth_domain = users
    # Optional
    SSLCertificateFile = /mnt/ssl/foo.crt
    SSLCertificateKeyFile = /mnt/ssl/foo.key
    SSLCertificateChainFile = /mnt/ssl/FooCA.crt

    """

    def install(self):
        self.run('apt-get -y install trac', notify=True, exit_on_error=True)
        self.run('apt-get -y install libapache2-svn', notify=True, exit_on_error=True)
        self.run("a2enmod ssl")
        self.run("a2enmod mod_python")
        self.run("a2enmod dav_svn")
        self.run("a2enmod rewrite")
        # Make sure that boto.log is writable by everyone so that subversion post-commit hooks can
        # write to it.
        self.run("touch /var/log/boto.log")
        self.run("chmod a+w /var/log/boto.log")

    def setup_vhost(self):
        domain = boto.config.get("Trac", "hostname").strip()
        if domain:
            domain_info = domain.split('.')
            cnf = open("/etc/apache2/sites-available/%s" % domain_info[0], "w")
            cnf.write("NameVirtualHost *:80\n")
            if boto.config.get("Trac", "SSLCertificateFile"):
                cnf.write("NameVirtualHost *:443\n\n")
                cnf.write("<VirtualHost *:80>\n")
                cnf.write("\tServerAdmin %s\n" % boto.config.get("Trac", "server_admin").strip())
                cnf.write("\tServerName %s\n" % domain)
                cnf.write("\tRewriteEngine On\n")
                cnf.write("\tRewriteRule ^(.*)$ https://%s$1\n" % domain)
                cnf.write("</VirtualHost>\n\n")

                cnf.write("<VirtualHost *:443>\n")
            else:
                cnf.write("<VirtualHost *:80>\n")

            cnf.write("\tServerAdmin %s\n" % boto.config.get("Trac", "server_admin").strip())
            cnf.write("\tServerName %s\n" % domain)
            cnf.write("\tDocumentRoot %s\n" % boto.config.get("Trac", "home").strip())

            cnf.write("\t<Directory %s>\n" % boto.config.get("Trac", "home").strip())
            cnf.write("\t\tOptions FollowSymLinks Indexes MultiViews\n")
            cnf.write("\t\tAllowOverride All\n")
            cnf.write("\t\tOrder allow,deny\n")
            cnf.write("\t\tallow from all\n")
            cnf.write("\t</Directory>\n")

            cnf.write("\t<Location />\n")
            cnf.write("\t\tAuthType Basic\n")
            cnf.write("\t\tAuthName \"%s\"\n" % boto.config.get("Trac", "name"))
            cnf.write("\t\tRequire valid-user\n")
            cnf.write("\t\tAuthUserFile /mnt/apache/passwd/passwords\n")
            cnf.write("\t</Location>\n")

            data_dir = boto.config.get("Trac", "data_dir")
            for env in os.listdir(data_dir):
                if(env[0] != "."):
                    cnf.write("\t<Location /trac/%s>\n" % env)
                    cnf.write("\t\tSetHandler mod_python\n")
                    cnf.write("\t\tPythonInterpreter main_interpreter\n")
                    cnf.write("\t\tPythonHandler trac.web.modpython_frontend\n")
                    cnf.write("\t\tPythonOption TracEnv %s/%s\n" % (data_dir, env))
                    cnf.write("\t\tPythonOption TracUriRoot /trac/%s\n" % env)
                    cnf.write("\t</Location>\n")

            svn_dir = boto.config.get("Trac", "svn_dir")
            for env in os.listdir(svn_dir):
                if(env[0] != "."):
                    cnf.write("\t<Location /svn/%s>\n" % env)
                    cnf.write("\t\tDAV svn\n")
                    cnf.write("\t\tSVNPath %s/%s\n" % (svn_dir, env))
                    cnf.write("\t</Location>\n")

            cnf.write("\tErrorLog /var/log/apache2/error.log\n")
            cnf.write("\tLogLevel warn\n")
            cnf.write("\tCustomLog /var/log/apache2/access.log combined\n")
            cnf.write("\tServerSignature On\n")
            SSLCertificateFile = boto.config.get("Trac", "SSLCertificateFile")
            if SSLCertificateFile:
                cnf.write("\tSSLEngine On\n")
                cnf.write("\tSSLCertificateFile %s\n" % SSLCertificateFile)

            SSLCertificateKeyFile = boto.config.get("Trac", "SSLCertificateKeyFile")
            if SSLCertificateKeyFile:
                cnf.write("\tSSLCertificateKeyFile %s\n" % SSLCertificateKeyFile)

            SSLCertificateChainFile = boto.config.get("Trac", "SSLCertificateChainFile")
            if SSLCertificateChainFile:
                cnf.write("\tSSLCertificateChainFile %s\n" % SSLCertificateChainFile)
            cnf.write("</VirtualHost>\n")
            cnf.close()
            self.run("a2ensite %s" % domain_info[0])
            self.run("/etc/init.d/apache2 force-reload")

    def main(self):
        self.install()
        self.setup_vhost()
