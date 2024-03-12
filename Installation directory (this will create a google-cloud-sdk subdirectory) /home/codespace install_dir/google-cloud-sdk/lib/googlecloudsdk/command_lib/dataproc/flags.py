# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags for workflow templates related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import json

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

import six


def _RegionAttributeConfig():
  fallthroughs = [deps.PropertyFallthrough(properties.VALUES.dataproc.region)]
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text=(
          'Dataproc region for the {resource}. Each Dataproc '
          'region constitutes an independent resource namespace constrained to '
          'deploying instances into Compute Engine zones inside the '
          'region. Overrides the default `dataproc/region` property '
          'value for this command invocation.'),
      fallthroughs=fallthroughs)


def _LocationAttributeConfig():
  fallthroughs = [deps.PropertyFallthrough(properties.VALUES.dataproc.location)]
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text=(
          'Dataproc location for the {resource}. Each Dataproc '
          'location constitutes an independent resource namespace constrained '
          'to deploying instances into Compute Engine zones inside the '
          'location. Overrides the default `dataproc/location` property '
          'value for this command invocation.'),
      fallthroughs=fallthroughs)


def AddRegionFlag(parser):
  region_prop = properties.VALUES.dataproc.region
  parser.add_argument(
      '--region',
      help=region_prop.help_text,
      # Don't set default, because it would override users' property setting.
      action=actions.StoreProperty(region_prop))


def AddLocationFlag(parser):
  location_prop = properties.VALUES.dataproc.location
  parser.add_argument(
      '--location',
      help=location_prop.help_text,
      # Don't set default, because it would override user's property setting.
      action=actions.StoreProperty(location_prop))


def AddProjectsLocationsResourceArg(parser, api_version):
  """Add resrouce arg for projects/{}/locations/{}."""

  spec = concepts.ResourceSpec(
      'dataproc.projects.locations',
      api_version=api_version,
      resource_name='region',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_RegionAttributeConfig())

  concept_parsers.ConceptParser.ForResource(
      '--region',
      spec,
      properties.VALUES.dataproc.region.help_text,
      required=True).AddToParser(parser)


def AddAsync(parser):
  """Adds async flag with our own help text."""
  parser.add_argument(
      '--async',
      action='store_true',
      dest='async_',
      help=('Return immediately without waiting for the operation in '
            'progress to complete.'))


def ClusterConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      help_text='The Cluster name.',
  )


def _GetClusterResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.clusters',
      api_version=api_version,
      resource_name='cluster',
      disable_auto_completers=True,
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=_RegionAttributeConfig(),
      clusterName=ClusterConfig(),
  )


def AddClusterResourceArg(parser, verb, api_version):
  concept_parsers.ConceptParser.ForResource(
      'cluster',
      _GetClusterResourceSpec(api_version),
      'The name of the cluster to {}.'.format(verb),
      required=True).AddToParser(parser)


def GkeClusterConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='gke-cluster',
      help_text='The GKE Cluster path.',
  )


def _DataprocRegionFallthrough():
  return [
      deps.ArgFallthrough('--region'),
      deps.PropertyFallthrough(properties.VALUES.dataproc.region)
  ]


def _GkeLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='gke-cluster-location',
      help_text='GKE region for the {resource}.',
      fallthroughs=_DataprocRegionFallthrough())


def _GetGkeClusterResourceSpec():
  return concepts.ResourceSpec(
      'container.projects.locations.clusters',
      resource_name='gke-cluster',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_GkeLocationAttributeConfig(),
      clustersId=GkeClusterConfig(),
  )


def AddGkeClusterResourceArg(parser):
  concept_parsers.ConceptParser.ForResource(
      '--gke-cluster',
      _GetGkeClusterResourceSpec(),
      'The GKE cluster to install the Dataproc cluster on.',
      required=True).AddToParser(parser)


def MetastoreServiceConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='metastore-service',
      help_text='Dataproc Metastore Service to be used as an external metastore.'
  )


