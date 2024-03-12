# Copyright (c) 2010 Jeremy Thurgood <firxen+boto@gmail.com>
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


# NOTE: These tests only cover the very simple cases I needed to test
# for the InstanceGroup fix.

import xml.sax

from boto import handler
from boto.emr import emrobject
from boto.resultset import ResultSet
from tests.compat import unittest


JOB_FLOW_EXAMPLE = b"""
<DescribeJobFlowsResponse
    xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-01-15">
  <DescribeJobFlowsResult>
    <JobFlows>
      <member>
        <ExecutionStatusDetail>
          <CreationDateTime>2009-01-28T21:49:16Z</CreationDateTime>
          <StartDateTime>2009-01-28T21:49:16Z</StartDateTime>
          <State>STARTING</State>
        </ExecutionStatusDetail>
        <BootstrapActions>
          <member>
            <BootstrapActionConfig>
              <ScriptBootstrapAction>
                <Args/>
                <Path>s3://elasticmapreduce/libs/hue/install-hue</Path>
              </ScriptBootstrapAction>
              <Name>Install Hue</Name>
            </BootstrapActionConfig>
          </member>
        </BootstrapActions>
        <VisibleToAllUsers>true</VisibleToAllUsers>
        <SupportedProducts>
          <member>Hue</member>
        </SupportedProducts>
        <Name>MyJobFlowName</Name>
        <LogUri>mybucket/subdir/</LogUri>
        <Steps>
          <member>
            <ExecutionStatusDetail>
              <CreationDateTime>2009-01-28T21:49:16Z</CreationDateTime>
              <State>PENDING</State>
            </ExecutionStatusDetail>
            <StepConfig>
              <HadoopJarStep>
                <Jar>MyJarFile</Jar>
                <MainClass>MyMailClass</MainClass>
                <Args>
                  <member>arg1</member>
                  <member>arg2</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>MyStepName</Name>
              <ActionOnFailure>CONTINUE</ActionOnFailure>
            </StepConfig>
          </member>
        </Steps>
        <JobFlowId>j-3UN6WX5RRO2AG</JobFlowId>
        <Instances>
          <Placement>
            <AvailabilityZone>us-east-1a</AvailabilityZone>
          </Placement>
          <SlaveInstanceType>m1.small</SlaveInstanceType>
          <MasterInstanceType>m1.small</MasterInstanceType>
          <Ec2KeyName>myec2keyname</Ec2KeyName>
          <InstanceCount>4</InstanceCount>
          <KeepJobFlowAliveWhenNoSteps>true</KeepJobFlowAliveWhenNoSteps>
        </Instances>
      </member>
    </JobFlows>
  </DescribeJobFlowsResult>
  <ResponseMetadata>
    <RequestId>9cea3229-ed85-11dd-9877-6fad448a8419</RequestId>
  </ResponseMetadata>
</DescribeJobFlowsResponse>
"""

