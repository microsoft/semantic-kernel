#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
import time
from tests.unit import unittest

from boto.datapipeline import layer1


class TestDataPipeline(unittest.TestCase):
    datapipeline = True

    def setUp(self):
        self.connection = layer1.DataPipelineConnection()
        self.sample_pipeline_objects = [
            {'fields': [
                {'key': 'workerGroup', 'stringValue': 'MyworkerGroup'}],
             'id': 'Default',
             'name': 'Default'},
            {'fields': [
                {'key': 'startDateTime', 'stringValue': '2012-09-25T17:00:00'},
                {'key': 'type', 'stringValue': 'Schedule'},
                {'key': 'period', 'stringValue': '1 hour'},
                {'key': 'endDateTime', 'stringValue': '2012-09-25T18:00:00'}],
             'id': 'Schedule',
             'name': 'Schedule'},
            {'fields': [
                {'key': 'type', 'stringValue': 'ShellCommandActivity'},
                {'key': 'command', 'stringValue': 'echo hello'},
                {'key': 'parent', 'refValue': 'Default'},
                {'key': 'schedule', 'refValue': 'Schedule'}],
             'id': 'SayHello',
             'name': 'SayHello'}
        ]
        self.connection.auth_service_name = 'datapipeline'

    def create_pipeline(self, name, unique_id, description=None):
        response = self.connection.create_pipeline(name, unique_id,
                                                   description)
        pipeline_id = response['pipelineId']
        self.addCleanup(self.connection.delete_pipeline, pipeline_id)
        return pipeline_id

    def get_pipeline_state(self, pipeline_id):
        response = self.connection.describe_pipelines([pipeline_id])
        for attr in response['pipelineDescriptionList'][0]['fields']:
            if attr['key'] == '@pipelineState':
                return attr['stringValue']

    def test_can_create_and_delete_a_pipeline(self):
        response = self.connection.create_pipeline('name', 'unique_id',
                                                   'description')
        self.connection.delete_pipeline(response['pipelineId'])

    def test_validate_pipeline(self):
        pipeline_id = self.create_pipeline('name2', 'unique_id2')

        self.connection.validate_pipeline_definition(
            self.sample_pipeline_objects, pipeline_id)

    def test_put_pipeline_definition(self):
        pipeline_id = self.create_pipeline('name3', 'unique_id3')
        self.connection.put_pipeline_definition(self.sample_pipeline_objects,
                                                pipeline_id)

        # We should now be able to get the pipeline definition and see
        # that it matches what we put.
        response = self.connection.get_pipeline_definition(pipeline_id)
        objects = response['pipelineObjects']
        self.assertEqual(len(objects), 3)
        self.assertEqual(objects[0]['id'], 'Default')
        self.assertEqual(objects[0]['name'], 'Default')
        self.assertEqual(objects[0]['fields'],
                         [{'key': 'workerGroup', 'stringValue': 'MyworkerGroup'}])

    def test_activate_pipeline(self):
        pipeline_id = self.create_pipeline('name4', 'unique_id4')
        self.connection.put_pipeline_definition(self.sample_pipeline_objects,
                                                pipeline_id)
        self.connection.activate_pipeline(pipeline_id)

        attempts = 0
        state = self.get_pipeline_state(pipeline_id)
        while state != 'SCHEDULED' and attempts < 10:
            time.sleep(10)
            attempts += 1
            state = self.get_pipeline_state(pipeline_id)
            if attempts > 10:
                self.fail("Pipeline did not become scheduled "
                          "after 10 attempts.")
        objects = self.connection.describe_objects(['Default'], pipeline_id)
        field = objects['pipelineObjects'][0]['fields'][0]
        self.assertDictEqual(field, {'stringValue': 'COMPONENT', 'key': '@sphere'})

    def test_list_pipelines(self):
        pipeline_id = self.create_pipeline('name5', 'unique_id5')
        pipeline_id_list = [p['id'] for p in
                            self.connection.list_pipelines()['pipelineIdList']]
        self.assertTrue(pipeline_id in pipeline_id_list)


if __name__ == '__main__':
    unittest.main()