def _MetastoreServiceLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='metastore-service-location',
      help_text='Dataproc Metastore location for the {resource}.',
      fallthroughs=_DataprocRegionFallthrough())


def _GetMetastoreServiceResourceSpec():
  return concepts.ResourceSpec(
      'metastore.projects.locations.services',
      resource_name='metastore-service',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_MetastoreServiceLocationAttributeConfig(),
      servicesId=MetastoreServiceConfig(),
  )


def AddMetastoreServiceResourceArg(parser):
  concept_parsers.ConceptParser.ForResource(
      '--metastore-service',
      _GetMetastoreServiceResourceSpec(),
      'Dataproc Metastore Service to be used as an external metastore.',
  ).AddToParser(parser)


def HistoryServerClusterConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='history-server-cluster',
      help_text='Spark History Server. '
      'Resource name of an existing Dataproc cluster to act as a '
      'Spark History Server for workloads run on the Cluster.')


def _HistoryServerClusterRegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='history-server-cluster-region',
      help_text=('Compute Engine region for the {resource}. It must be the '
                 'same region as the Dataproc cluster that is being created.'),
      fallthroughs=_DataprocRegionFallthrough())


def _GetHistoryServerClusterResourceSpec():
  return concepts.ResourceSpec(
      'dataproc.projects.regions.clusters',
      resource_name='history-server-cluster',
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=_HistoryServerClusterRegionAttributeConfig(),
      clusterName=HistoryServerClusterConfig(),
  )


def AddHistoryServerClusterResourceArg(parser):
  concept_parsers.ConceptParser.ForResource(
      '--history-server-cluster',
      _GetHistoryServerClusterResourceSpec(),
      'A Dataproc Cluster created as a History Server, see https://cloud.google.com/dataproc/docs/concepts/jobs/history-server',
  ).AddToParser(parser)


def AddZoneFlag(parser, short_flags=True):
  """Add zone flag."""
  parser.add_argument(
      '--zone',
      *(['-z'] if short_flags else []),
      help="""
            The compute zone (e.g. us-central1-a) for the cluster. If empty
            and --region is set to a value other than `global`, the server will
            pick a zone in the region.
            """,
      action=actions.StoreProperty(properties.VALUES.compute.zone))


def AddVersionFlag(parser):
  parser.add_argument(
      '--version', type=int, help='The version of the workflow template.')


def AddFileFlag(parser, input_type, action):
  # Examples: workflow template to run/export/import, cluster to create.
  parser.add_argument(
      '--file',
      help='The YAML file containing the {0} to {1}'.format(input_type, action),
      required=True)


def AddMainPythonFile(parser):
  parser.add_argument(
      'MAIN_PYTHON_FILE',
      help=('URI of the main Python file to use as the Spark driver. '
            'Must be a ``.py\'\' file.'))


def AddJvmMainMutex(parser):
  """Main class or main jar."""
  main_group = parser.add_mutually_exclusive_group(required=True)

  main_group.add_argument(
      '--class',
      dest='main_class',
      help=('Class contains the main method of the job. '
            'The jar file that contains the class must be in the classpath '
            'or specified in `jar_files`.'))

  main_group.add_argument(
      '--jar', dest='main_jar', help='URI of the main jar file.')


def AddMainSqlScript(parser):
  parser.add_argument(
      'SQL_SCRIPT',
      help='URI of the script that contains Spark SQL queries to execute.')


def AddSqlScriptVariables(parser):
  """Add --params flag."""
  parser.add_argument(
      '--vars',
      type=arg_parsers.ArgDict(),
      metavar='NAME=VALUE',
      help=('Mapping of query variable names to values (equivalent to the '
            'Spark SQL command: SET name="value";).'))


def AddJarFiles(parser):
  """Add --jars flag."""
  parser.add_argument(
      '--jars',
      type=arg_parsers.ArgList(),
      metavar='JAR',
      default=[],
      help=('Comma-separated list of jar files to be provided to the '
            'classpaths.'))


