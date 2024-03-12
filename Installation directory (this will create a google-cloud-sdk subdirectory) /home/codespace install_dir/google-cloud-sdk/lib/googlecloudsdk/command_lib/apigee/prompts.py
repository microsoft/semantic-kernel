# -*- coding: utf-8 -*- # Lint as: python3
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
"""Helper methods for interactive prompting."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core.console import console_io


def ResourceFromFreeformPrompt(name, long_name, list_func):
  """Prompts the user to select a resource.

  Args:
    name: the name of the resource. For example, "environment" or "developer".
    long_name: a longer form of `name` which the user will see in prompts.
      Should explain the context in which the resource will be used. For
      example, "the environment to be updated".
    list_func: a function that returns the names of existing resources.

  Returns:
    The resource's identifier if successful, or None if not.
  """
  resource_list = []
  try:
    resource_list = list_func()
  except errors.RequestError:
    # Organization list flakiness, no matches, etc.
    pass

  entity_names = resource_args.ENTITIES[name]
  if resource_list:
    enter_manually = "(some other %s)" % entity_names.docs_name
    choice = console_io.PromptChoice(
        resource_list + [enter_manually],
        prompt_string="Select %s:" % long_name)
    # If the user selected an option from resource_list, not the "enter
    # manually" option at the bottom...
    if choice < len(resource_list):
      return resource_list[choice]

  valid_pattern = resource_args.ValidPatternForEntity(name)
  validator = lambda response: valid_pattern.search(response) is not None
  error_str = "Doesn't match the expected format of a " + entity_names.docs_name

  prompt_message = "Enter %s: " % long_name
  return console_io.PromptWithValidator(validator, error_str, prompt_message)


def ListFromFreeformPrompt(message, add_message, empty_done_message):
  """Returns a list of strings inputted by the user.

  Args:
    message: the message to display when prompting for a new string.
    add_message: the menu option for adding a new string to the list.
    empty_done_message: the menu option to display for the "Done" option if no
      strings have been selected.
  """
  chosen = []
  menu_option = 0
  while menu_option <= len(chosen):
    if menu_option < len(chosen):
      chosen = chosen[:menu_option] + chosen[menu_option + 1:]
    elif menu_option == len(chosen):
      input_data = console_io.PromptResponse(message)
      chosen.append(input_data)

    options = ["Remove `%s`" % item for item in chosen]
    options.append(add_message)
    options.append("Done" if chosen else empty_done_message)
    menu_option = console_io.PromptChoice(options)
  return chosen


def ResourceListFromPrompt(name, list_func, end_empty_message=None):
  """Returns a list of resources selected by the user.

  Args:
    name: the entity name for the resources being selected.
    list_func: a zero argument function that will return a list of existing
      resources.
    end_empty_message: text for the menu option that will return an empty list.
  """
  resource_list = list_func()
  if not resource_list:
    docs_name = resource_args.ENTITIES[name].docs_name
    raise errors.EntityNotFoundError(
        message=("Could not find any %s to select. Check that at least one %s "
                 "has been created and is properly configued for use." %
                 (docs_name, docs_name)))

  chosen = []
  available = None
  menu_option = len(resource_list) + 1
  while menu_option != len(resource_list):
    if menu_option < len(chosen):
      # Falls within the "chosen" menu options. Remove the resource at exactly
      # the selected slot.
      chosen = chosen[:menu_option] + chosen[menu_option + 1:]
    elif menu_option < len(resource_list):
      # Falls within the "available" menu options.
      index = menu_option - len(chosen)
      chosen.append(available[index])
    available = [item for item in resource_list if item not in chosen]

    options = ["Remove `%s`" % item for item in chosen]
    options += ["Add `%s`" % item for item in available]
    if chosen:
      message = "Currently selected: %s" % ", ".join(chosen)
      options.append("Done")
    else:
      message = "No %s selected yet" % resource_args.ENTITIES[name].docs_name
      if end_empty_message is not None:
        options.append(end_empty_message)
    menu_option = console_io.PromptChoice(options, message=message)
  return chosen