JOB_FLOW_COMPLETED = b"""
<DescribeJobFlowsResponse xmlns="http://elasticmapreduce.amazonaws.com/doc/2009-03-31">
  <DescribeJobFlowsResult>
    <JobFlows>
      <member>
        <ExecutionStatusDetail>
          <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
          <LastStateChangeReason>Steps completed</LastStateChangeReason>
          <StartDateTime>2010-10-21T01:03:59Z</StartDateTime>
          <ReadyDateTime>2010-10-21T01:03:59Z</ReadyDateTime>
          <State>COMPLETED</State>
          <EndDateTime>2010-10-21T01:44:18Z</EndDateTime>
        </ExecutionStatusDetail>
        <BootstrapActions/>
        <Name>RealJobFlowName</Name>
        <LogUri>s3n://example.emrtest.scripts/jobflow_logs/</LogUri>
        <Steps>
          <member>
            <StepConfig>
              <HadoopJarStep>
                <Jar>s3n://us-east-1.elasticmapreduce/libs/script-runner/script-runner.jar</Jar>
                <Args>
                  <member>s3n://us-east-1.elasticmapreduce/libs/state-pusher/0.1/fetch</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>Setup Hadoop Debugging</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
            <ExecutionStatusDetail>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <StartDateTime>2010-10-21T01:03:59Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2010-10-21T01:04:22Z</EndDateTime>
            </ExecutionStatusDetail>
          </member>
          <member>
            <StepConfig>
              <HadoopJarStep>
                <Jar>/home/hadoop/contrib/streaming/hadoop-0.20-streaming.jar</Jar>
                <Args>
                  <member>-mapper</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-InitialMapper.py</member>
                  <member>-reducer</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-InitialReducer.py</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/20/*</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/19/*</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/18/*</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/17/*</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/16/*</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/15/*</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.data/raw/2010/10/14/*</member>
                  <member>-output</member>
                  <member>s3://example.emrtest.crunched/</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>testjob_Initial</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
            <ExecutionStatusDetail>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <StartDateTime>2010-10-21T01:04:22Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2010-10-21T01:36:18Z</EndDateTime>
            </ExecutionStatusDetail>
          </member>
          <member>
            <StepConfig>
              <HadoopJarStep>
                <Jar>/home/hadoop/contrib/streaming/hadoop-0.20-streaming.jar</Jar>
                <Args>
                  <member>-mapper</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step1Mapper.py</member>
                  <member>-reducer</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step1Reducer.py</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.crunched/*</member>
                  <member>-output</member>
                  <member>s3://example.emrtest.step1/</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>testjob_step1</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
            <ExecutionStatusDetail>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <StartDateTime>2010-10-21T01:36:18Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2010-10-21T01:37:51Z</EndDateTime>
            </ExecutionStatusDetail>
          </member>
          <member>
            <StepConfig>
              <HadoopJarStep>
                <Jar>/home/hadoop/contrib/streaming/hadoop-0.20-streaming.jar</Jar>
                <Args>
                  <member>-mapper</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step2Mapper.py</member>
                  <member>-reducer</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step2Reducer.py</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.crunched/*</member>
                  <member>-output</member>
                  <member>s3://example.emrtest.step2/</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>testjob_step2</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
            <ExecutionStatusDetail>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <StartDateTime>2010-10-21T01:37:51Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2010-10-21T01:39:32Z</EndDateTime>
            </ExecutionStatusDetail>
          </member>
          <member>
            <StepConfig>
              <HadoopJarStep>
                <Jar>/home/hadoop/contrib/streaming/hadoop-0.20-streaming.jar</Jar>
                <Args>
                  <member>-mapper</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step3Mapper.py</member>
                  <member>-reducer</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step3Reducer.py</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.step1/*</member>
                  <member>-output</member>
                  <member>s3://example.emrtest.step3/</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>testjob_step3</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
            <ExecutionStatusDetail>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <StartDateTime>2010-10-21T01:39:32Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2010-10-21T01:41:22Z</EndDateTime>
            </ExecutionStatusDetail>
          </member>
          <member>
            <StepConfig>
              <HadoopJarStep>
                <Jar>/home/hadoop/contrib/streaming/hadoop-0.20-streaming.jar</Jar>
                <Args>
                  <member>-mapper</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step4Mapper.py</member>
                  <member>-reducer</member>
                  <member>s3://example.emrtest.scripts/81d8-5a9d3df4a86c-step4Reducer.py</member>
                  <member>-input</member>
                  <member>s3://example.emrtest.step1/*</member>
                  <member>-output</member>
                  <member>s3://example.emrtest.step4/</member>
                </Args>
                <Properties/>
              </HadoopJarStep>
              <Name>testjob_step4</Name>
              <ActionOnFailure>TERMINATE_JOB_FLOW</ActionOnFailure>
            </StepConfig>
            <ExecutionStatusDetail>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <StartDateTime>2010-10-21T01:41:22Z</StartDateTime>
              <State>COMPLETED</State>
              <EndDateTime>2010-10-21T01:43:03Z</EndDateTime>
            </ExecutionStatusDetail>
          </member>
        </Steps>
        <JobFlowId>j-3H3Q13JPFLU22</JobFlowId>
        <Instances>
          <SlaveInstanceType>m1.large</SlaveInstanceType>
          <MasterInstanceId>i-64c21609</MasterInstanceId>
          <Placement>
            <AvailabilityZone>us-east-1b</AvailabilityZone>
          </Placement>
          <InstanceGroups>
            <member>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <InstanceRunningCount>0</InstanceRunningCount>
              <StartDateTime>2010-10-21T01:02:09Z</StartDateTime>
              <ReadyDateTime>2010-10-21T01:03:03Z</ReadyDateTime>
              <State>ENDED</State>
              <EndDateTime>2010-10-21T01:44:18Z</EndDateTime>
              <InstanceRequestCount>1</InstanceRequestCount>
              <InstanceType>m1.large</InstanceType>
              <Market>ON_DEMAND</Market>
              <LastStateChangeReason>Job flow terminated</LastStateChangeReason>
              <InstanceRole>MASTER</InstanceRole>
              <InstanceGroupId>ig-EVMHOZJ2SCO8</InstanceGroupId>
              <Name>master</Name>
            </member>
            <member>
              <CreationDateTime>2010-10-21T01:00:25Z</CreationDateTime>
              <InstanceRunningCount>0</InstanceRunningCount>
              <StartDateTime>2010-10-21T01:03:59Z</StartDateTime>
              <ReadyDateTime>2010-10-21T01:03:59Z</ReadyDateTime>
              <State>ENDED</State>
              <EndDateTime>2010-10-21T01:44:18Z</EndDateTime>
              <InstanceRequestCount>9</InstanceRequestCount>
              <InstanceType>m1.large</InstanceType>
              <Market>ON_DEMAND</Market>
              <LastStateChangeReason>Job flow terminated</LastStateChangeReason>
              <InstanceRole>CORE</InstanceRole>
              <InstanceGroupId>ig-YZHDYVITVHKB</InstanceGroupId>
              <Name>slave</Name>
            </member>
          </InstanceGroups>
          <NormalizedInstanceHours>40</NormalizedInstanceHours>
          <HadoopVersion>0.20</HadoopVersion>
          <MasterInstanceType>m1.large</MasterInstanceType>
          <MasterPublicDnsName>ec2-184-72-153-139.compute-1.amazonaws.com</MasterPublicDnsName>
          <Ec2KeyName>myubersecurekey</Ec2KeyName>
          <InstanceCount>10</InstanceCount>
          <KeepJobFlowAliveWhenNoSteps>false</KeepJobFlowAliveWhenNoSteps>
        </Instances>
      </member>
    </JobFlows>
  </DescribeJobFlowsResult>
  <ResponseMetadata>
    <RequestId>c31e701d-dcb4-11df-b5d9-337fc7fe4773</RequestId>
  </ResponseMetadata>
</DescribeJobFlowsResponse>
"""