def AddMainRFile(parser):
  parser.add_argument(
      'MAIN_R_FILE',
      help=('URI of the main R file to use as the driver. '
            'Must be a ``.R\'\' or ``.r\'\' file.'))


def AddPythonFiles(parser):
  """Add --py-files flag."""
  parser.add_argument(
      '--py-files',
      type=arg_parsers.ArgList(),
      metavar='PY',
      default=[],
      help=('Comma-separated list of Python scripts to be passed to the '
            'PySpark framework. Supported file types: ``.py\'\', ``.egg\'\' '
            'and ``.zip.\'\''))


def AddOtherFiles(parser):
  parser.add_argument(
      '--files',
      type=arg_parsers.ArgList(),
      metavar='FILE',
      default=[],
      help='Files to be placed in the working directory.')


def AddArchives(parser):
  parser.add_argument(
      '--archives',
      type=arg_parsers.ArgList(),
      metavar='ARCHIVE',
      default=[],
      help=('Archives to be extracted into the working directory. '
            'Supported file types: .jar, .tar, .tar.gz, .tgz, and .zip.'))


def AddArgs(parser):
  """Remaining args to the program."""
  parser.add_argument(
      'args',
      metavar='JOB_ARG',
      nargs=argparse.REMAINDER,
      default=[],
      help='Arguments to pass to the driver.')


def AddBucket(parser):
  """Cloud Storage bucket to upload workload dependencies."""
  parser.add_argument(
      '--deps-bucket',
      help=('A Cloud Storage bucket to upload workload '
            'dependencies.'))


def JobConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='job',
      help_text='The Job ID.',
  )


def _GetJobResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.jobs',
      api_version=api_version,
      resource_name='job',
      disable_auto_completers=True,
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=_RegionAttributeConfig(),
      jobId=JobConfig(),
  )


def AddJobResourceArg(parser, verb, api_version):
  concept_parsers.ConceptParser.ForResource(
      'job',
      _GetJobResourceSpec(api_version),
      'The ID of the job to {0}.'.format(verb),
      required=True).AddToParser(parser)


def AddBatchResourceArg(parser, verb, api_version, use_location=False):
  """Adds batch resource argument to parser."""

  def BatchConfig():
    return concepts.ResourceParameterAttributeConfig(
        name='batch',
        help_text='Batch job ID.',
    )

  def GetBatchResourceSpec(api_version):
    return concepts.ResourceSpec(
        'dataproc.projects.locations.batches',
        api_version=api_version,
        resource_name='batch',
        disable_auto_completers=True,
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        locationsId=_LocationAttributeConfig()
        if use_location
        else _RegionAttributeConfig(),
        batchesId=BatchConfig(),
    )

  concept_parsers.ConceptParser.ForResource(
      'batch',
      GetBatchResourceSpec(api_version),
      'ID of the batch job to {0}.'.format(verb),
      required=True).AddToParser(parser)


def AddSessionResourceArg(parser, verb, api_version):
  """Adds session resource argument to parser."""

  def SessionConfig():
    return concepts.ResourceParameterAttributeConfig(
        name='session',
        help_text='Session ID.',
    )

  def GetSessionResourceSpec(api_version):
    return concepts.ResourceSpec(
        'dataproc.projects.locations.sessions',
        api_version=api_version,
        resource_name='session',
        disable_auto_completers=True,
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        locationsId=_LocationAttributeConfig(),
        sessionsId=SessionConfig(),
    )

  concept_parsers.ConceptParser.ForResource(
      'session',
      GetSessionResourceSpec(api_version),
      'ID of the session to {0}.'.format(verb),
      required=True).AddToParser(parser)


