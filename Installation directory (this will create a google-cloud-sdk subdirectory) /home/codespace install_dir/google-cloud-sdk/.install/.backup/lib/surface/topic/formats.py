# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Resource formats supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_topics


class Formats(base.TopicCommand):
  """Resource formats supplementary help."""

  detailed_help = {

      'DESCRIPTION': textwrap.dedent("""\
          {description}

          ### Formats

          A format expression is used to change the default output format of a
          command.
          Many output formats are available; some for pretty printing
          human-readable output and others for returning machine-readable
          output.

          A format expression has 3 parts:

          _NAME_:: _name_
          _ATTRIBUTES_:: *[* [no-]_attribute-name_[=_value_] [, ... ] *]*
          _PROJECTION_:: *(* _resource-key_ [, ...] *)*


          _NAME_ is required, _ATTRIBUTES_ are optional, and _PROJECTIONS_
          may be required for some formats. Unknown attribute names are
          silently ignored.

          Each *gcloud* *list* command has a default format expression. The
          *--format* flag can alter or replace the default. For example,

              --format="[box]"

          adds box decorations to a default table, and

              --format=json

          lists the resource in *json* format.

          {format_registry}
          """).format(
              description=resource_topics.ResourceDescription('format'),
              format_registry=resource_topics.FormatRegistryDescriptions()),

      'EXAMPLES': """\
          List a table of compute instance resources sorted by *name* with
          box decorations and title *Instances*:

            $ gcloud compute instances list --format="table[box,title=Instances](name:sort=1, zone:label=zone, status)"

          List a nested table of the quotas of a region:

            $ gcloud compute regions describe us-central1 --format="table(quotas:format='table(metric,limit,usage)')"

          Print a flattened list of global quotas in CSV format:

            $ gcloud compute project-info describe --flatten="quotas[]" --format="csv(quotas.metric,quotas.limit,quotas.usage)"

          List the disk interfaces for all compute instances as a compact
          comma separated list:

            $ gcloud compute instances list --format="value(disks[].interface.list())"

          List the URIs for all compute instances:

            $ gcloud compute instances list --format="value(uri())"

          List all compute instances with their creation timestamps displayed
          according to the local timezone:

            $ gcloud compute instances list --format="table(name,creationTimestamp.date(tz=LOCAL))"

          List the project authenticated user email address:

            $ gcloud info --format="value(config.account)"

          List resources filtered on repeated fields by projecting subfields on
          a repeated message:

            $ gcloud alpha genomics readgroupsets list --format="default(readGroups[].name)"

          Return the scope of the current instance:

            $ gcloud compute zones list --format="value(selfLink.scope())"

          selfLink is a fully qualified name. (e.g. 'https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a')
          The previous example returns a list of just the names of each zone
          (e.g. 'us-central1-a'). This is because selfLink.scope() grabs the
          last part of the URL segment. To extract selfLink starting from
          /projects and return the scope of the current instance:

            $ gcloud compute zones list --format="value(selfLink.scope(projects))"

          List all scopes enabled for a Compute Engine instance and flatten the
          multi-valued resource:

            $ gcloud compute instances list --format="flattened(name,serviceAccounts[].email,serviceAccounts[].scopes[].basename())"

          Display a multi-valued resource's service account keys with the
          corresponding service account, extracting just the first '/' delimited
          part with segment(0):

            $ gcloud iam service-accounts keys list --iam-account=svc-2-123@test-minutia-123.iam.gserviceaccount.com --project=test-minutia-123 --format="table(name.scope(serviceAccounts).segment(0):label='service Account',name.scope(keys):label='keyID',validAfterTime)"

          The last example returns a table with service account names without
          their full paths, keyID and validity.
          """,
      }
