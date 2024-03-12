# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interface to handle end to end flow of U2F signing."""

import sys

from pyu2f.convenience import baseauthenticator
from pyu2f.convenience import customauthenticator
from pyu2f.convenience import localauthenticator


def CreateCompositeAuthenticator(origin):
  authenticators = [customauthenticator.CustomAuthenticator(origin),
                    localauthenticator.LocalAuthenticator(origin)]
  return CompositeAuthenticator(authenticators)


class CompositeAuthenticator(baseauthenticator.BaseAuthenticator):
  """Composes multiple authenticators into a single authenticator.

  Priority is based on the order of the list initialized with the instance.
  """

  def __init__(self, authenticators):
    self.authenticators = authenticators

  def Authenticate(self, app_id, challenge_data,
                   print_callback=sys.stderr.write):
    """See base class."""
    for authenticator in self.authenticators:
      if authenticator.IsAvailable():
        result = authenticator.Authenticate(app_id,
                                            challenge_data,
                                            print_callback)
        return result

    raise ValueError('No valid authenticators found')

  def IsAvailable(self):
    """See base class."""
    return True
