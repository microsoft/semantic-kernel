from boto import handler
import xml.sax


class Tag(object):
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Key':
            self.key = value
        elif name == 'Value':
            self.value = value

    def to_xml(self):
        return '<Tag><Key>%s</Key><Value>%s</Value></Tag>' % (
            self.key, self.value)

    def __eq__(self, other):
        return (self.key == other.key and self.value == other.value)


class TagSet(list):
    def startElement(self, name, attrs, connection):
        if name == 'Tag':
            tag = Tag()
            self.append(tag)
            return tag
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

    def add_tag(self, key, value):
        tag = Tag(key, value)
        self.append(tag)

    def to_xml(self):
        xml = '<TagSet>'
        for tag in self:
            xml += tag.to_xml()
        xml += '</TagSet>'
        return xml


class Tags(list):
    """A container for the tags associated with a bucket."""

    def startElement(self, name, attrs, connection):
        if name == 'TagSet':
            tag_set = TagSet()
            self.append(tag_set)
            return tag_set
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

    def to_xml(self):
        xml = '<Tagging>'
        for tag_set in self:
            xml += tag_set.to_xml()
        xml +='</Tagging>'
        return xml

    def add_tag_set(self, tag_set):
        self.append(tag_set)
