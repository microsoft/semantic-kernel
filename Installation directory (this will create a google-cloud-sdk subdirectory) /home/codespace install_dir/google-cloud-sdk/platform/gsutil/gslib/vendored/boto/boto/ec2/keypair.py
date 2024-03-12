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
Represents an EC2 Keypair
"""

import os
from boto.ec2.ec2object import EC2Object
from boto.exception import BotoClientError


class KeyPair(EC2Object):

    def __init__(self, connection=None):
        super(KeyPair, self).__init__(connection)
        self.name = None
        self.fingerprint = None
        self.material = None

    def __repr__(self):
        return 'KeyPair:%s' % self.name

    def endElement(self, name, value, connection):
        if name == 'keyName':
            self.name = value
        elif name == 'keyFingerprint':
            self.fingerprint = value
        elif name == 'keyMaterial':
            self.material = value
        else:
            setattr(self, name, value)

    def delete(self, dry_run=False):
        """
        Delete the KeyPair.

        :rtype: bool
        :return: True if successful, otherwise False.
        """
        return self.connection.delete_key_pair(self.name, dry_run=dry_run)

    def save(self, directory_path):
        """
        Save the material (the unencrypted PEM encoded RSA private key)
        of a newly created KeyPair to a local file.

        :type directory_path: string
        :param directory_path: The fully qualified path to the directory
                               in which the keypair will be saved.  The
                               keypair file will be named using the name
                               of the keypair as the base name and .pem
                               for the file extension.  If a file of that
                               name already exists in the directory, an
                               exception will be raised and the old file
                               will not be overwritten.

        :rtype: bool
        :return: True if successful.
        """
        if self.material:
            directory_path = os.path.expanduser(directory_path)
            file_path = os.path.join(directory_path, '%s.pem' % self.name)
            if os.path.exists(file_path):
                raise BotoClientError('%s already exists, it will not be overwritten' % file_path)
            fp = open(file_path, 'wb')
            fp.write(self.material)
            fp.close()
            os.chmod(file_path, 0o600)
            return True
        else:
            raise BotoClientError('KeyPair contains no material')

    def copy_to_region(self, region, dry_run=False):
        """
        Create a new key pair of the same new in another region.
        Note that the new key pair will use a different ssh
        cert than the this key pair.  After doing the copy,
        you will need to save the material associated with the
        new key pair (use the save method) to a local file.

        :type region: :class:`boto.ec2.regioninfo.RegionInfo`
        :param region: The region to which this security group will be copied.

        :rtype: :class:`boto.ec2.keypair.KeyPair`
        :return: The new key pair
        """
        if region.name == self.region:
            raise BotoClientError('Unable to copy to the same Region')
        conn_params = self.connection.get_params()
        rconn = region.connect(**conn_params)
        kp = rconn.create_key_pair(self.name, dry_run=dry_run)
        return kp
