# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Specifications for resource-identifying command line parameters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers

# The singular name is used internally by gcloud to identify the reference type
# and should be named according to the rules in the Cloud SDK internal docs.
# The plural name refers to the entity name in the API resource path, e.g.,
# apigee.googleapis.com/v1/myEntityNamePlurals/...
_EntityNames = collections.namedtuple(
    "EntityNames",
    "singular plural docs_name valid_pattern secondary_description")

_ENTITY_TUPLES = [
    _EntityNames("project", "projects", "projects", None,
                 "GCP project containing the {resource}."),
    _EntityNames(
        "organization", "organizations", "organization",
        r"^[a-z][-a-z0-9]{0,30}[a-z0-9]$",
        "Apigee organization containing the {resource}. If "
        "unspecified, the Cloud Platform project's associated "
        "organization will be used."),
    _EntityNames("api", "apis", "API proxy", r"^[\s\w.-]{1,255}$",
                 "API proxy for the {resource}."),
    _EntityNames("environment", "environments", "environment",
                 r"^[a-z][-a-z0-9]{0,30}[a-z0-9]$",
                 "Deployment environment of the {resource}."),
    _EntityNames("revision", "revisions", "revision", None,
                 "Revision of the {resource}."),
    _EntityNames("deployment", "deployments", "deployment", None,
                 "Relevant deployment of the {resource}."),
    _EntityNames("operation", "operations", "operation", None,
                 "Operation operating on the {resource}."),
    _EntityNames("product", "apiproducts", "API product",
                 r"^[A-Za-z0-9._$ %-]+$",
                 "Relevant product for the {resource}."),
    _EntityNames("developer", "developers", "developer", None,
                 "Developer of the {resource}."),
    _EntityNames("app", "apps", "application", None,
                 "Relevant application for the {resource}."),
    _EntityNames("archive_deployment", "archiveDeployments",
                 "archive deployment", None,
                 "Archive deployment for {resource}")
]
ENTITIES = {item.singular: item for item in _ENTITY_TUPLES}


def _ValidPatternForEntity(name):
  pattern = ENTITIES[name].valid_pattern
  return r".*" if pattern is None else pattern


def ValidPatternForEntity(entity_name):
  """Returns a compiled regex that matches valid values for `entity_name`."""
  return re.compile(_ValidPatternForEntity(entity_name))


def AttributeConfig(name, fallthroughs=None, help_text=None, validate=False):
  """Returns a ResourceParameterAttributeConfig for the attribute named `name`.

  Args:
    name: singular name of the attribute. Must exist in ENTITIES.
    fallthroughs: optional list of gcloud fallthrough objects which should be
      used to get this attribute's value if the user doesn't specify one.
    help_text: help text to use for this resource parameter instead of the
      default help text for the attribute.
    validate: whether to check that user-provided value for this attribute
      matches the expected pattern.
  """
  validator = None
  if validate:
    validator = arg_parsers.RegexpValidator(
        _ValidPatternForEntity(name),
        "Must match the format of a valid {2} ({3})".format(*ENTITIES[name]))

  return concepts.ResourceParameterAttributeConfig(
      name=name,
      parameter_name=ENTITIES[name].plural,
      value_type=validator,
      help_text=help_text or ENTITIES[name].secondary_description,
      fallthroughs=fallthroughs)


def ResourceSpec(path, fallthroughs=tuple(), help_texts=None, validate=False):
  """Returns a ResourceSpec for the resource path `path`.

  Args:
    path: a list of attribute names. All must exist in ENTITIES.
    fallthroughs: optional list of googlecloudsdk.command_lib.apigee.Fallthrough
      objects which will provide default values for the attributes in `path`.
    help_texts: a mapping of attribute names to help text strings, to use
      instead of their default help text.
    validate: whether to check that the user-provided resource matches the
      expected naming conventions of the resource path.
  """
  help_texts = collections.defaultdict(lambda: None, help_texts or {})
  entities = [ENTITIES[name] for name in path]
  ids = {}
  for entity in entities:
    relevant_fallthroughs = [
        fallthrough for fallthrough in fallthroughs
        if entity.singular in fallthrough
    ]
    config = AttributeConfig(
        entity.singular,
        relevant_fallthroughs,
        help_texts[entity.singular],
        validate=validate)
    ids[entity.plural + "Id"] = config

  return concepts.ResourceSpec(
      "apigee." + ".".join(entity.plural for entity in entities),
      resource_name=entities[-1].docs_name,
      **ids)


def AddSingleResourceArgument(parser,
                              resource_path,
                              help_text,
                              fallthroughs=tuple(),
                              positional=True,
                              argument_name=None,
                              required=None,
                              prefixes=False,
                              validate=False,
                              help_texts=None):
  """Creates a concept parser for `resource_path` and adds it to `parser`.

  Args:
    parser: the argparse.ArgumentParser to which the concept parser will be
      added.
    resource_path: path to the resource, in `entity.other_entity.leaf` format.
    help_text: the help text to display when describing the resource as a whole.
    fallthroughs: fallthrough providers for entities in resource_path.
    positional: whether the leaf entity should be provided as a positional
      argument, rather than as a flag.
    argument_name: what to name the leaf entity argument. Defaults to the leaf
      entity name from the resource path.
    required: whether the user is required to provide this resource. Defaults to
      True for positional arguments, False otherwise.
    prefixes: whether to append prefixes to the non-leaf arguments.
    validate: whether to check that the user-provided resource matches the
      expected naming conventions of the resource path.
    help_texts: custom help text for generated arguments. Defaults to each
      entity using a generic help text.
  """
  split_path = resource_path.split(".")
  if argument_name is None:
    leaf_element_name = split_path[-1]
    if positional:
      argument_name = leaf_element_name.upper()
    else:
      argument_name = "--" + leaf_element_name.replace("_", "-")

  if required is None:
    required = positional

  concept_parsers.ConceptParser.ForResource(
      argument_name,
      ResourceSpec(split_path, fallthroughs, help_texts, validate=validate),
      help_text,
      required=required,
      prefixes=prefixes).AddToParser(parser)
