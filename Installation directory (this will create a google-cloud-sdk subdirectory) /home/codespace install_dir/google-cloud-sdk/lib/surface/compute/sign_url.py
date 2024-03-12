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
"""Implements the command for generating Cloud CDN Signed URLs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import sign_url_utils
from googlecloudsdk.command_lib.compute import signed_url_flags
from googlecloudsdk.core.util import files


class SignUrl(base.Command):
  """Sign specified URL for use with Cloud CDN Signed URLs.

  *{command}* generates a signed URL for the specified URL and
  optionally validates the response by sending a request to the signed URL.

  Cloud CDN Signed URLs give you a way to serve responses from the
  globally distributed CDN cache, even if the request needs to be
  authorized.

  Signed URLs are a mechanism to temporarily give a client access to a
  private resource without requiring additional authorization. To achieve
  this, the full request URL that should be allowed is hashed
  and cryptographically signed. By using the signed URL you give it, that
  one request will be considered authorized to receive the requested
  content.

  Generally, a signed URL can be used by anyone who has it. However, it
  is usually only intended to be used by the client that was directly
  given the URL. To mitigate this, they expire at a time chosen by the
  issuer. To minimize the risk of a signed URL being shared, it is recommended
  that the signed URL be set to expire as soon as possible.

  A 128-bit secret key is used for signing the URLs.

  The URLs to sign have the following restrictions:

  - The URL scheme must be either HTTP or HTTPS.
  - The URLs must not contain the query parameters: `Expires`, `KeyName` or
    `Signature`, since they are used for signing.
  - The URL must not have a fragment.
  """

  category = base.TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    signed_url_flags.AddCdnSignedUrlKeyName(parser, required=True)
    signed_url_flags.AddCdnSignedUrlKeyFile(parser, required=True)
    parser.add_argument(
        '--expires-in',
        type=arg_parsers.Duration(),
        required=True,
        help="""\
      The duration for which the signed URL will be valid. For example,
      specifying `12h` will cause the signed URL to be valid up to 12 hours.
      See $ gcloud topic datetimes for information on duration formats.
      """)
    parser.add_argument(
        '--validate',
        action='store_true',
        help="""\
      If provided, validates the generated signed URL by sending a HEAD request
      and prints out the HTTP response code.

      If the signed URL is valid, the result should be the same as the response
      code sent by the backend. If it isn't, recheck the key name and the
      contents of the key file, and ensure that expires-in is set to at least
      several seconds and that the clock on the computer running this command
      is accurate.

      If not provided, the generated signed URL is not verified.
      """)
    parser.add_argument('url', help='The URL to sign.')

  def Run(self, args):
    """Signs the specified URL and optionally also validates it.

    Args:
      args: The arguments passed to this command.

    Returns:
      Returns a dictionary. The 'signedUrl' key in the dictionary maps to the
      Signed URL. The 'validationResponseCode' key in the dictionary maps to
      the response code obtained for the HEAD request issued to the Signed URL.
    """
    key_value = files.ReadBinaryFileContents(args.key_file).rstrip()
    result = {}
    result['signedUrl'] = sign_url_utils.SignUrl(args.url, args.key_name,
                                                 key_value, args.expires_in)

    if args.validate:
      result['validationResponseCode'] = sign_url_utils.ValidateSignedUrl(
          result['signedUrl'])

    return result
