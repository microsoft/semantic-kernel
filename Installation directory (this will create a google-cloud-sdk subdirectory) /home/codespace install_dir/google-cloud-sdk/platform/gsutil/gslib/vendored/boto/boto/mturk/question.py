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

import xml.sax.saxutils

class Question(object):
    template = "<Question>%(items)s</Question>"

    def __init__(self, identifier, content, answer_spec,
                 is_required=False, display_name=None):
        # copy all of the parameters into object attributes
        self.__dict__.update(vars())
        del self.self

    def get_as_params(self, label='Question'):
        return {label: self.get_as_xml()}

    def get_as_xml(self):
        items = [
            SimpleField('QuestionIdentifier', self.identifier),
            SimpleField('IsRequired', str(self.is_required).lower()),
            self.content,
            self.answer_spec,
        ]
        if self.display_name is not None:
            items.insert(1, SimpleField('DisplayName', self.display_name))
        items = ''.join(item.get_as_xml() for item in items)
        return self.template % vars()

try:
    from lxml import etree

    class ValidatingXML(object):

        def validate(self):
            import urllib2
            schema_src_file = urllib2.urlopen(self.schema_url)
            schema_doc = etree.parse(schema_src_file)
            schema = etree.XMLSchema(schema_doc)
            doc = etree.fromstring(self.get_as_xml())
            schema.assertValid(doc)
except ImportError:
    class ValidatingXML(object):

        def validate(self):
            pass


class ExternalQuestion(ValidatingXML):
    """
    An object for constructing an External Question.
    """
    schema_url = "http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd"
    template = '<ExternalQuestion xmlns="%(schema_url)s"><ExternalURL>%%(external_url)s</ExternalURL><FrameHeight>%%(frame_height)s</FrameHeight></ExternalQuestion>' % vars()

    def __init__(self, external_url, frame_height):
        self.external_url = xml.sax.saxutils.escape( external_url )
        self.frame_height = frame_height

    def get_as_params(self, label='ExternalQuestion'):
        return {label: self.get_as_xml()}

    def get_as_xml(self):
        return self.template % vars(self)


class XMLTemplate(object):
    def get_as_xml(self):
        return self.template % vars(self)


class SimpleField(XMLTemplate):
    """
    A Simple name/value pair that can be easily rendered as XML.

    >>> SimpleField('Text', 'A text string').get_as_xml()
    '<Text>A text string</Text>'
    """
    template = '<%(field)s>%(value)s</%(field)s>'

    def __init__(self, field, value):
        self.field = field
        self.value = value


class Binary(XMLTemplate):
    template = """<Binary><MimeType><Type>%(type)s</Type><SubType>%(subtype)s</SubType></MimeType><DataURL>%(url)s</DataURL><AltText>%(alt_text)s</AltText></Binary>"""

    def __init__(self, type, subtype, url, alt_text):
        self.__dict__.update(vars())
        del self.self


class List(list):
    """A bulleted list suitable for OrderedContent or Overview content"""
    def get_as_xml(self):
        items = ''.join('<ListItem>%s</ListItem>' % item for item in self)
        return '<List>%s</List>' % items


class Application(object):
    template = "<Application><%(class_)s>%(content)s</%(class_)s></Application>"
    parameter_template = "<Name>%(name)s</Name><Value>%(value)s</Value>"

    def __init__(self, width, height, **parameters):
        self.width = width
        self.height = height
        self.parameters = parameters

    def get_inner_content(self, content):
        content.append_field('Width', self.width)
        content.append_field('Height', self.height)
        for name, value in self.parameters.items():
            value = self.parameter_template % vars()
            content.append_field('ApplicationParameter', value)

    def get_as_xml(self):
        content = OrderedContent()
        self.get_inner_content(content)
        content = content.get_as_xml()
        class_ = self.__class__.__name__
        return self.template % vars()


class HTMLQuestion(ValidatingXML):
    schema_url = 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd'
    template = '<HTMLQuestion xmlns=\"%(schema_url)s\"><HTMLContent><![CDATA[<!DOCTYPE html>%%(html_form)s]]></HTMLContent><FrameHeight>%%(frame_height)s</FrameHeight></HTMLQuestion>' % vars()

    def __init__(self, html_form, frame_height):
        self.html_form = html_form
        self.frame_height = frame_height

    def get_as_params(self, label="HTMLQuestion"):
        return {label: self.get_as_xml()}

    def get_as_xml(self):
        return self.template % vars(self)


class JavaApplet(Application):
    def __init__(self, path, filename, *args, **kwargs):
        self.path = path
        self.filename = filename
        super(JavaApplet, self).__init__(*args, **kwargs)

    def get_inner_content(self, content):
        content = OrderedContent()
        content.append_field('AppletPath', self.path)
        content.append_field('AppletFilename', self.filename)
        super(JavaApplet, self).get_inner_content(content)


