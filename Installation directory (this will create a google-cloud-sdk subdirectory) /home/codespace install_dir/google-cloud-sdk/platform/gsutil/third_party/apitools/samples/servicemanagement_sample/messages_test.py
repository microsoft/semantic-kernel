#
# Copyright 2016 Google Inc.
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

"""Test for generated servicemanagement messages module."""

import unittest

from apitools.base.py import extra_types

from samples.servicemanagement_sample.servicemanagement_v1 \
    import servicemanagement_v1_messages as messages  # nopep8


class MessagesTest(unittest.TestCase):

    def testInstantiateMessageWithAdditionalProperties(self):
        PROJECT_NAME = 'test-project'
        SERVICE_NAME = 'test-service'
        SERVICE_VERSION = '1.0'

        prop = messages.Operation.ResponseValue.AdditionalProperty
        messages.Operation(
            name='operation-12345-67890',
            done=False,
            response=messages.Operation.ResponseValue(
                additionalProperties=[
                    prop(key='producerProjectId',
                         value=extra_types.JsonValue(
                             string_value=PROJECT_NAME)),
                    prop(key='serviceName',
                         value=extra_types.JsonValue(
                             string_value=SERVICE_NAME)),
                    prop(key='serviceConfig',
                         value=extra_types.JsonValue(
                             object_value=extra_types.JsonObject(
                                 properties=[
                                     extra_types.JsonObject.Property(
                                         key='id',
                                         value=extra_types.JsonValue(
                                             string_value=SERVICE_VERSION)
                                     )
                                 ])
                         ))
                ]))
