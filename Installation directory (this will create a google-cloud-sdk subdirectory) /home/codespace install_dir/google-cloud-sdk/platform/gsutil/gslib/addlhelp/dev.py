# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Additional help about contributing code to gsutil."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  We're open to incorporating gsutil code changes authored by users. Here
  are some guidelines:

  1. Before we can accept code submissions, we have to jump a couple of legal
     hurdles. Please fill out either the individual or corporate Contributor
     License Agreement:

     - If you are an individual writing original source code and you're
       sure you own the intellectual property,
       then you'll need to sign an individual CLA
       (https://cla.developers.google.com/about/google-individual).
     - If you work for a company that wants to allow you to contribute your
       work to gsutil, then you'll need to sign a corporate CLA
       (https://cla.developers.google.com/about/google-corporate)

     Follow either of the two links above to access the appropriate CLA and
     instructions for how to sign and return it. Once we receive it, we'll
     add you to the official list of contributors and be able to accept
     your patches.

  2. If you found a bug or have an idea for a feature enhancement, we suggest
     you check https://github.com/GoogleCloudPlatform/gsutil/issues to see if it
     has already been reported by another user. From there you can also
     subscribe to updates to the issue.

     If a GitHub issue doesn't already exist, create one about your idea before
     sending actual code. Often we can discuss the idea and help propose things
     that could save you later revision work.

  3. We tend to avoid adding command line options that are of use to only
     a very small fraction of users, especially if there's some other way
     to accommodate such needs. Adding such options complicates the code and
     also adds overhead to users having to read through an "alphabet soup"
     list of option documentation.

  4. While gsutil has a number of features specific to Google Cloud Storage,
     it can also be used with other cloud storage providers. We're open to
     including changes for making gsutil support features specific to other
     providers, as long as those changes don't make gsutil work worse for Google
     Cloud Storage. If you do make such changes we recommend including someone
     with knowledge of the specific provider as a code reviewer (see below).

  5. You can check out the gsutil code from the GitHub repository:

       https://github.com/GoogleCloudPlatform/gsutil

     To clone a read-only copy of the repository:

       git clone git://github.com/GoogleCloudPlatform/gsutil.git

     To push your own changes to GitHub, click the Fork button on the
     repository page and clone the repository from your own fork.

  6. The gsutil git repository uses git submodules to pull in external modules.
     After checking out the repository, make sure to also pull the submodules
     by entering into the gsutil top-level directory and run:

       git submodule update --init --recursive

  7. Please make sure to run all tests against your modified code. To
     do this, change directories into the gsutil top-level directory and run:

       ./gsutil test

     The above tests take a long time to run because they send many requests to
     the production service. The gsutil test command has a -u argument that will
     only run unit tests. These run quickly, as they are executed with an
     in-memory mock storage service implementation. To run only the unit tests,
     run:

       ./gsutil test -u

     If you made changes to boto, please run the boto tests. For these tests you
     need to use HMAC credentials (from gsutil config -a), because the boto test
     suite doesn't import the OAuth2 handler. You'll also need to install some
     Python modules. Change directories into the boto root directory at
     third_party/boto and run:

       pip install -r requirements.txt

     (You probably need to run this command using sudo.)
     Make sure each of the individual installations succeeded. If they don't
     you may need to run the install command again.

     Then ensure your .boto file has HMAC credentials defined, and then change
     directories into boto's tests directory and run:

       python test.py unit
       python test.py -t s3 -t gs -t ssl

  8. Please consider contributing test code for your change, especially if the
     change impacts any of the core gsutil code (like the gsutil cp command).

  9. Please run the yapf linter with the config files in the root of the GitHub
     repository:

       yapf -irp .

  10. When it's time to send us code, please submit a PR to the `gsutil GitHub
      repository <https://github.com/GoogleCloudPlatform/gsutil>`_. For help on
      making GitHub PRs, please refer to this
      `GitHub help document <https://help.github.com/en/articles/about-pull-requests>`_.
""")


class CommandOptions(HelpProvider):
  """Additional help about contributing code to gsutil."""
  # TODO: gsutil-beta: Add lint .rc file and linting instructions.

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='dev',
      help_name_aliases=[
          'development',
          'developer',
          'code',
          'mods',
          'software',
      ],
      help_type='additional_help',
      help_one_line_summary='Contributing Code to gsutil',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
