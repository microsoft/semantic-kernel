#
# Copyright 2013 Google LLC. All Rights Reserved.
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
# All Rights Reserved.

"""The Python datastore protocol buffer definition (old name)."""

from __future__ import absolute_import



# The proto2 compiler generates datastore_v3_pb.py, but all our code refers
# to datastore_pb.py, so import all the symbols from there. Also import the
# names that were imported to datastore_pb by the old proto1 specification,
# as some tests and possibly some user code may be referring to them.

from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.action_pb import Action
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import CompositeIndex
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import EntityProto
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import Index
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import Path
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import Property
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import PropertyValue
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.entity_pb import Reference
from googlecloudsdk.third_party.appengine.googlestorage.onestore.v3.snapshot_pb import Snapshot

from googlecloudsdk.third_party.appengine.api.api_base_pb import Integer64Proto
from googlecloudsdk.third_party.appengine.api.api_base_pb import StringProto
from googlecloudsdk.third_party.appengine.api.api_base_pb import VoidProto
from googlecloudsdk.third_party.appengine.datastore import datastore_v3_pb
from googlecloudsdk.third_party.appengine.datastore.datastore_v3_pb import *

