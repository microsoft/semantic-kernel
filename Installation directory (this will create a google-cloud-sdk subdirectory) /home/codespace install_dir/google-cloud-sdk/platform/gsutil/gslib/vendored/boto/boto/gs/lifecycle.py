# Copyright 2013 Google Inc.
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

from boto.exception import InvalidLifecycleConfigError

# Relevant tags for the lifecycle configuration XML document.
LIFECYCLE_CONFIG      = 'LifecycleConfiguration'
RULE                  = 'Rule'
ACTION                = 'Action'
DELETE                = 'Delete'
SET_STORAGE_CLASS     = 'SetStorageClass'
CONDITION             = 'Condition'
AGE                   = 'Age'
CREATED_BEFORE        = 'CreatedBefore'
NUM_NEWER_VERSIONS    = 'NumberOfNewerVersions'
IS_LIVE               = 'IsLive'
MATCHES_STORAGE_CLASS = 'MatchesStorageClass'

# List of all action elements.
LEGAL_ACTIONS = [DELETE, SET_STORAGE_CLASS]
# List of all condition elements.
LEGAL_CONDITIONS = [AGE, CREATED_BEFORE, NUM_NEWER_VERSIONS, IS_LIVE,
                    MATCHES_STORAGE_CLASS]
# List of conditions elements that may be repeated.
LEGAL_REPEATABLE_CONDITIONS = [MATCHES_STORAGE_CLASS]

class Rule(object):
    """
    A lifecycle rule for a bucket.

    :ivar action: Action to be taken.

    :ivar action_text: The text value for the specified action, if any.

    :ivar conditions: A dictionary of conditions that specify when the action
    should be taken. Each item in the dictionary represents the name and
    value (or a list of multiple values, if applicable) of a condition.
    """

    def __init__(self, action=None, action_text=None, conditions=None):
        self.action = action
        self.action_text = action_text
        self.conditions = conditions or {}

        # Name of the current enclosing tag (used to validate the schema).
        self.current_tag = RULE

    def validateStartTag(self, tag, parent):
        """Verify parent of the start tag."""
        if self.current_tag != parent:
            raise InvalidLifecycleConfigError(
                'Invalid tag %s found inside %s tag' % (tag, self.current_tag))

    def validateEndTag(self, tag):
        """Verify end tag against the start tag."""
        if tag != self.current_tag:
            raise InvalidLifecycleConfigError(
                'Mismatched start and end tags (%s/%s)' %
                (self.current_tag, tag))

    def startElement(self, name, attrs, connection):
        if name == ACTION:
            self.validateStartTag(name, RULE)
        elif name in LEGAL_ACTIONS:
            self.validateStartTag(name, ACTION)
            # Verify there is only one action tag in the rule.
            if self.action is not None:
                raise InvalidLifecycleConfigError(
                    'Only one action tag is allowed in each rule')
            self.action = name
        elif name == CONDITION:
            self.validateStartTag(name, RULE)
        elif name in LEGAL_CONDITIONS:
            self.validateStartTag(name, CONDITION)
            # Verify there is no duplicate conditions.
            if (name in self.conditions and
                name not in LEGAL_REPEATABLE_CONDITIONS):
                raise InvalidLifecycleConfigError(
                    'Found duplicate non-repeatable conditions %s' % name)
        else:
            raise InvalidLifecycleConfigError('Unsupported tag ' + name)
        self.current_tag = name

    def endElement(self, name, value, connection):
        self.validateEndTag(name)
        if name == RULE:
            # We have to validate the rule after it is fully populated because
            # the action and condition elements could be in any order.
            self.validate()
        elif name == ACTION:
            self.current_tag = RULE
        elif name in LEGAL_ACTIONS:
            if name == SET_STORAGE_CLASS and value is not None:
                self.action_text = value.strip()
            self.current_tag = ACTION
        elif name == CONDITION:
            self.current_tag = RULE
        elif name in LEGAL_CONDITIONS:
            self.current_tag = CONDITION
            # Some conditions specify a list of values.
            if name in LEGAL_REPEATABLE_CONDITIONS:
                if name not in self.conditions:
                    self.conditions[name] = []
                self.conditions[name].append(value.strip())
            else:
                self.conditions[name] = value.strip()
        else:
            raise InvalidLifecycleConfigError('Unsupported end tag ' + name)

    def validate(self):
        """Validate the rule."""
        if not self.action:
            raise InvalidLifecycleConfigError(
                'No action was specified in the rule')
        if not self.conditions:
            raise InvalidLifecycleConfigError(
                'No condition was specified for action %s' % self.action)

    def to_xml(self):
        """Convert the rule into XML string representation."""
        s = ['<' + RULE + '>']
        s.append('<' + ACTION + '>')
        if self.action_text:
            s.extend(['<' + self.action + '>',
                      self.action_text,
                      '</' + self.action + '>'])
        else:
            s.append('<' + self.action + '/>')
        s.append('</' + ACTION + '>')
        s.append('<' + CONDITION + '>')
        for condition_name in self.conditions:
            if condition_name not in LEGAL_CONDITIONS:
                continue
            if condition_name in LEGAL_REPEATABLE_CONDITIONS:
                condition_values = self.conditions[condition_name]
            else:
                # Wrap condition value in a list, allowing us to iterate over
                # all condition values using the same logic.
                condition_values = [self.conditions[condition_name]]
            for condition_value in condition_values:
                s.extend(['<' + condition_name + '>',
                          condition_value,
                          '</' + condition_name + '>'])
        s.append('</' + CONDITION + '>')
        s.append('</' + RULE + '>')
        return ''.join(s)

class LifecycleConfig(list):
    """
    A container of rules associated with a lifecycle configuration.
    """

    def __init__(self):
        # Track if root tag has been seen.
        self.has_root_tag = False

    def startElement(self, name, attrs, connection):
        if name == LIFECYCLE_CONFIG:
            if self.has_root_tag:
                raise InvalidLifecycleConfigError(
                    'Only one root tag is allowed in the XML')
            self.has_root_tag = True
        elif name == RULE:
            if not self.has_root_tag:
                raise InvalidLifecycleConfigError('Invalid root tag ' + name)
            rule = Rule()
            self.append(rule)
            return rule
        else:
            raise InvalidLifecycleConfigError('Unsupported tag ' + name)

    def endElement(self, name, value, connection):
        if name == LIFECYCLE_CONFIG:
            pass
        else:
            raise InvalidLifecycleConfigError('Unsupported end tag ' + name)

    def to_xml(self):
        """Convert LifecycleConfig object into XML string representation."""
        s = ['<?xml version="1.0" encoding="UTF-8"?>']
        s.append('<' + LIFECYCLE_CONFIG + '>')
        for rule in self:
            s.append(rule.to_xml())
        s.append('</' + LIFECYCLE_CONFIG + '>')
        return ''.join(s)

    def add_rule(self, action, action_text, conditions):
        """
        Add a rule to this Lifecycle configuration.  This only adds the rule to
        the local copy.  To install the new rule(s) on the bucket, you need to
        pass this Lifecycle config object to the configure_lifecycle method of
        the Bucket object.

        :type action: str
        :param action: Action to be taken.

        :type action_text: str
        :param action_text: Value for the specified action.

        :type conditions: dict
        :param conditions: A dictionary of conditions that specify when the
        action should be taken. Each item in the dictionary represents the name
        and value of a condition.
        """
        rule = Rule(action, action_text, conditions)
        self.append(rule)
