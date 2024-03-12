# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute instance groups commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress
import re
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instance_templates import service_proxy_aux_data

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      properties.machineType.machine_type(),
      properties.scheduling.preemptible.yesno(yes=true, no=''),
      creationTimestamp
    )"""

_INSTANTIATE_FROM_VALUES = [
    'attach-read-only',
    'blank',
    'custom-image',
    'do-not-include',
    'source-image',
    'source-image-family',
]


def MakeInstanceTemplateArg(plural=False, include_regional=False):
  return flags.ResourceArgument(
      resource_name='instance template',
      completer=completers.InstanceTemplatesCompleter,
      plural=plural,
      global_collection='compute.instanceTemplates',
      regional_collection=('compute.regionInstanceTemplates'
                           if include_regional else None))


def MakeSourceInstanceArg():
  return flags.ResourceArgument(
      name='--source-instance',
      resource_name='instance',
      completer=completers.InstancesCompleter,
      required=False,
      zonal_collection='compute.instances',
      short_help=('The name of the source instance that the instance template '
                  'will be created from.'))


def AddConfigureDiskArgs(parser):
  parser.add_argument(
      '--configure-disk',
      type=arg_parsers.ArgDict(
          spec={
              'auto-delete': arg_parsers.ArgBoolean(),
              'device-name': str,
              'instantiate-from': str,
              'custom-image': str,
          },),
      metavar='PROPERTY=VALUE',
      action='append',
      help="""\
    This option has effect only when used with `--source-instance`. It
    allows you to override how the source-instance's disks are defined in
    the template.

    *device-name*::: Name of the device for which the configuration is being
    overridden.

    *auto-delete*::: If `true`, this persistent disk will be automatically
    deleted when the instance is deleted. However, if the disk is
    detached from the instance, this option won't apply. If not provided,
    the setting is copied from the source instance. Allowed values of the
    flag are: `false`, `no`, `true`, and `yes`.

    *instantiate-from*::: Specifies whether to include the disk and which
    image to use. Valid values are: {}

    *custom-image*::: The custom image to use if custom-image is specified
    for instantiate-from.
    """.format(', '.join(_INSTANTIATE_FROM_VALUES)),
  )


def AddServiceProxyConfigArgs(parser,
                              hide_arguments=False,
                              release_track=base.ReleaseTrack.GA):
  """Adds service proxy configuration arguments for instance templates."""
  service_proxy_group = parser.add_group(hidden=hide_arguments)

  service_proxy_spec = {
      'enabled': None,
      'serving-ports': str,
      'proxy-port': int,
      'tracing': service_proxy_aux_data.TracingState,
      'access-log': str,
      'network': str
  }
  service_proxy_help = textwrap.dedent("""
  Controls whether the Traffic Director service proxy (Envoy) and agent are
  installed and configured on the VM. "cloud-platform" scope is enabled
  automatically to allow connections to the Traffic Director API. Do not use
  the --no-scopes flag.

  *enabled*::: If specified, the service-proxy software will be installed when
  the instance is created. The instance is configured to work with Traffic
  Director.

  *serving-ports*::: Semi-colon-separated (;) list of the ports, specified
  inside quotation marks ("), on which the customer's application/workload
  is serving.

  For example:

        serving-ports="80;8080"

  The service proxy will intercept inbound traffic, then forward it to the
  specified serving port(s) on localhost. If not provided, no incoming traffic
  is intercepted.

  *proxy-port*::: The port on which the service proxy listens.
  The VM intercepts traffic and redirects it to this port to be handled by the
  service proxy. If omitted, the default value is '15001'.

  *tracing*::: Enables the service proxy to generate distributed tracing
  information. If set to ON, the service proxy's control plane generates a
  configuration that enables request ID-based tracing. For more information,
  refer to the `generate_request_id` documentation for the Envoy proxy. Allowed
  values are `ON` and `OFF`.

  *access-log*::: The filepath for access logs sent to the service proxy by the
  control plane. All incoming and outgoing requests are recorded in this file.
  For more information, refer to the file access log documentation for the Envoy
  proxy.

  *network*::: The name of a valid VPC network. The Google Cloud Platform VPC
  network used by the service proxy's control plane to generate dynamic
  configuration for the service proxy.
  """)

  if release_track == base.ReleaseTrack.ALPHA:
    service_proxy_spec.update({
        'intercept-dns': None,
        'source': str,
    })
    service_proxy_help += textwrap.dedent("""
    *intercept-dns*::: Enables interception of UDP traffic by the service proxy.

    *source*::: The Google Cloud Storage bucket location source
    for the Envoy. The service-proxy-agent will download the archive from Envoy
    and install it on the virtual machine, unpacking it into the root (/)
    directory of the virtual machine. Therefore, the archive must contain not
    only the executable and license files but they must be located in the
    correct directories within the archive. For example:
    /usr/local/bin/envoy and /usr/local/doc/envoy-LICENSE
    """)

  if (release_track == base.ReleaseTrack.ALPHA or
      release_track == base.ReleaseTrack.BETA):
    service_proxy_spec.update({
        'intercept-all-outbound-traffic': None,
        'exclude-outbound-ip-ranges': str,
        'exclude-outbound-port-ranges': str,
        'scope': str,
        'mesh': str,
        'project-number': str,
    })
    service_proxy_help += textwrap.dedent("""
    *intercept-all-outbound-traffic*::: Enables interception of all outgoing
    traffic. The traffic is intercepted by the service proxy and then redirected
    to external host.

    *exclude-outbound-ip-ranges*::: Semi-colon-separated (;) list of the IPs or
    CIDRs, specified inside quotation marks ("), that should be excluded from
    redirection. Only applies when `intercept-all-outbound-traffic` flag is set.

    For example:

         exclude-outbound-ip-ranges="8.8.8.8;129.168.10.0/24"

    *exclude-outbound-port-ranges*::: Semi-colon-separated (;) list of the ports
    or port ranges, specified inside quotation marks ("), that should be
    excluded from redirection. Only applies when
    `intercept-all-outbound-traffic` flag is set.

    For example:

         exclude-outbound-port-ranges="81;8080-8090"

    *scope*::: Scope defines a logical configuration boundary for a Gateway
    resource. On VM boot up, the service proxy reaches the Traffic Director to
    retrieve routing information that corresponds to the routes attached to the
    gateway with this scope name. When scope is specified, the network value is
    ignored. You cannot specify `scope` and `mesh` values at the same time.

    *mesh*::: Mesh defines a logical configuration boundary for a Mesh resource.
    On VM boot up, the service proxy reaches the Traffic Director to retrieve
    routing information that corresponds to the routes attached to the mesh with
    this mesh name. When mesh is specified, the network value is ignored. You
    cannot specify `scope` and `mesh` values at the same time.

    *project-number*::: Project number defines the project where Mesh and
    Gateway resources are created. If not specified, the project where the
    instance exists is used.
    """)

  service_proxy_group.add_argument(
      '--service-proxy',
      type=arg_parsers.ArgDict(
          spec=service_proxy_spec,
          allow_key_only=True,
          required_keys=['enabled']),
      hidden=hide_arguments,
      help=service_proxy_help)
  service_proxy_group.add_argument(
      '--service-proxy-labels',
      metavar='KEY=VALUE, ...',
      type=arg_parsers.ArgDict(),
      hidden=hide_arguments,
      help="""\
      Labels that you can apply to your service proxy. These will be reflected in your Envoy proxy's bootstrap metadata.
      These can be any `key=value` pairs that you want to set as proxy metadata (for example, for use with config filtering).
      You might use these flags for application and version labels: `app=review` and/or `version=canary`.
      """)
  service_proxy_group.add_argument(
      '--service-proxy-agent-location',
      metavar='LOCATION',
      hidden=True,
      help="""\
      GCS bucket location of service-proxy-agent. Mainly used for testing and development.
      """)
  service_proxy_group.add_argument(
      '--service-proxy-xds-version',
      type=int,
      hidden=True,
      help="""\
      xDS version of the service proxy to be installed.
      """)


def ValidateServiceProxyFlags(args):
  """Validates the values of all --service-proxy related flags."""

  if getattr(args, 'service_proxy', False):
    if args.no_scopes:
      # --no-scopes flag needs to be removed for adding cloud-platform scope.
      # This is required for TrafficDirector to work properly.
      raise exceptions.ConflictingArgumentsException('--service-proxy',
                                                     '--no-scopes')

    if 'serving-ports' in args.service_proxy:
      try:
        serving_ports = list(
            map(int, args.service_proxy['serving-ports'].split(';')))
        for port in serving_ports:
          if port < 1 or port > 65535:
            # valid port range is 1 - 65535
            raise ValueError
      except ValueError:
        # an invalid port is present in the list of workload ports.
        raise exceptions.InvalidArgumentException(
            'serving-ports',
            'List of ports can only contain numbers between 1 and 65535.')

    if 'proxy-port' in args.service_proxy:
      try:
        proxy_port = args.service_proxy['proxy-port']
        if proxy_port < 1025 or proxy_port > 65535:
          # valid range for proxy-port is 1025 - 65535
          raise ValueError
      except ValueError:
        raise exceptions.InvalidArgumentException(
            'proxy-port', 'Port value can only be between 1025 and 65535.')

    if 'exclude-outbound-ip-ranges' in args.service_proxy:
      if 'intercept-all-outbound-traffic' not in args.service_proxy:
        raise exceptions.RequiredArgumentException(
            'intercept-all-outbound-traffic',
            'exclude-outbound-ip-ranges parameters requires '
            'intercept-all-outbound-traffic to be set')

      ip_ranges = args.service_proxy['exclude-outbound-ip-ranges'].split(';')
      for ip_range in ip_ranges:
        try:
          ipaddress.ip_network(ip_range)
        except ValueError:
          # An invalid IP/CIDR is present in the list of excluded IP ranges.
          raise exceptions.InvalidArgumentException(
              'exclude-outbound-ip-ranges',
              'List of IPs may contain only IPs & CIDRs.')

    if 'exclude-outbound-port-ranges' in args.service_proxy:
      if 'intercept-all-outbound-traffic' not in args.service_proxy:
        raise exceptions.RequiredArgumentException(
            'intercept-all-outbound-traffic',
            'exclude-outbound-port-ranges parameters requires '
            'intercept-all-outbound-traffic to be set')

      port_ranges = (
          args.service_proxy['exclude-outbound-port-ranges'].split(';'))
      for port_range in port_ranges:
        ports = port_range.split('-')
        try:
          if len(ports) == 1:
            ValidateSinglePort(ports[0])
          elif len(ports) == 2:
            ValidateSinglePort(ports[0])
            ValidateSinglePort(ports[1])
          else:
            raise ValueError
        except ValueError:
          # An invalid port is present in the list of excluded port ranges.
          raise exceptions.InvalidArgumentException(
              'exclude-outbound-port-ranges',
              'List of port ranges can only contain numbers between 1 and '
              '65535, i.e. "80;8080-8090".')

    if 'scope' in args.service_proxy and 'mesh' in args.service_proxy:
      raise exceptions.ConflictingArgumentsException('--service-proxy:scope',
                                                     '--service-proxy:mesh')


def ValidateSinglePort(port_str):
  port = int(port_str)
  if port < 1 or port > 65535:
    # valid port range is 1 - 65535
    raise ValueError


def AddMeshArgs(parser, hide_arguments=False):
  """Adds Anthos Service Mesh configuration arguments for instance templates."""

  mesh_group = parser.add_group(hidden=hide_arguments)
  mesh_group.add_argument(
      '--mesh',
      type=arg_parsers.ArgDict(
          spec={
              'gke-cluster': str,
              'workload': str
          },
          allow_key_only=False,
          required_keys=['gke-cluster', 'workload']),
      hidden=hide_arguments,
      help="""\
      Controls whether the Anthos Service Mesh service proxy (Envoy) and agent are installed and configured on the VM.
      "cloud-platform" scope is enabled automatically to allow the service proxy to be started.
      Do not use the `--no-scopes` flag.

      *gke-cluster*::: The location/name of the GKE cluster. The location can be a zone or a
          region, e.g. ``us-central1-a/my-cluster''.

      *workload*::: The workload identifier of the VM. In a GKE cluster, it is
          the identifier namespace/name of the `WorkloadGroup` custom resource representing the VM
          workload, e.g. ``foo/my-workload''.
      """)


def ValidateMeshFlag(args):
  """Validates the values of the --mesh flag."""

  if getattr(args, 'mesh', False):
    if args.no_scopes:
      # --no-scopes flag needs to be removed for adding cloud-platform scope.
      # This is required for ASM's service proxy to work properly.
      raise exceptions.ConflictingArgumentsException('--mesh', '--no-scopes')

    rgx = r'(.*)\/(.*)'
    try:
      if not re.match(rgx, args.mesh['gke-cluster']):
        raise ValueError
    except ValueError:
      raise exceptions.InvalidArgumentException(
          'gke-cluster',
          'GKE cluster value should have the format location/name.')
    try:
      if not re.match(rgx, args.mesh['workload']):
        raise ValueError
    except ValueError:
      raise exceptions.InvalidArgumentException(
          'workload', 'Workload value should have the format namespace/name.')


def AddPostKeyRevocationActionTypeArgs(parser):
  """Helper to add --post-key-revocation-action-type flag."""
  help_text = ('Specifies the behavior of the instance when the KMS key of one '
               'of its attached disks is revoked. The default is noop.')
  choices_text = {
      'noop':
          'No operation is performed.',
      'shutdown': ('The instance is shut down when the KMS key of one of '
                   'its attached disks is revoked.')
  }
  parser.add_argument(
      '--post-key-revocation-action-type',
      choices=choices_text,
      metavar='POLICY',
      required=False,
      help=help_text)


def AddKeyRevocationActionTypeArgs(parser):
  """Helper to add --key-revocation-action-type flag."""
  help_text = ('Specifies the behavior of the instance when the KMS key of one '
               'of its attached disks is revoked. The default is none.')
  choices_text = {
      'none': 'No operation is performed.',
      'stop': 'The instance is stopped when the KMS key of one of its attached '
              'disks is revoked.'
  }
  parser.add_argument(
      '--key-revocation-action-type',
      choices=choices_text,
      metavar='POLICY',
      required=False,
      help=help_text)


def ValidateSourceInstanceFlags(args):
  """Validates --source-instance flag."""

  if getattr(args, 'source_instance', False):
    if getattr(args, 'machine_type', False):
      # --machine-type flag cannot be used with --source-instance flag since API
      # doesn't support overriding machine type if source instance is provided
      raise exceptions.ConflictingArgumentsException('--source-instance',
                                                     '--machine-type')
    if getattr(args, 'labels', False):
      # --labels flag cannot be used with --source-instance flag since API
      # doesn't support overriding labels if source instance is provided
      raise exceptions.ConflictingArgumentsException('--source-instance',
                                                     '--labels')

    if getattr(args, 'configure_disk', False):
      for disk in args.configure_disk:
        if 'device-name' not in disk:
          raise exceptions.RequiredArgumentException(
              'device-name',
              '`--configure-disk` requires `device-name` to be set')

        instantiate_from = disk.get('instantiate-from')
        custom_image = disk.get('custom-image')
        if custom_image and instantiate_from != 'custom-image':
          raise exceptions.InvalidArgumentException(
              '--configure-disk',
              'Value for `instantiate-from` must be \'custom-image\' if the key '
              '`custom-image` is specified.')
        if instantiate_from == 'custom-image' and custom_image is None:
          raise exceptions.InvalidArgumentException(
              '--configure-disk',
              'Value for \'custom-image\' must be specified if `instantiate-from`'
              ' has value `custom-image`.')
