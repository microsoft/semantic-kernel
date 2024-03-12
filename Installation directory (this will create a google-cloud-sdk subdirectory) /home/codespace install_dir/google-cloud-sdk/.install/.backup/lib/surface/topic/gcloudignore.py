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
"""Extra help for .gcloudignore."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class GcloudignoreHelp(base.TopicCommand):
  r"""Reference for `.gcloudignore` files.

  Several commands in `gcloud` involve uploading the contents of a directory to
  Google Cloud to host or build. In many cases, you will not want to
  upload certain files (i.e., "ignore" them).

  If there is a file called `.gcloudignore` _in the top-level directory to
  upload_, the files that it specifies (see "SYNTAX") will be ignored.

  Gcloud commands may generate a .gcloudignore file; see the individual
  command help page for details.

  The following `gcloud` commands respect the `.gcloudignore` file:

  * `gcloud app deploy`
    * Note: If you add `app.yaml` to the `.gcloudignore` file, this command will
    fail.
  * `gcloud functions deploy`
  * `gcloud builds submit`
  * `gcloud composer environments storage {dags, data, plugins} import`
  * `gcloud container builds submit`
  * `gcloud run deploy`
  * `gcloud run jobs deploy`
  *  gcloud alpha deploy releases create
  * `gcloud infra-manager deployments apply`
  * `gcloud infra-manager previews create`
  * `gcloud alpha functions local deploy`
  * `gcloud alpha run jobs deploy`
  * `gcloud beta run jobs deploy`

  To globally disable `.gcloudignore` parsing (including default file-ignore
  behavior), run:

     $ gcloud config set gcloudignore/enabled false

  The default content of the generated `.gcloudignore` file, which can be
  overridden with `--ignore-file`, is as follows:

    .gcloudignore
    .git
    .gitignore

  ## SYNTAX

  The syntax of `.gcloudignore` borrows heavily from that of `.gitignore`; see
  https://git-scm.com/docs/gitignore or `man gitignore` for a full reference.

  Each line in a `.gcloudignore` is one of the following:

  * *pattern*: a pattern specifies file names to ignore (or explicitly include)
    in the upload. If multiple patterns match the file name, the last matching
    pattern takes precedence.
  * *comment*: comments begin with `#` and are ignored (see "ADVANCED TOPICS"
    for an exception). If you want to include a `#` at the beginning of a
    pattern, you must escape it: ```\#```.
  * *blank line*: A blank line is ignored and useful for readability.

  Some example patterns follow; see the full reference
  (https://git-scm.com/docs/gitignore or `man gitignore`) for details.

  To ignore any file named `foo`, and any file in the root of the upload
  directory named `bar`:

    foo
    /bar

  To ignore any file starting with `foo`, ending with `bar`, or starting with
  `baz` and ending with `qux`:

    foo*
    *bar
    baz*qux

  To explicitly include any file named `foo` (useful if `foo` was excluded
  earlier in the file) and ignore a file named `!bar`:

    !foo
    \!bar

  To ignore any directory `foo` and all its contents (though not a file
  `foo`), any file `baz`, and the directory `qux` and all its contents:

    foo/
    **/baz
    qux/**


  ### ADVANCED TOPICS

  In order to ignore files specified in the gitignore file, there is a special
  comment syntax:

    #!include:.gitignore

  This will insert the content of a `.gitignore`-style file named `.gitignore`
  at the point of the include line. It does not recurse (that is, the included
  file *cannot* `#!include` another file) and cannot be anywhere but the
  top-level directory to be uploaded.

  To display files that will be uploaded run:

    gcloud meta list-files-for-upload

  ## EXAMPLES

  This `.gcloudignore` would prevent the upload of the `node_modules/` directory
  and any files ending in `~`:

    /node_modules/
    *~

  This `.gcloudignore` (similar to the one generated when Git files are
  present) would prevent the upload of the `.gcloudignore` file, the `.git`
  directory, and any files in ignored in the `.gitignore` file:

    .gcloudignore
    # If you would like to upload your .git directory, .gitignore file or
    # files from your .gitignore file, remove the corresponding line below:
    .git
    .gitignore
    #!include:.gitignore
  """
