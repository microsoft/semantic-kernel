# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
Represents an EC2 Object
"""
from boto.ec2.tag import TagSet


class EC2Object(object):

    def __init__(self, connection=None):
        self.connection = connection
        if self.connection and hasattr(self.connection, 'region'):
            self.region = connection.region
        else:
            self.region = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)


class TaggedEC2Object(EC2Object):
    """
    Any EC2 resource that can be tagged should be represented
    by a Python object that subclasses this class.  This class
    has the mechanism in place to handle the tagSet element in
    the Describe* responses.  If tags are found, it will create
    a TagSet object and allow it to parse and collect the tags
    into a dict that is stored in the "tags" attribute of the
    object.
    """

    def __init__(self, connection=None):
        super(TaggedEC2Object, self).__init__(connection)
        self.tags = TagSet()

    def startElement(self, name, attrs, connection):
        if name == 'tagSet':
            return self.tags
        else:
            return None

    def add_tag(self, key, value='', dry_run=False):
        """
        Add a tag to this object.  Tags are stored by AWS and can be used
        to organize and filter resources.  Adding a tag involves a round-trip
        to the EC2 service.

        :type key: str
        :param key: The key or name of the tag being stored.

        :type value: str
        :param value: An optional value that can be stored with the tag.
                      If you want only the tag name and no value, the
                      value should be the empty string.
        """
        self.add_tags({key: value}, dry_run)

    def add_tags(self, tags, dry_run=False):
        """
        Add tags to this object.  Tags are stored by AWS and can be used
        to organize and filter resources.  Adding tags involves a round-trip
        to the EC2 service.

        :type tags: dict
        :param tags: A dictionary of key-value pairs for the tags being stored.
                     If for some tags you want only the name and no value, the
                     corresponding value for that tag name should be an empty
                     string.
        """
        status = self.connection.create_tags(
            [self.id],
            tags,
            dry_run=dry_run
        )
        if self.tags is None:
            self.tags = TagSet()
        self.tags.update(tags)

    def remove_tag(self, key, value=None, dry_run=False):
        """
        Remove a tag from this object.  Removing a tag involves a round-trip
        to the EC2 service.

        :type key: str
        :param key: The key or name of the tag being stored.

        :type value: str
        :param value: An optional value that can be stored with the tag.
                      If a value is provided, it must match the value currently
                      stored in EC2.  If not, the tag will not be removed.  If
                      a value of None is provided, the tag will be
                      unconditionally deleted.
                      NOTE: There is an important distinction between a value
                      of '' and a value of None.
        """
        self.remove_tags({key: value}, dry_run)

    def remove_tags(self, tags, dry_run=False):
        """
        Removes tags from this object.  Removing tags involves a round-trip
        to the EC2 service.

        :type tags: dict
        :param tags: A dictionary of key-value pairs for the tags being removed.
                     For each key, the provided value must match the value
                     currently stored in EC2.  If not, that particular tag will
                     not be removed.  However, if a value of None is provided,
                     the tag will be unconditionally deleted.
                     NOTE: There is an important distinction between a value of
                     '' and a value of None.
        """
        status = self.connection.delete_tags(
            [self.id],
            tags,
            dry_run=dry_run
        )
        for key, value in tags.items():
            if key in self.tags:
                if value is None or value == self.tags[key]:
                    del self.tags[key]
