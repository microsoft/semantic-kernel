# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
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

from boto import handler
import xml.sax

class Deleted(object):
    """
    A successfully deleted object in a multi-object delete request.

    :ivar key: Key name of the object that was deleted.
    
    :ivar version_id: Version id of the object that was deleted.
    
    :ivar delete_marker: If True, indicates the object deleted
        was a DeleteMarker.
        
    :ivar delete_marker_version_id: Version ID of the delete marker
        deleted.
    """
    def __init__(self, key=None, version_id=None,
                 delete_marker=False, delete_marker_version_id=None):
        self.key = key
        self.version_id = version_id
        self.delete_marker = delete_marker
        self.delete_marker_version_id = delete_marker_version_id
        
    def __repr__(self):
        if self.version_id:
            return '<Deleted: %s.%s>' % (self.key, self.version_id)
        else:
            return '<Deleted: %s>' % self.key
        
    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Key':
            self.key = value
        elif name == 'VersionId':
            self.version_id = value
        elif name == 'DeleteMarker':
            if value.lower() == 'true':
                self.delete_marker = True
        elif name == 'DeleteMarkerVersionId':
            self.delete_marker_version_id = value
        else:
            setattr(self, name, value)
            
class Error(object):
    """
    An unsuccessful deleted object in a multi-object delete request.

    :ivar key: Key name of the object that was not deleted.
    
    :ivar version_id: Version id of the object that was not deleted.
    
    :ivar code: Status code of the failed delete operation.
        
    :ivar message: Status message of the failed delete operation.
    """
    def __init__(self, key=None, version_id=None,
                 code=None, message=None):
        self.key = key
        self.version_id = version_id
        self.code = code
        self.message = message
        
    def __repr__(self):
        if self.version_id:
            return '<Error: %s.%s(%s)>' % (self.key, self.version_id,
                                           self.code)
        else:
            return '<Error: %s(%s)>' % (self.key, self.code)
        
    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Key':
            self.key = value
        elif name == 'VersionId':
            self.version_id = value
        elif name == 'Code':
            self.code = value
        elif name == 'Message':
            self.message = value
        else:
            setattr(self, name, value)
            
class MultiDeleteResult(object):
    """
    The status returned from a MultiObject Delete request.

    :ivar deleted: A list of successfully deleted objects.  Note that if
        the quiet flag was specified in the request, this list will
        be empty because only error responses would be returned.

    :ivar errors: A list of unsuccessfully deleted objects.
    """

    def __init__(self, bucket=None):
        self.bucket = None
        self.deleted = []
        self.errors = []

    def startElement(self, name, attrs, connection):
        if name == 'Deleted':
            d = Deleted()
            self.deleted.append(d)
            return d
        elif name == 'Error':
            e = Error()
            self.errors.append(e)
            return e
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)
 
