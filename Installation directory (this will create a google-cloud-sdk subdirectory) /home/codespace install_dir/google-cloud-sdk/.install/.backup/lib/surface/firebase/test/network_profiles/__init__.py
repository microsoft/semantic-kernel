# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""The 'gcloud firebase test network-profiles' command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class NetworkProfiles(base.Group):
  """Explore network profiles available for testing.

  A network traffic profile consists of a set of parameters to emulate network
  conditions when running a test. This feature only works on physical devices.
  The network shaping parameters are:

  - *RULE*: Where to apply traffic shaping. The UP rule shapes the
    connection from the device to the internet. The DOWN rule shapes the
    connection from the internet to the device.
  - *DELAY*: The delay in packet transmission, in ms.
  - *LOSS_RATIO*: The ratio of packets dropped during transmission.
  - *DUPLICATION_RATIO*: The ratio of packets duplicated during
    transmission.
  - *BANDWIDTH*: The average packet transmission rate in kbits/s, as
    defined by the token bucket algorithm.
  - *BURST*: The total size, in kbits, by which packets can exceed the
    bandwidth, as defined by the token bucket algorithm.
  """

  detailed_help = {
      'EXAMPLES': """\
          To list all network profiles which can be used for testing, run:

            $ {command} list

          To view information about a specific network profile, run:

            $ {command} describe PROFILE_ID
          """,
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags common to this sub-group.

    Args:
      parser: An argparse parser used to add arguments that immediately follow
          this group in the CLI. Positional arguments are allowed.
    """
    pass
