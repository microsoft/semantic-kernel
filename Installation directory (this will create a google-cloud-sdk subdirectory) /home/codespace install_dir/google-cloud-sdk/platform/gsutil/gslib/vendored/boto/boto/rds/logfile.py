# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2014 Jumping Qu http://newrice.blogspot.com/
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

class LogFile(object):

    def __init__(self, connection=None):
        self.connection = connection
        self.size = None
        self.log_filename = None
        self.last_written = None
        
    def __repr__(self):
        #return '(%s, %s, %s)' % (self.logfilename, self.size, self.lastwritten)
        return '%s' % (self.log_filename)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'LastWritten':
            self.last_written = value
        elif name == 'LogFileName':
            self.log_filename = value
        elif name == 'Size':
            self.size = value
        else:
            setattr(self, name, value)


class LogFileObject(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.log_filename = None

    def __repr__(self):
        return "LogFileObject: %s/%s" % (self.dbinstance_id, self.log_filename)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'LogFileData':
            self.data = value
        elif name == 'AdditionalDataPending':
            self.additional_data_pending = value
        elif name == 'Marker':
            self.marker = value
        else:
            setattr(self, name, value)
