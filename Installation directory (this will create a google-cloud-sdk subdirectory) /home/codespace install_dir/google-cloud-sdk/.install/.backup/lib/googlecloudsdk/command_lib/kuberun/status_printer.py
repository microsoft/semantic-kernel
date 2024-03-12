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
"""Custom printer for KubeRun Application Status."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.command_lib.kuberun import pretty_print
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.core.resource import resource_printer
from six.moves.urllib_parse import urlparse

_PRINTER_FORMAT = 'status'

_INGRESS_EXPLANATION_TEMPLATE = """If your component URL ends in \
'.example.com', you must use the Ingress IP in order to reach the component.
To do so, type `curl -H "Host: <component URL without http://>" http://{}`.

To avoid having to specify a Host header for every request, follow the steps \
to configure a default domain for your cluster at \
https://cloud.google.com/kuberun/docs/default-domain.
"""


def _ComponentTable(components):
  """Format component to table."""
  con = console_attr.GetConsoleAttr()
  rows = []
  for component in components:
    status_symbol = pretty_print.GetReadySymbol(component.deployment_state)
    status_color = pretty_print.GetReadyColor(component.deployment_state)
    rows.append((con.Colorize(status_symbol, status_color), component.name,
                 component.deployment_reason, component.commit_id[:6],
                 component.deployment_time, component.url))

  return cp.Table([('', 'NAME', 'REASON', 'COMMIT', 'LAST-DEPLOYED', 'URL')] +
                  rows, console_attr=con)


def _ModulesTable(modules):
  """Format module to table."""
  con = console_attr.GetConsoleAttr()
  rows = []
  for module in modules:
    for component in module.components:
      status_symbol = pretty_print.GetReadySymbol(component.deployment_state)
      status_color = pretty_print.GetReadyColor(component.deployment_state)
      rows.append((con.Colorize(status_symbol, status_color), component.name,
                   module.name, component.deployment_reason,
                   component.commit_id[:6], component.deployment_time,
                   component.url))

  return cp.Table([('', 'NAME', 'MODULE', 'REASON', 'COMMIT', 'LAST-DEPLOYED',
                    'URL')] + rows, console_attr=con)


class ApplicationStatusPrinter(cp.CustomPrinterBase):
  """Prints the KubeRun Application Status custom human-readable format."""

  @staticmethod
  def Register(parser):
    """Register this custom printer with the given parser."""
    resource_printer.RegisterFormatter(
        _PRINTER_FORMAT, ApplicationStatusPrinter, hidden=True)
    parser.display_info.AddFormat(_PRINTER_FORMAT)

  def Transform(self, record):
    """Transform ApplicationStatus into the output structure of marker classes.

    Args:
      record: a dict object

    Returns:
      lines formatted for output
    """
    status = record['status']
    results = [
        cp.Section([
            cp.Labeled([('Environment', record['environment']),
                        ('Ingress IP', status.ingress_ip)])
        ])
    ]
    if len(status.modules) == 1:
      results.append(
          cp.Section([cp.Labeled(
              [
                  ('Components', _ComponentTable(status.modules[0].components))
              ])], max_column_width=25))
    else:
      results.append(
          cp.Section(
              [cp.Labeled([('Components', _ModulesTable(status.modules))])],
              max_column_width=25))
    results.append(cp.Section([
        '\n',
        _INGRESS_EXPLANATION_TEMPLATE.format(status.ingress_ip)
    ]))
    return cp.Lines(results)


class ComponentStatusPrinter(cp.CustomPrinterBase):
  """Prints the KubeRun Component Status in a custom human-readable format."""

  @staticmethod
  def Register(parser):
    """Register this custom printer with the given parser."""
    resource_printer.RegisterFormatter(
        _PRINTER_FORMAT, ComponentStatusPrinter, hidden=True)
    parser.display_info.AddFormat(_PRINTER_FORMAT)

  def Transform(self, record):
    """Transform ComponentStatus into the output structure of marker classes.

    Args:
      record: a dict object

    Returns:
      lines formatted for output
    """
    con = console_attr.GetConsoleAttr()
    component = record['status']
    status = con.Colorize(
        pretty_print.GetReadySymbol(component.deployment_state),
        pretty_print.GetReadyColor(component.deployment_state))
    component_url = urlparse(component.url)

    results = [
        cp.Section([
            con.Emphasize('{} Component {} in environment {}'.format(
                status, component.name, record['environment'])),
            'Deployed at {} from commit {}\n'.format(component.deployment_time,
                                                     component.commit_id)
        ]),
        cp.Section([
            cp.Labeled([('Component Service(s)', cp.Lines(component.services))
                       ]),
        ]),
        cp.Section([
            '\nGet more details about services using kuberun '
            'core services describe SERVICE'
        ])
    ]

    if component.deployment_state == 'Ready':
      results.append(
          cp.Section([
              '\nTo invoke this component, run:',
              '  curl {}'.format(component.url), 'OR',
              '  curl -H "Host: {}" {}://{}'.format(component_url.netloc,
                                                    component_url.scheme,
                                                    record['ingressIp'])
          ]))
    elif component.deployment_state == 'Failed':
      msg = '\n! Deployment failed with message: {}'.format(
          component.deployment_message)
      results.append(con.Emphasize(con.Colorize(msg, 'yellow')))
    return cp.Lines(results)
