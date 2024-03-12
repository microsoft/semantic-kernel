# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Cloud Datacatalog taxonomies client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.data_catalog import util


class TaxonomiesClient(object):
  """Cloud Datacatalog taxonomies client."""

  def __init__(self, version_label):
    self.version_label = version_label
    self.client = util.GetClientInstance(version_label)
    self.messages = util.GetMessagesModule(version_label)
    self.service = self.client.projects_locations_taxonomies

  def Export(self, project, location, taxonomies):
    """Parses export args into the request."""
    parent = 'projects/' + project + '/locations/' + location
    taxonomies = ['{0}/taxonomies/{1}'.format(parent, taxonomy)
                  for taxonomy in taxonomies]
    export_request = self.messages.DatacatalogProjectsLocationsTaxonomiesExportRequest(
        parent=parent,
        serializedTaxonomies=True,
        taxonomies=taxonomies,
    )

    return self.service.Export(export_request)

  def Import(self, project, location, req_body):
    """Parses import args into the request."""
    parent = 'projects/' + project + '/locations/' + location
    if self.version_label == 'v1':
      import_request = self.messages.DatacatalogProjectsLocationsTaxonomiesImportRequest(
          parent=parent,
          googleCloudDatacatalogV1ImportTaxonomiesRequest=req_body,
      )
    else:
      import_request = self.messages.DatacatalogProjectsLocationsTaxonomiesImportRequest(
          parent=parent,
          googleCloudDatacatalogV1beta1ImportTaxonomiesRequest=req_body,
      )

    return self.service.Import(import_request)
