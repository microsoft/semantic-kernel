# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Resource escaping supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


# NOTE: If the name of this topic is modified, please make sure to update all
# references to it in error messages and other help messages as there are no
# tests to catch such changes.
class Escaping(base.TopicCommand):
  """List/dictionary-type argument escaping supplementary help."""

  detailed_help = {

      'DESCRIPTION': """\
          {description}

          *gcloud* supports list-type and dictionary-type flags that take one
          argument which is a list of one or more comma-separated items:

              --list-flag=value1,value2,value3

              --dict-flag=key1=value1,key2=value2

          In the case of a dict-type flag, each item is a key-value pair
          separated by '='. If more than one '=' is present, the first is used.

          In order to include commas in your arguments, specify an alternate
          delimiter using the following syntax:

              ^DELIM^flag value, with comma

          where _DELIM_ is a sequence of one or more characters that may not
          appear in any value in the list.

          NOTE: In cmd.exe and PowerShell on Windows, `^` is a special character
          and you must escape it by repeating it. In the following examples,
          every time you see `^`, replace it with `^^^^`.
          """,

      'EXAMPLES': """\
          In these examples, a list-type or dictionary-type flag is given, along
          with a shell comment explaining how it is parsed. The parsed flags are
          shown here using Python-style list or dict formats (in other
          languages, what Python calls "dicts" are often called "associative
          arrays," "maps," or "hashes").

          Basic example:

              --list-flag=^:^a,b:c,d # => ['a,b', 'c,d']

          Multi-character delimiters are allowed:

              --list-flag=^--^a-,b--c # => ['a-,b', 'c']

          Just one '^' has no special meaning:

              --list-flag=^a,b,c # => ['^a', 'b', 'c']

          This is an alternative way of starting with '^':

              --list-flag=^,^^a,b,c # => ['^a', 'b', 'c']

          A '^' anywhere but the start has no special meaning:

              --list-flag=a^:^,b,c # => ['a^:^', 'b', 'c']

          Dictionary-type arguments work exactly the same as list-type
          arguments:

              --dict-flag=^:^a=b,c:d=f,g # => {'a': 'b,c', 'd': 'f,g'}

          To reserve ephemeral IP addresses, passed in as a list, which are
          being used by virtual machine instances in the us-central1 region,
          run:

              $ gcloud compute addresses create \
              --addresses ^:^123.456.789.198:22.333.146.189:789.312.645 \
              --region us-central1

          To create a Google Compute Engine virtual machine instance
          with metadata as a list ({'key1': '"value1"', 'key2': 'value2',
          'key3': 'value3Index1,value3Index2', 'key4': 'value4'), run:

              $ gcloud compute instances create example-instance1 \
              --metadata ^:^key1="value1":key2=value2:key3=value3Index1,value3Index2,valueIndex3:key4=value4
          """,
      }
