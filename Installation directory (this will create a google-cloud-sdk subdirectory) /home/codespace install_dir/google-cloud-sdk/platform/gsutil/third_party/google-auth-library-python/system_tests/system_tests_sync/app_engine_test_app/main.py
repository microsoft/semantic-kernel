# Copyright 2016 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""App Engine standard application that runs basic system tests for
google.auth.app_engine.
This application has to run tests manually instead of using pytest because
pytest currently doesn't work on App Engine standard.
"""

import contextlib
import json
import sys
from StringIO import StringIO
import traceback

from google.appengine.api import app_identity
import google.auth
from google.auth import _helpers
from google.auth import app_engine
import google.auth.transport.urllib3
import urllib3.contrib.appengine
import webapp2

FAILED_TEST_TMPL = """
Test {} failed: {}
Stacktrace:
{}
Captured output:
{}
"""
TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"
HTTP = urllib3.contrib.appengine.AppEngineManager()
HTTP_REQUEST = google.auth.transport.urllib3.Request(HTTP)


def test_credentials():
    credentials = app_engine.Credentials()
    scoped_credentials = credentials.with_scopes([EMAIL_SCOPE])

    scoped_credentials.refresh(None)

    assert scoped_credentials.valid
    assert scoped_credentials.token is not None

    # Get token info and verify scope
    url = _helpers.update_query(
        TOKEN_INFO_URL, {"access_token": scoped_credentials.token}
    )
    response = HTTP_REQUEST(url=url, method="GET")
    token_info = json.loads(response.data.decode("utf-8"))

    assert token_info["scope"] == EMAIL_SCOPE


def test_default():
    credentials, project_id = google.auth.default()

    assert isinstance(credentials, app_engine.Credentials)
    assert project_id == app_identity.get_application_id()


@contextlib.contextmanager
def capture():
    """Context manager that captures stderr and stdout."""
    oldout, olderr = sys.stdout, sys.stderr
    try:
        out = StringIO()
        sys.stdout, sys.stderr = out, out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr


def run_test_func(func):
    with capture() as capsys:
        try:
            func()
            return True, ""
        except Exception as exc:
            output = FAILED_TEST_TMPL.format(
                func.func_name, exc, traceback.format_exc(), capsys.getvalue()
            )
            return False, output


def run_tests():
    """Runs all tests.
    Returns:
        Tuple[bool, str]: A tuple containing True if all tests pass, False
        otherwise, and any captured output from the tests.
    """
    status = True
    output = ""

    tests = (test_credentials, test_default)

    for test in tests:
        test_status, test_output = run_test_func(test)
        status = status and test_status
        output += test_output

    return status, output


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers["content-type"] = "text/plain"

        status, output = run_tests()

        if not status:
            self.response.status = 500

        self.response.write(output)


app = webapp2.WSGIApplication([("/", MainHandler)], debug=True)