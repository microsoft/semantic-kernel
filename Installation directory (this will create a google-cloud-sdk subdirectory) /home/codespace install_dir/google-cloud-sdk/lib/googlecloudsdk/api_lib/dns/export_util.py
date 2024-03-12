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

"""Helper methods for exporting record-sets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from dns import name
from dns import rdata
from dns import rdataclass
from dns import rdatatype
from dns import zone
from googlecloudsdk.api_lib.dns import svcb_stub
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.resource import resource_printer


# Enable support for exporting SVCB and HTTPS records.
svcb_stub.register()


class Error(exceptions.Error):
  """Base exception for all export errors."""


class UnableToExportRecordsToFile(Error):
  """Unable to export records to specified file."""


def WriteToZoneFile(zone_file, record_sets, domain):
  """Writes the given record-sets in zone file format to the given file.

  Args:
    zone_file: file, File into which the records should be written.
    record_sets: list, ResourceRecordSets to be written out.
    domain: str, The origin domain for the zone file.
  """
  zone_contents = zone.Zone(name.from_text(domain))
  for record_set in record_sets:
    rdset = zone_contents.get_rdataset(record_set.name,
                                       record_set.type,
                                       create=True)
    for rrdata in record_set.rrdatas:
      rdset.add(rdata.from_text(rdataclass.IN,
                                rdatatype.from_text(record_set.type),
                                str(rrdata),
                                origin=zone_contents.origin),
                ttl=record_set.ttl)
  zone_contents.to_file(zone_file, relativize=False)


def WriteToYamlFile(yaml_file, record_sets):
  """Writes the given record-sets in yaml format to the given file.

  Args:
    yaml_file: file, File into which the records should be written.
    record_sets: list, ResourceRecordSets to be written out.
  """
  resource_printer.Print(record_sets, print_format='yaml', out=yaml_file)
