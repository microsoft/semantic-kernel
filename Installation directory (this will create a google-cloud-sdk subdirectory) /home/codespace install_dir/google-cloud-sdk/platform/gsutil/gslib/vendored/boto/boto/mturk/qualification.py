# Copyright (c) 2008 Chris Moyer http://coredumped.org/
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

class Qualifications(object):

    def __init__(self, requirements=None):
        if requirements is None:
            requirements = []
        self.requirements = requirements

    def add(self, req):
        self.requirements.append(req)

    def get_as_params(self):
        params = {}
        assert(len(self.requirements) <= 10)
        for n, req in enumerate(self.requirements):
            reqparams = req.get_as_params()
            for rp in reqparams:
                params['QualificationRequirement.%s.%s' % ((n+1), rp) ] = reqparams[rp]
        return params


class Requirement(object):
    """
    Representation of a single requirement
    """

    def __init__(self, qualification_type_id, comparator, integer_value=None, required_to_preview=False):
        self.qualification_type_id = qualification_type_id
        self.comparator = comparator
        self.integer_value = integer_value
        self.required_to_preview = required_to_preview

    def get_as_params(self):
        params =  {
            "QualificationTypeId": self.qualification_type_id,
            "Comparator": self.comparator,
        }
        if self.comparator in ('In', 'NotIn'):
            for i, integer_value in enumerate(self.integer_value, 1):
                params['IntegerValue.%d' % i] = integer_value
        elif self.comparator not in ('Exists', 'DoesNotExist') and self.integer_value is not None:
            params['IntegerValue'] = self.integer_value
        if self.required_to_preview:
            params['RequiredToPreview'] = "true"
        return params

class PercentAssignmentsSubmittedRequirement(Requirement):
    """
    The percentage of assignments the Worker has submitted, over all assignments the Worker has accepted. The value is an integer between 0 and 100.
    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(PercentAssignmentsSubmittedRequirement, self).__init__(qualification_type_id="00000000000000000000", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)

class PercentAssignmentsAbandonedRequirement(Requirement):
    """
    The percentage of assignments the Worker has abandoned (allowed the deadline to elapse), over all assignments the Worker has accepted. The value is an integer between 0 and 100.
    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(PercentAssignmentsAbandonedRequirement, self).__init__(qualification_type_id="00000000000000000070", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)

class PercentAssignmentsReturnedRequirement(Requirement):
    """
    The percentage of assignments the Worker has returned, over all assignments the Worker has accepted. The value is an integer between 0 and 100.
    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(PercentAssignmentsReturnedRequirement, self).__init__(qualification_type_id="000000000000000000E0", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)

class PercentAssignmentsApprovedRequirement(Requirement):
    """
    The percentage of assignments the Worker has submitted that were subsequently approved by the Requester, over all assignments the Worker has submitted. The value is an integer between 0 and 100.
    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(PercentAssignmentsApprovedRequirement, self).__init__(qualification_type_id="000000000000000000L0", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)

class PercentAssignmentsRejectedRequirement(Requirement):
    """
    The percentage of assignments the Worker has submitted that were subsequently rejected by the Requester, over all assignments the Worker has submitted. The value is an integer between 0 and 100.
    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(PercentAssignmentsRejectedRequirement, self).__init__(qualification_type_id="000000000000000000S0", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)

class NumberHitsApprovedRequirement(Requirement):
    """
    Specifies the total number of HITs submitted by a Worker that have been approved. The value is an integer greater than or equal to 0.

    If specifying a Country and Subdivision, use a tuple of valid  ISO 3166 country code and ISO 3166-2 subdivision code, e.g. ('US', 'CA') for the US State of California.

    When using the 'In' and 'NotIn', locale should be a list of Countries and/or (Country, Subdivision) tuples.

    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(NumberHitsApprovedRequirement, self).__init__(qualification_type_id="00000000000000000040", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)

class LocaleRequirement(Requirement):
    """
    A Qualification requirement based on the Worker's location. The Worker's location is specified by the Worker to Mechanical Turk when the Worker creates his account.
    """

    def __init__(self, comparator, locale, required_to_preview=False):
        super(LocaleRequirement, self).__init__(qualification_type_id="00000000000000000071", comparator=comparator, integer_value=None, required_to_preview=required_to_preview)
        self.locale = locale

    def get_as_params(self):
        params =  {
            "QualificationTypeId": self.qualification_type_id,
            "Comparator": self.comparator,
        }
        if self.comparator in ('In', 'NotIn'):
            for i, locale in enumerate(self.locale, 1):
                if isinstance(locale, tuple):
                    params['LocaleValue.%d.Country' % i] = locale[0]
                    params['LocaleValue.%d.Subdivision' % i] = locale[1]
                else:
                    params['LocaleValue.%d.Country' % i] = locale
        else:
            if isinstance(self.locale, tuple):
                params['LocaleValue.Country'] = self.locale[0]
                params['LocaleValue.Subdivision'] = self.locale[1]
            else:
                params['LocaleValue.Country'] = self.locale
        if self.required_to_preview:
            params['RequiredToPreview'] = "true"
        return params

class AdultRequirement(Requirement):
    """
    Requires workers to acknowledge that they are over 18 and that they agree to work on potentially offensive content. The value type is boolean, 1 (required), 0 (not required, the default).
    """

    def __init__(self, comparator, integer_value, required_to_preview=False):
        super(AdultRequirement, self).__init__(qualification_type_id="00000000000000000060", comparator=comparator, integer_value=integer_value, required_to_preview=required_to_preview)
