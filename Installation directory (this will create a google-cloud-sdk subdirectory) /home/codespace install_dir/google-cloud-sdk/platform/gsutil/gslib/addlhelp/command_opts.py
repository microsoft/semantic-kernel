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
"""Additional help about gsutil command-level options."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>DESCRIPTION</B>
  gsutil supports separate options for the top-level gsutil command and
  the individual sub-commands (like cp, rm, etc.) The top-level options
  control behavior of gsutil that apply across commands. For example, in
  the command:

    gsutil -m cp -p file gs://bucket/obj

  the -m option applies to gsutil, while the -p option applies to the cp
  sub-command.


<B>OPTIONS</B>
  -D          Shows HTTP requests/headers and additional debug info needed
              when posting support requests, including exception stack traces.

              CAUTION: The output from using this flag includes authentication
              credentials. Before including this flag in your command, be sure
              you understand how the command's output is used, and, if
              necessary, remove or redact sensitive information.

  -DD         Same as -D, plus HTTP upstream payload.

  -h          Allows you to specify certain HTTP headers, for example:

                gsutil -h "Cache-Control:public,max-age=3600" \\
                       -h "Content-Type:text/html" cp ...

              Note that you need to quote the headers/values that
              contain spaces (such as "Content-Disposition: attachment;
              filename=filename.ext"), to avoid having the shell split them
              into separate arguments.

              The following headers are stored as object metadata and used
              in future requests on the object:

                Cache-Control
                Content-Disposition
                Content-Encoding
                Content-Language
                Content-Type

              The following headers are used to check data integrity:

                Content-MD5

              gsutil also supports custom metadata headers with a matching
              Cloud Storage Provider prefix, such as:

                x-goog-meta-

              Note that for gs:// URLs, the Cache Control header is specific to
              the API being used. The XML API accepts any cache control headers
              and returns them during object downloads.  The JSON API respects
              only the public, private, no-cache, max-age, and no-transform
              cache control headers.

              See "gsutil help setmeta" for the ability to set metadata
              fields on objects after they have been uploaded.

  -i          Allows you to use the configured credentials to impersonate a
              service account, for example:

                gsutil -i "service-account@google.com" ls gs://pub

              Note that this setting will be ignored by the XML API and S3. See
              'gsutil help creds' for more information on impersonating service
              accounts.

  -m          Causes supported operations (acl ch, acl set, cp, mv, rm, rsync,
              and setmeta) to run in parallel. This can significantly improve
              performance if you are performing operations on a large number of
              files over a reasonably fast network connection.

              gsutil performs the specified operation using a combination of
              multi-threading and multi-processing. The number of threads
              and processors are determined by ``parallel_thread_count`` and
              ``parallel_process_count``, respectively. These values are set in
              the .boto configuration file or specified in individual requests
              with the ``-o`` top-level flag. Because gsutil has no built-in
              support for throttling requests, you should experiment with these
              values. The optimal values can vary based on a number of factors,
              including network speed, number of CPUs, and available memory.

              Using the -m option can consume a significant amount of network
              bandwidth and cause problems or make your performance worse if
              you use a slower network. For example, if you start a large rsync
              operation over a network link that's also used by a number of
              other important jobs, there could be degraded performance in
              those jobs. Similarly, the -m option can make your performance
              worse, especially for cases that perform all operations locally,
              because it can "thrash" your local disk.

              To prevent such issues, reduce the values for
              ``parallel_thread_count`` and ``parallel_process_count``, or stop
              using the -m option entirely. One tool that you can use to limit
              how much I/O capacity gsutil consumes and prevent it from
              monopolizing your local disk is `ionice
              <http://www.tutorialspoint.com/unix_commands/ionice.htm>`_
              (built in to many Linux systems). For example, the following
              command reduces the I/O priority of gsutil so it doesn't
              monopolize your local disk:

                ionice -c 2 -n 7 gsutil -m rsync -r ./dir gs://some bucket

              If a download or upload operation using parallel transfer fails
              before the entire transfer is complete (e.g. failing after 300 of
              1000 files have been transferred), you must restart the entire
              transfer.

              Also, although most commands normally fail upon encountering an
              error when the -m flag is disabled, all commands continue to try
              all operations when -m is enabled with multiple threads or
              processes, and the number of failed operations (if any) are
              reported as an exception at the end of the command's execution.

  -o          Override values in the `boto configuration file
              <https://cloud.google.com/storage/docs/boto-gsutil>`_ for the
              current command, in the format ``<section>:<name>=<value>``. For
              example, ``gsutil -o "GSUtil:parallel_thread_count=4" ...``. This
              does not pass the option to gsutil integration tests and does not
              change the values that are saved in the boto configuration file.

  -q          Causes gsutil to perform operations quietly, i.e., without
              reporting progress indicators of files being copied or removed,
              etc. Errors are still reported. This option can be useful for
              running gsutil from a cron job that logs its output to a file, for
              which the only information desired in the log is failures.

  -u          Allows you to specify the ID or number of a user project to be
              billed for the request. For example:

                gsutil -u "bill-this-project" cp ...
""")


class CommandOptions(HelpProvider):
  """Additional help about gsutil command-level options."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='options',
      help_name_aliases=['arg', 'args', 'cli', 'opt', 'opts'],
      help_type='additional_help',
      help_one_line_summary='Global Command Line Options',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