class Flash(Application):
    def __init__(self, url, *args, **kwargs):
        self.url = url
        super(Flash, self).__init__(*args, **kwargs)

    def get_inner_content(self, content):
        content = OrderedContent()
        content.append_field('FlashMovieURL', self.url)
        super(Flash, self).get_inner_content(content)


class FormattedContent(XMLTemplate):
    schema_url = 'http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/FormattedContentXHTMLSubset.xsd'
    template = '<FormattedContent><![CDATA[%(content)s]]></FormattedContent>'

    def __init__(self, content):
        self.content = content


class OrderedContent(list):

    def append_field(self, field, value):
        self.append(SimpleField(field, value))

    def get_as_xml(self):
        return ''.join(item.get_as_xml() for item in self)


class Overview(OrderedContent):
    template = '<Overview>%(content)s</Overview>'

    def get_as_params(self, label='Overview'):
        return {label: self.get_as_xml()}

    def get_as_xml(self):
        content = super(Overview, self).get_as_xml()
        return self.template % vars()


class QuestionForm(ValidatingXML, list):
    """
    From the AMT API docs:

    The top-most element of the QuestionForm data structure is a
    QuestionForm element. This element contains optional Overview
    elements and one or more Question elements. There can be any
    number of these two element types listed in any order. The
    following example structure has an Overview element and a
    Question element followed by a second Overview element and
    Question element--all within the same QuestionForm.

    ::

        <QuestionForm xmlns="[the QuestionForm schema URL]">
            <Overview>
                [...]
            </Overview>
            <Question>
                [...]
            </Question>
            <Overview>
                [...]
            </Overview>
            <Question>
                [...]
            </Question>
            [...]
        </QuestionForm>

    QuestionForm is implemented as a list, so to construct a
    QuestionForm, simply append Questions and Overviews (with at least
    one Question).
    """
    schema_url = "http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionForm.xsd"
    xml_template = """<QuestionForm xmlns="%(schema_url)s">%%(items)s</QuestionForm>""" % vars()

    def is_valid(self):
        return (
            any(isinstance(item, Question) for item in self)
            and
            all(isinstance(item, (Question, Overview)) for item in self)
            )

    def get_as_xml(self):
        assert self.is_valid(), "QuestionForm contains invalid elements"
        items = ''.join(item.get_as_xml() for item in self)
        return self.xml_template % vars()


class QuestionContent(OrderedContent):
    template = '<QuestionContent>%(content)s</QuestionContent>'

    def get_as_xml(self):
        content = super(QuestionContent, self).get_as_xml()
        return self.template % vars()


class AnswerSpecification(object):
    template = '<AnswerSpecification>%(spec)s</AnswerSpecification>'

    def __init__(self, spec):
        self.spec = spec

    def get_as_xml(self):
        spec = self.spec.get_as_xml()
        return self.template % vars()


class Constraints(OrderedContent):
    template = '<Constraints>%(content)s</Constraints>'

    def get_as_xml(self):
        content = super(Constraints, self).get_as_xml()
        return self.template % vars()


class Constraint(object):
    def get_attributes(self):
        pairs = zip(self.attribute_names, self.attribute_values)
        attrs = ' '.join(
            '%s="%d"' % (name, value)
            for (name, value) in pairs
            if value is not None
            )
        return attrs

    def get_as_xml(self):
        attrs = self.get_attributes()
        return self.template % vars()


class NumericConstraint(Constraint):
    attribute_names = 'minValue', 'maxValue'
    template = '<IsNumeric %(attrs)s />'

    def __init__(self, min_value=None, max_value=None):
        self.attribute_values = min_value, max_value


class LengthConstraint(Constraint):
    attribute_names = 'minLength', 'maxLength'
    template = '<Length %(attrs)s />'

    def __init__(self, min_length=None, max_length=None):
        self.attribute_values = min_length, max_length


class RegExConstraint(Constraint):
    attribute_names = 'regex', 'errorText', 'flags'
    template = '<AnswerFormatRegex %(attrs)s />'

    def __init__(self, pattern, error_text=None, flags=None):
        self.attribute_values = pattern, error_text, flags

    def get_attributes(self):
        pairs = zip(self.attribute_names, self.attribute_values)
        attrs = ' '.join(
            '%s="%s"' % (name, value)
            for (name, value) in pairs
            if value is not None
            )
        return attrs


class NumberOfLinesSuggestion(object):
    template = '<NumberOfLinesSuggestion>%(num_lines)s</NumberOfLinesSuggestion>'

    def __init__(self, num_lines=1):
        self.num_lines = num_lines

    def get_as_xml(self):
        num_lines = self.num_lines
        return self.template % vars()


