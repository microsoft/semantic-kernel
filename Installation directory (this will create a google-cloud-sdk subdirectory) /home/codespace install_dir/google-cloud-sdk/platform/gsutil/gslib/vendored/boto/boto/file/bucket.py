# Copyright 2010 Google Inc.
# Copyright (c) 2011, Nexenta Systems Inc.
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

# File representation of bucket, for use with "file://" URIs.

import os
from boto.file.key import Key
from boto.file.simpleresultset import SimpleResultSet
from boto.s3.bucketlistresultset import BucketListResultSet

class Bucket(object):
    def __init__(self, name, contained_key):
        """Instantiate an anonymous file-based Bucket around a single key.
        """
        self.name = name
        self.contained_key = contained_key

    def __iter__(self):
        return iter(BucketListResultSet(self))

    def __str__(self):
        return 'anonymous bucket for file://' + self.contained_key

    def delete_key(self, key_name, headers=None,
                   version_id=None, mfa_token=None):
        """
        Deletes a key from the bucket.

        :type key_name: string
        :param key_name: The key name to delete

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type mfa_token: tuple or list of strings
        :param mfa_token: Unused in this subclass.
        """
        os.remove(key_name)

    def get_all_keys(self, headers=None, **params):
        """
        This method returns the single key around which this anonymous Bucket
        was instantiated.

        :rtype: SimpleResultSet
        :return: The result from file system listing the keys requested

        """
        key = Key(self.name, self.contained_key)
        return SimpleResultSet([key])

    def get_key(self, key_name, headers=None, version_id=None,
                                            key_type=Key.KEY_REGULAR_FILE):
        """
        Check to see if a particular key exists within the bucket.
        Returns: An instance of a Key object or None

        :type key_name: string
        :param key_name: The name of the key to retrieve

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type stream_type: integer
        :param stream_type: Type of the Key - Regular File or input/output Stream

        :rtype: :class:`boto.file.key.Key`
        :returns: A Key object from this bucket.
        """
        if key_name == '-':
            return Key(self.name, '-', key_type=Key.KEY_STREAM_READABLE)
        else:
            fp = open(key_name, 'rb')
            return Key(self.name, key_name, fp)

    def new_key(self, key_name=None, key_type=Key.KEY_REGULAR_FILE):
        """
        Creates a new key

        :type key_name: string
        :param key_name: The name of the key to create

        :rtype: :class:`boto.file.key.Key`
        :returns: An instance of the newly created key object
        """
        if key_name == '-':
            return Key(self.name, '-', key_type=Key.KEY_STREAM_WRITABLE)
        else:
            dir_name = os.path.dirname(key_name)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
            fp = open(key_name, 'wb')
            return Key(self.name, key_name, fp)