def AddNodeGroupResourceArg(parser, verb, api_version):
  """Adds node group resource argument to parser."""

  def NodeGroupConfig():
    return concepts.ResourceParameterAttributeConfig(
        name='node_group',
        help_text='Node group ID.',
    )

  def GetNodeGroupResourceSpec(api_version):
    return concepts.ResourceSpec(
        'dataproc.projects.regions.clusters.nodeGroups',
        api_version=api_version,
        resource_name='node_group',
        disable_auto_completers=True,
        projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        region=_RegionAttributeConfig(),
        clusterName=ClusterConfig(),
        nodeGroupsId=NodeGroupConfig(),
    )

  concept_parsers.ConceptParser.ForResource(
      'node_group',
      GetNodeGroupResourceSpec(api_version),
      'ID of the node group to {0}.'.format(verb),
      required=True).AddToParser(parser)


def OperationConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='The Operation ID.',
  )


def _GetOperationResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.operations',
      api_version=api_version,
      resource_name='operation',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      regionsId=_RegionAttributeConfig(),
      operationsId=OperationConfig(),
  )


def AddOperationResourceArg(parser, verb, api_version):
  name = 'operation'
  concept_parsers.ConceptParser.ForResource(
      name,
      _GetOperationResourceSpec(api_version),
      'The ID of the operation to {0}.'.format(verb),
      required=True).AddToParser(parser)


def AddTimeoutFlag(parser, default='10m'):
  # This may be made visible or passed to the server in future.
  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(),
      default=default,
      help=('Client side timeout on how long to wait for Dataproc operations. '
            'See $ gcloud topic datetimes for information on duration '
            'formats.'),
      hidden=True)


def AddParametersFlag(parser):
  parser.add_argument(
      '--parameters',
      metavar='PARAM=VALUE',
      type=arg_parsers.ArgDict(),
      help="""
          A map from parameter names to values that should be used for those
          parameters. A value must be provided for every configured parameter.
          Parameters can be configured when creating or updating a workflow
          template.
          """,
      dest='parameters')


def AddMinCpuPlatformArgs(parser, include_driver_pool_args=False):
  """Add mininum CPU platform flags for both master and worker instances."""
  help_text = """\
      When specified, the VM is scheduled on the host with a specified CPU
      architecture or a more recent CPU platform that's available in that
      zone. To list available CPU platforms in a zone, run:

          $ gcloud compute zones describe ZONE

      CPU platform selection may not be available in a zone. Zones
      that support CPU platform selection provide an `availableCpuPlatforms`
      field, which contains the list of available CPU platforms in the zone
      (see [Availability of CPU platforms](/compute/docs/instances/specify-min-cpu-platform#availablezones)
      for more information).
      """
  parser.add_argument(
      '--master-min-cpu-platform',
      metavar='PLATFORM',
      required=False,
      help=help_text)
  parser.add_argument(
      '--worker-min-cpu-platform',
      metavar='PLATFORM',
      required=False,
      help=help_text)
  if include_driver_pool_args:
    parser.add_argument(
        '--driver-pool-min-cpu-platform',
        metavar='PLATFORM',
        required=False,
        help=help_text)


def AddComponentFlag(parser):
  """Add optional components flag."""
  help_text = """\
      List of optional components to be installed on cluster machines.

      The following page documents the optional components that can be
      installed:
      https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/optional-components.
      """
  parser.add_argument(
      '--optional-components',
      metavar='COMPONENT',
      type=arg_parsers.ArgList(element_type=lambda val: val.upper()),
      dest='components',
      help=help_text)


def TemplateAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='template',
      help_text='The workflow template name.',
  )


def _GetTemplateResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.workflowTemplates',
      api_version=api_version,
      resource_name='template',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      regionsId=_RegionAttributeConfig(),
      workflowTemplatesId=TemplateAttributeConfig(),
  )


def AddTemplateResourceArg(parser, verb, api_version, positional=True):
  """Adds a workflow template resource argument.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    api_version: api version, for example v1
    positional: bool, if True, means that the instance ID is a positional rather
      than a flag.
  """
  name = 'template' if positional else '--workflow-template'
  concept_parsers.ConceptParser.ForResource(
      name,
      _GetTemplateResourceSpec(api_version),
      'The name of the workflow template to {}.'.format(verb),
      required=True).AddToParser(parser)


