# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
# All rights reserved.
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
Base class to make checking the certs easier.
"""


# We subclass from ``object`` instead of ``TestCase`` here so that this doesn't
# add noise to the test suite (otherwise these no-ops would run on every
# import).
class ServiceCertVerificationTest(object):
    ssl = True

    # SUBCLASSES MUST OVERRIDE THIS!
    # Something like ``boto.sqs.regions()``...
    regions = []

    def test_certs(self):
        self.assertTrue(len(self.regions) > 0)

        for region in self.regions:
            special_access_required = False

            for snippet in ('gov', 'cn-'):
                if snippet in region.name:
                    special_access_required = True
                    break

            try:
                c = region.connect()
                self.sample_service_call(c)
            except:
                # This is bad (because the SSL cert failed). Re-raise the
                # exception.
                if not special_access_required:
                    raise

    def sample_service_call(self, conn):
        """
        Subclasses should override this method to do a service call that will
        always succeed (like fetch a list, even if it's empty).
        """
        pass
