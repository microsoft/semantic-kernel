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
"""Essential Contacts API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis

API_NAME = 'essentialcontacts'
ALPHA_API_VERSION = 'v1alpha1'
BETA_API_VERSION = 'v1beta1'
GA_API_VERSION = 'v1'
DEFAULT_API_VERSION = GA_API_VERSION

_CONTACT_TYPES_BY_VERSION = {
    ALPHA_API_VERSION: {
        'param_name': 'googleCloudEssentialcontactsV1alpha1Contact',
        'message_name': 'GoogleCloudEssentialcontactsV1alpha1Contact'
    },
    BETA_API_VERSION: {
        'param_name': 'googleCloudEssentialcontactsV1beta1Contact',
        'message_name': 'GoogleCloudEssentialcontactsV1beta1Contact'
    },
    GA_API_VERSION: {
        'param_name': 'googleCloudEssentialcontactsV1Contact',
        'message_name': 'GoogleCloudEssentialcontactsV1Contact'
    }
}


def GetClientInstance(version=DEFAULT_API_VERSION):
  return apis.GetClientInstance(
      api_name=API_NAME, api_version=version, no_http=False)


def GetMessages(version=DEFAULT_API_VERSION):
  return apis.GetMessagesModule(api_name=API_NAME, api_version=version)


def GetContactMessage(version=DEFAULT_API_VERSION):
  """Gets the contact message for the specified version of the API."""
  versioned_message_type = _CONTACT_TYPES_BY_VERSION[version]['message_name']
  return getattr(GetMessages(version), versioned_message_type)


def GetContactParamName(version=DEFAULT_API_VERSION):
  return _CONTACT_TYPES_BY_VERSION[version]['param_name']


def GetContactNotificationCategoryEnum(version=DEFAULT_API_VERSION):
  return GetContactMessage(
      version).NotificationCategorySubscriptionsValueListEntryValuesEnum


class ContactsClient():
  """Client for Essential Contacts API."""

  def __init__(self, version=DEFAULT_API_VERSION):

    self.client = GetClientInstance(version)

    self._messages = self.client.MESSAGES_MODULE

    self._projects_service = self.client.projects_contacts

    self._folders_service = self.client.folders_contacts

    self._organizations_service = self.client.organizations_contacts

    self.contact_message = GetContactMessage(version)

    self.contact_param_name = GetContactParamName(version)

  def Create(self, parent_name, email, notification_categories, language_tag):
    """Creates an Essential Contact.

    Args:
      parent_name: the full id of the resource to create the contact for in the
        form of [projects|folders|organizations]/{resourceId}
      email: the contact's email address.
      notification_categories: the categories of notifications this contact
        should receive.
      language_tag: the contact's preferred language to receive communication
        in.

    Returns:
      The created contact.
    """
    contact = self.contact_message(
        email=email,
        notificationCategorySubscriptions=notification_categories,
        languageTag=language_tag)
    args = {'parent': parent_name, self.contact_param_name: contact}

    if parent_name.startswith('folders'):
      create_req = self._messages.EssentialcontactsFoldersContactsCreateRequest(
          **args)
      return self._folders_service.Create(create_req)
    if parent_name.startswith('organizations'):
      create_req = self._messages.EssentialcontactsOrganizationsContactsCreateRequest(
          **args)
      return self._organizations_service.Create(create_req)

    create_req = self._messages.EssentialcontactsProjectsContactsCreateRequest(
        **args)
    return self._projects_service.Create(create_req)

  def Update(self, contact_name, notification_categories, language_tag):
    """Updates an Essential Contact.

    Args:
      contact_name: the full id of the contact to update in the form of
        [projects|folders|organizations]/{resourceId}/contacts/{contactId}
      notification_categories: the categories of notifications this contact
        should receive, or None if not updating notification categories.
      language_tag: the contact's preferred language to receive communication
        in, or None if not updating language.

    Returns:
      The updated contact.
    """
    update_masks = []
    if notification_categories:
      update_masks.append('notification_category_subscriptions')
    if language_tag:
      update_masks.append('language_tag')
    update_mask = ','.join(update_masks)

    contact = self.contact_message(
        notificationCategorySubscriptions=notification_categories,
        languageTag=language_tag)
    args = {
        'name': contact_name,
        'updateMask': update_mask,
        self.contact_param_name: contact
    }

    if contact_name.startswith('folders'):
      update_req = self._messages.EssentialcontactsFoldersContactsPatchRequest(
          **args)
      return self._folders_service.Patch(update_req)
    if contact_name.startswith('organizations'):
      update_req = self._messages.EssentialcontactsOrganizationsContactsPatchRequest(
          **args)
      return self._organizations_service.Patch(update_req)

    update_req = self._messages.EssentialcontactsProjectsContactsPatchRequest(
        **args)
    return self._projects_service.Patch(update_req)

  def Delete(self, contact_name):
    """Deletes an Essential Contact.

    Args:
      contact_name: the full id of the contact to delete in the form of
        [projects|folders|organizations]/{resourceId}/contacts/{contactId}

    Returns:
      Empty response message.
    """
    if contact_name.startswith('folders'):
      delete_req = self._messages.EssentialcontactsFoldersContactsDeleteRequest(
          name=contact_name)
      return self._folders_service.Delete(delete_req)

    if contact_name.startswith('organizations'):
      delete_req = self._messages.EssentialcontactsOrganizationsContactsDeleteRequest(
          name=contact_name)
      return self._organizations_service.Delete(delete_req)

    delete_req = self._messages.EssentialcontactsProjectsContactsDeleteRequest(
        name=contact_name)
    return self._projects_service.Delete(delete_req)

  def Describe(self, contact_name):
    """Describes an Essential Contact.

    Args:
      contact_name: the full id of the contact to describe in the form of
        [projects|folders|organizations]/{resourceId}/contacts/{contactId}

    Returns:
      The requested contact.
    """
    if contact_name.startswith('folders'):
      describe_req = self._messages.EssentialcontactsFoldersContactsGetRequest(
          name=contact_name)
      return self._folders_service.Get(describe_req)

    if contact_name.startswith('organizations'):
      describe_req = self._messages.EssentialcontactsOrganizationsContactsGetRequest(
          name=contact_name)
      return self._organizations_service.Get(describe_req)

    describe_req = self._messages.EssentialcontactsProjectsContactsGetRequest(
        name=contact_name)
    return self._projects_service.Get(describe_req)

  def List(self, parent_name, page_size=50, limit=None):
    """Lists Essential Contacts set directly on a Cloud resource.

    Args:
      parent_name: the full name of the parent resource to list contacts for in
        the form of [projects|folders|organizations]/{resourceId}
      page_size: the number of contacts to return per page of the result list.
      limit: the total number of contacts to return.

    Returns:
      The contacts that have been set directly on the requested resource.
    """
    service = None
    list_req = None

    if parent_name.startswith('folders'):
      service = self._folders_service
      list_req = self._messages.EssentialcontactsFoldersContactsListRequest(
          parent=parent_name)
    elif parent_name.startswith('organizations'):
      service = self._organizations_service
      list_req = self._messages.EssentialcontactsOrganizationsContactsListRequest(
          parent=parent_name)
    else:
      service = self._projects_service
      list_req = self._messages.EssentialcontactsProjectsContactsListRequest(
          parent=parent_name)

    return list_pager.YieldFromList(
        service,
        list_req,
        batch_size=page_size,
        limit=limit,
        field='contacts',
        batch_size_attribute='pageSize')

  def Compute(self,
              parent_name,
              notification_categories,
              page_size=50,
              limit=None):
    """Computes the Essential Contacts for a Cloud resource.

    Args:
      parent_name: the full name of the parent resource to compute contacts for
        in the form of [projects|folders|organizations]/{resourceId}
      notification_categories: the notification categories (as choices) to
        retrieve subscribed contacts for.
      page_size: the number of contacts to return per page of the result list.
      limit: the total number of contacts to return.

    Returns:
      The contacts that have been computed from the resource hierarchy.
    """
    service = None
    compute_req = None

    if parent_name.startswith('folders'):
      service = self._folders_service
      compute_req = self._messages.EssentialcontactsFoldersContactsComputeRequest(
          parent=parent_name, notificationCategories=notification_categories)
    elif parent_name.startswith('organizations'):
      service = self._organizations_service
      compute_req = self._messages.EssentialcontactsOrganizationsContactsComputeRequest(
          parent=parent_name, notificationCategories=notification_categories)
    else:
      service = self._projects_service
      compute_req = self._messages.EssentialcontactsProjectsContactsComputeRequest(
          parent=parent_name, notificationCategories=notification_categories)

    return list_pager.YieldFromList(
        service,
        compute_req,
        batch_size=page_size,
        limit=limit,
        method='Compute',
        field='contacts',
        batch_size_attribute='pageSize')