def _AutoscalingPolicyResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.autoscalingPolicies',
      api_version=api_version,
      resource_name='autoscaling policy',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      regionsId=_RegionAttributeConfig(),
      autoscalingPoliciesId=concepts.ResourceParameterAttributeConfig(
          name='autoscaling_policy',
          help_text='The autoscaling policy id.',
      ),
  )


def _SessionTemplateResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.locations.sessionTemplates',
      api_version=api_version,
      resource_name='session template',
      disable_auto_completers=True,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_LocationAttributeConfig(),
      sessionTemplatesId=concepts.ResourceParameterAttributeConfig(
          name='session_template',
          help_text='The session template name.',
      ),
  )


def AddAutoscalingPolicyResourceArg(parser, verb, api_version):
  """Adds a workflow template resource argument.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to apply to the resource, such as 'to update'.
    api_version: api version, for example v1
  """
  concept_parsers.ConceptParser.ForResource(
      'autoscaling_policy',
      _AutoscalingPolicyResourceSpec(api_version),
      'The autoscaling policy to {}.'.format(verb),
      required=True).AddToParser(parser)


def AddSessionTemplateResourceArg(parser, verb, api_version):
  """Adds a session template resource argument.

  Args:
    parser: The argparse parser for the command.
    verb: The verb to apply to the resource, such as 'to update'.
    api_version: api version, for example v1
  """
  concept_parsers.ConceptParser.ForResource(
      'session_template',
      _SessionTemplateResourceSpec(api_version),
      'The session template to {}.'.format(verb),
      required=True).AddToParser(parser)


def AddAutoscalingPolicyResourceArgForCluster(parser, api_version):
  """Adds a workflow template resource argument.

  Args:
    parser: the argparse parser for the command.
    api_version: api version, for example v1
  """
  concept_parsers.ConceptParser.ForResource(
      '--autoscaling-policy',
      _AutoscalingPolicyResourceSpec(api_version),
      'The autoscaling policy to use.',
      command_level_fallthroughs={
          'region': ['--region'],
      },
      flag_name_overrides={
          'region': ''
      },
      required=False).AddToParser(parser)


def AddListOperationsFormat(parser):
  parser.display_info.AddTransforms({
      'operationState': _TransformOperationState,
      'operationTimestamp': _TransformOperationTimestamp,
      'operationType': _TransformOperationType,
      'operationWarnings': _TransformOperationWarnings,
  })
  parser.display_info.AddFormat('table(name.segment():label=NAME, '
                                'metadata.operationTimestamp():label=TIMESTAMP,'
                                'metadata.operationType():label=TYPE, '
                                'metadata.operationState():label=STATE, '
                                'status.code.yesno(no=\'\'):label=ERROR, '
                                'metadata.operationWarnings():label=WARNINGS)')


def _TransformOperationType(metadata):
  """Extract operation type from metadata."""
  if 'operationType' in metadata:
    return metadata['operationType']
  elif 'graph' in metadata:
    return 'WORKFLOW'
  return ''


def _TransformOperationState(metadata):
  """Extract operation state from metadata."""
  if 'status' in metadata:
    return metadata['status']['state']
  elif 'state' in metadata:
    return metadata['state']
  return ''


def _TransformOperationTimestamp(metadata):
  """Extract operation start timestamp from metadata."""
  if 'statusHistory' in metadata:
    return metadata['statusHistory'][0]['stateStartTime']
  elif 'startTime' in metadata:
    return metadata['startTime']
  return ''


def _TransformOperationWarnings(metadata):
  """Returns a count of operations if any are present."""
  if 'warnings' in metadata:
    return len(metadata['warnings'])
  return ''


