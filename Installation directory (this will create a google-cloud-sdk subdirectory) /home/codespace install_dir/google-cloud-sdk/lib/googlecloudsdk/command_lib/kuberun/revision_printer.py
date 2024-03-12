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
"""Revision-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.command_lib.kuberun import k8s_object_printer
from googlecloudsdk.command_lib.kuberun import kubernetes_consts
from googlecloudsdk.core.resource import custom_printer_base as cp
import six

REVISION_PRINTER_FORMAT = 'revision'


def FormatSecretKeyRef(v):
  return '{}:{}'.format(v.secretKeyRef.name, v.secretKeyRef.key)


def FormatSecretVolumeSource(v):
  if v.items:
    return '{}:{}'.format(v.secretName, v.items[0].key)
  else:
    return v.secretName


def FormatConfigMapKeyRef(v):
  return '{}:{}'.format(v.configMapKeyRef.name, v.configMapKeyRef.key)


def FormatConfigMapVolumeSource(v):
  if v.items:
    return '{}:{}'.format(v.name, v.items[0].key)
  else:
    return v.name


class RevisionPrinter(cp.CustomPrinterBase):
  """Prints the run Revision in a custom human-readable format.

  Format specific to Cloud Run revisions. Only available on Cloud Run commands
  that print revisions.
  """

  def Transform(self, record):
    """Transform a revision into the output structure of marker classes."""
    rev = revision.Revision(record)
    fmt = cp.Lines([
        k8s_object_printer.FormatHeader(rev),
        k8s_object_printer.FormatLabels(rev.labels),
        ' ',
        self.TransformSpec(rev),
        k8s_object_printer.FormatReadyMessage(rev),
    ])
    return fmt

  def _GetUserEnvironmentVariables(self, container):
    return cp.Mapped(k8s_object_printer.OrderByKey(container.env.literals))

  def _GetSecrets(self, record, container):
    secrets = {}
    secrets.update(
        {k: FormatSecretKeyRef(v) for k, v in container.env.secrets.items()}
    )
    secrets.update(
        {
            k: FormatSecretVolumeSource(v)
            for k, v in record.MountedVolumeJoin(container, 'secrets').items()
        }
    )
    return cp.Mapped(k8s_object_printer.OrderByKey(secrets))

  def _GetConfigMaps(self, record, container):
    config_maps = {}
    config_maps.update(
        {
            k: FormatConfigMapKeyRef(v)
            for k, v in container.env.config_maps.items()
        }
    )
    config_maps.update(
        {
            k: FormatConfigMapVolumeSource(v)
            for k, v in record.MountedVolumeJoin(
                container, 'config_maps'
            ).items()
        }
    )
    return cp.Mapped(k8s_object_printer.OrderByKey(config_maps))

  def _GetTimeout(self, record):
    if record.timeout is not None:
      return '{}s'.format(record.timeout)
    return None

  def _GetInitInstances(self, record):
    if record.annotations:
      return record.annotations.get(revision.INITIAL_SCALE_ANNOTATION, '')
    return None

  def _GetMinInstances(self, record):
    if record.annotations:
      return record.annotations.get(revision.MIN_SCALE_ANNOTATION, '')
    return None

  def _GetMaxInstances(self, record):
    if record.annotations:
      return record.annotations.get(revision.MAX_SCALE_ANNOTATION, '')
    return None

  def GetContainer(self, record, container):
    limits = collections.defaultdict(str, container.resource_limits)
    return cp.Labeled([
        ('Image', container.image),
        ('Command', ' '.join(container.command)),
        ('Args', ' '.join(container.args)),
        (
            'Port',
            ' '.join(six.text_type(p.containerPort) for p in container.ports),
        ),
        ('Memory', limits['memory']),
        ('CPU', limits['cpu']),
        ('GPU', limits[revision.NVIDIA_GPU_RESOURCE]),
        ('Env vars', self._GetUserEnvironmentVariables(container)),
        ('Secrets', self._GetSecrets(record, container)),
        ('Config Maps', self._GetConfigMaps(record, container)),
    ])

  def GetContainers(self, record):
    def Containers():
      for container in record.containers:
        if container.name:
          key = 'Container {name}'.format(name=container.name)
        else:
          key = 'Container'
        value = self.GetContainer(record, container)
        yield (key, value)

    return cp.Mapped(Containers())

  def TransformSpec(self, record):
    return cp.Lines([
        self.GetContainers(record),
        cp.Labeled([
            ('Service account', record.spec.serviceAccountName),
            ('Concurrency', record.concurrency),
            ('Initial Instances', self._GetInitInstances(record)),
            ('Min Instances', self._GetMinInstances(record)),
            ('Max Instances', self._GetMaxInstances(record)),
            ('Timeout', self._GetTimeout(record)),
        ]),
    ])


def Active(record):
  """Returns True/False/None indicating the active status of the resource."""
  active_cond = [
      x
      for x in record.get(kubernetes_consts.FIELD_STATUS, {}).get(
          kubernetes_consts.FIELD_CONDITIONS, []
      )
      if x[kubernetes_consts.FIELD_TYPE] == kubernetes_consts.VAL_ACTIVE
  ]
  if active_cond:
    status = active_cond[0].get(kubernetes_consts.FIELD_STATUS)
    return True if status == kubernetes_consts.VAL_TRUE else False
  else:
    return None