class FreeTextAnswer(object):
    template = '<FreeTextAnswer>%(items)s</FreeTextAnswer>'

    def __init__(self, default=None, constraints=None, num_lines=None):
        self.default = default
        if constraints is None:
            self.constraints = Constraints()
        else:
            self.constraints = Constraints(constraints)
        self.num_lines = num_lines

    def get_as_xml(self):
        items = [self.constraints]
        if self.default:
            items.append(SimpleField('DefaultText', self.default))
        if self.num_lines:
            items.append(NumberOfLinesSuggestion(self.num_lines))
        items = ''.join(item.get_as_xml() for item in items)
        return self.template % vars()


class FileUploadAnswer(object):
    template = """<FileUploadAnswer><MaxFileSizeInBytes>%(max_bytes)d</MaxFileSizeInBytes><MinFileSizeInBytes>%(min_bytes)d</MinFileSizeInBytes></FileUploadAnswer>"""

    def __init__(self, min_bytes, max_bytes):
        assert 0 <= min_bytes <= max_bytes <= 2 * 10 ** 9
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def get_as_xml(self):
        return self.template % vars(self)


class SelectionAnswer(object):
    """
    A class to generate SelectionAnswer XML data structures.
    Does not yet implement Binary selection options.
    """
    SELECTIONANSWER_XML_TEMPLATE = """<SelectionAnswer>%s%s<Selections>%s</Selections></SelectionAnswer>""" # % (count_xml, style_xml, selections_xml)
    SELECTION_XML_TEMPLATE = """<Selection><SelectionIdentifier>%s</SelectionIdentifier>%s</Selection>""" # (identifier, value_xml)
    SELECTION_VALUE_XML_TEMPLATE = """<%s>%s</%s>""" # (type, value, type)
    STYLE_XML_TEMPLATE = """<StyleSuggestion>%s</StyleSuggestion>""" # (style)
    MIN_SELECTION_COUNT_XML_TEMPLATE = """<MinSelectionCount>%s</MinSelectionCount>""" # count
    MAX_SELECTION_COUNT_XML_TEMPLATE = """<MaxSelectionCount>%s</MaxSelectionCount>""" # count
    ACCEPTED_STYLES = ['radiobutton', 'dropdown', 'checkbox', 'list', 'combobox', 'multichooser']
    OTHER_SELECTION_ELEMENT_NAME = 'OtherSelection'

    def __init__(self, min=1, max=1, style=None, selections=None, type='text', other=False):

        if style is not None:
            if style in SelectionAnswer.ACCEPTED_STYLES:
                self.style_suggestion = style
            else:
                raise ValueError("style '%s' not recognized; should be one of %s" % (style, ', '.join(SelectionAnswer.ACCEPTED_STYLES)))
        else:
            self.style_suggestion = None

        if selections is None:
            raise ValueError("SelectionAnswer.__init__(): selections must be a non-empty list of (content, identifier) tuples")
        else:
            self.selections = selections

        self.min_selections = min
        self.max_selections = max

        assert len(selections) >= self.min_selections, "# of selections is less than minimum of %d" % self.min_selections
        #assert len(selections) <= self.max_selections, "# of selections exceeds maximum of %d" % self.max_selections

        self.type = type

        self.other = other

    def get_as_xml(self):
        if self.type == 'text':
            TYPE_TAG = "Text"
        elif self.type == 'binary':
            TYPE_TAG = "Binary"
        else:
            raise ValueError("illegal type: %s; must be either 'text' or 'binary'" % str(self.type))

        # build list of <Selection> elements
        selections_xml = ""
        for tpl in self.selections:
            value_xml = SelectionAnswer.SELECTION_VALUE_XML_TEMPLATE % (TYPE_TAG, tpl[0], TYPE_TAG)
            selection_xml = SelectionAnswer.SELECTION_XML_TEMPLATE % (tpl[1], value_xml)
            selections_xml += selection_xml

        if self.other:
            # add OtherSelection element as xml if available
            if hasattr(self.other, 'get_as_xml'):
                assert isinstance(self.other, FreeTextAnswer), 'OtherSelection can only be a FreeTextAnswer'
                selections_xml += self.other.get_as_xml().replace('FreeTextAnswer', 'OtherSelection')
            else:
                selections_xml += "<OtherSelection />"

        if self.style_suggestion is not None:
            style_xml = SelectionAnswer.STYLE_XML_TEMPLATE % self.style_suggestion
        else:
            style_xml = ""

        if self.style_suggestion != 'radiobutton':
            count_xml = SelectionAnswer.MIN_SELECTION_COUNT_XML_TEMPLATE %self.min_selections
            count_xml += SelectionAnswer.MAX_SELECTION_COUNT_XML_TEMPLATE %self.max_selections
        else:
            count_xml = ""

        ret = SelectionAnswer.SELECTIONANSWER_XML_TEMPLATE % (count_xml, style_xml, selections_xml)

        # return XML
        return ret