class TestEMRResponses(unittest.TestCase):
    def _parse_xml(self, body, markers):
        rs = ResultSet(markers)
        h = handler.XmlHandler(rs, None)
        xml.sax.parseString(body, h)
        return rs

    def _assert_fields(self, response, **fields):
        for field, expected in fields.items():
            actual = getattr(response, field)
            self.assertEquals(expected, actual,
                              "Field %s: %r != %r" % (field, expected, actual))

    def test_JobFlows_example(self):
        [jobflow] = self._parse_xml(JOB_FLOW_EXAMPLE,
                                    [('member', emrobject.JobFlow)])
        self._assert_fields(jobflow,
                            creationdatetime='2009-01-28T21:49:16Z',
                            startdatetime='2009-01-28T21:49:16Z',
                            state='STARTING',
                            instancecount='4',
                            jobflowid='j-3UN6WX5RRO2AG',
                            loguri='mybucket/subdir/',
                            name='MyJobFlowName',
                            availabilityzone='us-east-1a',
                            slaveinstancetype='m1.small',
                            masterinstancetype='m1.small',
                            ec2keyname='myec2keyname',
                            keepjobflowalivewhennosteps='true')

    def test_JobFlows_completed(self):
        [jobflow] = self._parse_xml(JOB_FLOW_COMPLETED,
                                    [('member', emrobject.JobFlow)])
        self._assert_fields(jobflow,
                            creationdatetime='2010-10-21T01:00:25Z',
                            startdatetime='2010-10-21T01:03:59Z',
                            enddatetime='2010-10-21T01:44:18Z',
                            state='COMPLETED',
                            instancecount='10',
                            jobflowid='j-3H3Q13JPFLU22',
                            loguri='s3n://example.emrtest.scripts/jobflow_logs/',
                            name='RealJobFlowName',
                            availabilityzone='us-east-1b',
                            slaveinstancetype='m1.large',
                            masterinstancetype='m1.large',
                            ec2keyname='myubersecurekey',
                            keepjobflowalivewhennosteps='false')
        self.assertEquals(6, len(jobflow.steps))
        self.assertEquals(2, len(jobflow.instancegroups))