def AddPersonalAuthSessionArgs(parser):
  """Adds the arguments for enabling personal auth sessions."""

  parser.add_argument(
      '--access-boundary',
      help="""
        The path to a JSON file specifying the credential access boundary for
        the personal auth session.

        If not specified, then the access boundary defaults to one that includes
        the following roles on the containing project:

            roles/storage.objectViewer
            roles/storage.objectCreator
            roles/storage.objectAdmin
            roles/storage.legacyBucketReader

        For more information, see:
        https://cloud.google.com/iam/docs/downscoping-short-lived-credentials.
        """)
  parser.add_argument(
      '--openssl-command',
      hidden=True,
      help="""
        The full path to the command used to invoke the OpenSSL tool on this
        machine.
        """)
  parser.add_argument(
      '--refresh-credentials',
      action='store_true',
      default=True,
      hidden=True,
      help="""
        Keep the command running to periodically refresh credentials.
        """)


def ProjectGcsObjectsAccessBoundary(project):
  """Get an access boundary limited to to a project's GCS objects.

  Args:
    project: The project ID for the access boundary.

  Returns:
    A JSON formatted access boundary suitable for creating a downscoped token.
  """
  cab_resource = '//cloudresourcemanager.googleapis.com/projects/{}'.format(
      project)
  access_boundary = {
      'access_boundary': {
          'accessBoundaryRules': [{
              'availableResource':
                  cab_resource,
              'availablePermissions': [
                  'inRole:roles/storage.objectViewer',
                  'inRole:roles/storage.objectCreator',
                  'inRole:roles/storage.objectAdmin',
                  'inRole:roles/storage.legacyBucketReader'
              ]
          }]
      }
  }
  return six.text_type(json.dumps(access_boundary))


def AddSizeFlag(parser):
  """Adds the size field for resizing node groups.

  Args:
    parser: The argparse parser for the command.
  """
  parser.add_argument(
      '--size',
      help=('New size for a node group.'),
      type=int,
      required=True)


def AddGracefulDecommissionTimeoutFlag(parser):
  """Adds a graceful decommission timeout for resizing a node group.

  Args:
    parser: The argparse parser for the command.
  """
  parser.add_argument(
      '--graceful-decommission-timeout',
      help=(
          'Graceful decommission timeout for a node group scale-down resize.'
      ),
      required=False)


def AddDriverPoolId(parser):
  """Adds the customer provided driver pool id field.

  Args:
    parser: The argparse parser for the command.
  """
  parser.add_argument(
      '--driver-pool-id',
      help=("""
            Custom identifier for the DRIVER Node Group being created. If not
            provided, a random string is generated.
            """),
      required=False,
      default=None)


def InstanceConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='instance',
      help_text='The instance name.',
  )


def _GetInstanceResourceSpec(api_version):
  return concepts.ResourceSpec(
      'dataproc.projects.regions.clusters',
      api_version=api_version,
      resource_name='instance',
      disable_auto_completers=True,
      projectId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      region=_RegionAttributeConfig(),
      clusterName=InstanceConfig(),
  )


def AddInstanceResourceArg(parser, verb, api_version):
  concept_parsers.ConceptParser.ForResource(
      'instance',
      _GetInstanceResourceSpec(api_version),
      'The name of the instance to {}.'.format(verb),
      required=True).AddToParser(parser)


def GdceClusterConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='gdce-cluster',
      help_text='The GDCE Cluster path.',
  )


def _GdceLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='gdce-cluster-location',
      help_text='GDCE region for the {resource}.',
      fallthroughs=_DataprocRegionFallthrough(),
  )


def AddGdceClusterResourceArg(parser):
  concept_parsers.ConceptParser.ForResource(
      '--gdce-cluster',
      _GetGdceClusterResourceSpec(),
      'The GDCE cluster to install the Dataproc instance on.',
      required=True,
  ).AddToParser(parser)


def _GetGdceClusterResourceSpec():
  return concepts.ResourceSpec(
      'edgecontainer.projects.locations.clusters',
      resource_name='gdce-cluster',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=_GdceLocationAttributeConfig(),
      clustersId=GdceClusterConfig()
  )
