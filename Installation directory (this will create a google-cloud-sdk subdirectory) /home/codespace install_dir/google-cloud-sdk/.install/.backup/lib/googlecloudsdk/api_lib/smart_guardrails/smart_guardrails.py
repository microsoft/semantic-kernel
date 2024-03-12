# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Smart Guardrails Recommendation Utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.recommender import insight
from googlecloudsdk.command_lib.projects import util as project_util

_PROJECT_WARNING_MESSAGE = """Shutting down this project will immediately:
  - Stop all traffic and billing.
  - Start deleting resources.
  - Schedule the final deletion of the project after 30 days.
  - Block your access to the project.
  - Notify the owner of the project.

Learn more about the shutdown process at
https://cloud.google.com/resource-manager/docs/creating-managing-projects#shutting_down_projects
"""

_PROJECT_RISK_MESSAGE = (
    "*** HIGH-RISK CHANGE WARNING ***: If you shut down this project you risk "
    "losing data or interrupting your services"
)

_PROJECT_REASONS_PREFIX = ". In the last 30 days we observed this project had"

_PROJECT_ADVICE = (
    "We recommend verifying this is the correct project to shut down.\n"
)

_SA_DELETE_APP_ENGINE_WARNING_MESSAGE = (
    "This service account lets App Engine and Cloud Functions access essential"
    " Cloud Platform services such as Datastore. Deleting this account will "
    "break any current or future App Engine applications and Cloud Functions "
    "in this project.\n\n"
    "WARNING: You CANNOT  undo this action. "
    "Do not delete this service account unless you are sure you"
    " will never use App Engine in this project."
)

_SA_DELETE_COMPUTE_ENGINE_WARNING_MESSAGE = (
    "This service account lets Compute Engine access essential Cloud Platform "
    "services such as logging and Cloud Storage. Deleting this account will "
    "prevent instances that are running as this account from accessing "
    "Cloud Platform services.\n\n"
    "WARNING: You CANNOT undo this action. "
    "If you delete this account, instances in this project will only be able "
    "to access Cloud Platform services via custom service accounts."
)

_SA_WARNING_MESSAGE = (
    "Deleting this service account (SA) will delete "
    "all associated key IDs, and will prevent the account from authenticating"
    " to any Google Cloud service API.\n\n"
    "You cannot restore or roll back this change easily. We highly recommend"
    " disabling the account first, testing for any unexpected impact, and only"
    " then deleting.\n"
)

_SA_RISK_MESSAGE = (
    "*** HIGH-RISK CHANGE WARNING ***: If you delete this SA you risk "
    "interrupting your service, as we observed it was substantially used in "
    "the last 90 days"
)

_SA_ADVICE = "We recommend verifying this is the correct account to delete.\n"

_POLICY_BINDING_DELETE_WARNING_MESSAGE = (
    "You are about to delete the role [{}].\n"
)

_POLICY_BINDING_DELETE_RISK_MESSAGE = (
    "*** HIGH-RISK CHANGE WARNING ***: If you remove the role [{}], there is "
    "a high risk that you might cause interruptions because it was used "
    "in the last 90 days"
)

_POLICY_BINDING_DELETE_ADVICE = (
    "We recommend you verify the details and replace them with less privileged"
    " roles, if necessary.\n"
)

_POLICY_BINDING_REPLACE_ADVICE = (
    "We recommend replacing it with the role{} [{}], in order to remove "
    "unused permissions while preserving the used one.\n"
)

_PROJECT_INSIGHT_TYPE = "google.resourcemanager.project.ChangeRiskInsight"

_SA_INSIGHT_TYPE = "google.iam.serviceAccount.ChangeRiskInsight"

_POLICY_BINDING_INSIGHT_TYPE = "google.iam.policy.ChangeRiskInsight"

_RECOMMENDATIONS_HOME_URL = (
    "https://console.cloud.google.com/home/recommendations"
)

_MAX_NUMBER_OF_REASONS = 3


def _GetIamPolicyBindingMatcher(member, role):
  """Returns a function that matches an insight by policy binding.

  Args:
    member: Member string to fully match.
    role: Member role to fully match.

  Returns:
    A function that matches an insight object by policy binding. The returned
    function returns true iff both the member and the role match.
  """

  def Matcher(gcloud_insight):
    matches_member = False
    matches_role = False
    for additional_property in gcloud_insight.content.additionalProperties:
      if additional_property.key == "risk":
        for p in additional_property.value.object_value.properties:
          if p.key == "usageAtRisk":
            for f in p.value.object_value.properties:
              if f.key == "iamPolicyUtilization":
                for iam_p in f.value.object_value.properties:
                  if iam_p.key == "member":
                    if iam_p.value.string_value == member:
                      matches_member = True
                  if iam_p.key == "role":
                    if iam_p.value.string_value == role:
                      matches_role = True
    return matches_member and matches_role

  return Matcher


def _GetInsightLink(gcloud_insight):
  """Returns a message with a link to the associated recommendation.

  Args:
    gcloud_insight: Insight object returned by the recommender API.

  Returns:
    A string message with a link to the associated recommendation.
  """
  return ("View the full risk assessment at: {0}/view-link/{1}").format(
      _RECOMMENDATIONS_HOME_URL, gcloud_insight.name
  )


def _GetResourceRiskReasons(gcloud_insight):
  """Extracts a list of string reasons from the resource change insight.

  Args:
    gcloud_insight: Insight object returned by the recommender API.

  Returns:
    A list of strings. If no reasons could be found, then returns empty list.
    The number of reasons is limited by _MAX_NUMBER_OF_REASONS, and the last
    reason indicates how many more reasons there are if applicable.
  """
  reasons = []
  num_reasons = 0
  last_reason = ""
  for additional_property in gcloud_insight.content.additionalProperties:
    if additional_property.key == "importance":
      for p in additional_property.value.object_value.properties:
        if p.key == "detailedReasons":
          for reason in p.value.array_value.entries:
            num_reasons += 1
            if num_reasons < _MAX_NUMBER_OF_REASONS:
              reasons.append(reason.string_value)
            elif num_reasons == _MAX_NUMBER_OF_REASONS:
              last_reason = reason.string_value
  if num_reasons > _MAX_NUMBER_OF_REASONS:
    last_reason = "{} other importance indicators.".format(
        num_reasons - _MAX_NUMBER_OF_REASONS + 1
    )
  if num_reasons >= _MAX_NUMBER_OF_REASONS:
    reasons.append(last_reason)
  return reasons


def _GetDeletionRiskMessage(
    gcloud_insight, risk_message, reasons_prefix="", add_new_line=True
):
  """Returns a risk message for resource deletion.

  Args:
    gcloud_insight: Insight object returned by the recommender API.
    risk_message: String risk message.
    reasons_prefix: String prefix before listing reasons.
    add_new_line: Bool for if a new line is added when no reasons are present.

  Returns:
    Formatted string risk message with reasons if any. The reasons are
    extracted from the gcloud_insight object.
  """
  reasons = _GetResourceRiskReasons(gcloud_insight)
  if not reasons:
    return "{}.{}".format(risk_message, "\n" if add_new_line else "")
  if len(reasons) == 1:
    return "{0}{1} {2}\n".format(risk_message, reasons_prefix, reasons[0])
  message = "{0}{1}:\n".format(risk_message, reasons_prefix)
  message += "".join("  - {0}\n".format(reason) for reason in reasons)
  return message


def _GetRiskInsight(
    release_track, project_id, insight_type, request_filter=None, matcher=None
):
  """Returns the first insight fetched by the recommender API.

  Args:
    release_track: Release track of the recommender.
    project_id: Project ID.
    insight_type: String insight type.
    request_filter: Optional string filter for the recommender.
    matcher: Matcher for the insight object. None means match all.

  Returns:
    Insight object returned by the recommender API. Returns 'None' if no
    matching insights were found. Returns the first insight object that matches
    the matcher. If no matcher, returns the first insight object fetched.
  """
  client = insight.CreateClient(release_track)
  parent_name = ("projects/{0}/locations/global/insightTypes/{1}").format(
      project_id, insight_type
  )
  result = client.List(
      parent_name, page_size=100, limit=None, request_filter=request_filter
  )
  for r in result:
    if not matcher:
      return r
    if matcher(r):
      return r
  return None


def _IsDefaultAppEngineServiceAccount(email):
  """Returns true if email is used as a default App Engine Service Account.

  Args:
    email: Service Account email.

  Returns:
    Returns true if the given email is default App Engine Service Account.
    Returns false otherwise.
  """
  return re.search(
      r"^([\w:.-]+)@appspot(\.[^.]+\.iam)?\.gserviceaccount\.com", email
  )


def _IsDefaultComputeEngineServiceAccount(email, project_number):
  """Returns true if email is used as a default Compute Engine Service Account.

  Args:
    email: Service Account email.
    project_number: Project number.

  Returns:
    Returns true if the given email is a default Compue Engine Service Account.
    Returns false otherwise.
  """
  if email == "{0}@developer.gserviceaccount.com".format(project_number):
    return True
  if email == "{0}@project.gserviceaccount.com".format(project_number):
    return True
  return re.search(
      r"^[0-9]+-compute@developer(\.[^.]+\.iam)?\.gserviceaccount\.com", email
  )


def _GetPolicyBindingMinimalRoles(gcloud_insight):
  """Returns minimal roles extracted from the IAM policy binding insight.

  Args:
    gcloud_insight: Insight returned by the recommender API.

  Returns: A list of strings. Empty if no minimal roles were found.
  """
  minimal_roles = []
  for additional_property in gcloud_insight.content.additionalProperties:
    if additional_property.key == "risk":
      for p in additional_property.value.object_value.properties:
        if p.key == "usageAtRisk":
          for f in p.value.object_value.properties:
            if f.key == "iamPolicyUtilization":
              for iam_p in f.value.object_value.properties:
                if iam_p.key == "minimalRoles":
                  for role in iam_p.value.array_value.entries:
                    minimal_roles.append(role.string_value)
  return minimal_roles


def _GetPolicyBindingDeletionAdvice(minimal_roles):
  """Returns advice for policy binding deletion.

  Args:
    minimal_roles: A string list of minimal recommended roles.

  Returns: A string advice on safe deletion.
  """
  if minimal_roles:
    return _POLICY_BINDING_REPLACE_ADVICE.format(
        "" if len(minimal_roles) <= 1 else "s", ", ".join(minimal_roles)
    )
  else:
    return _POLICY_BINDING_DELETE_ADVICE


def GetProjectDeletionRisk(release_track, project_id):
  """Returns a risk assesment message for project deletion.

  Args:
    release_track: Release track of the recommender.
    project_id: Project ID.

  Returns:
    String message prompt to be displayed for project deletion.
    If the project deletion is high risk, the message includes the
    Active Assist warning.
  """
  risk_insight = _GetRiskInsight(
      release_track, project_id, _PROJECT_INSIGHT_TYPE
  )
  if risk_insight:
    return "\n".join([
        _PROJECT_WARNING_MESSAGE,
        _GetDeletionRiskMessage(
            gcloud_insight=risk_insight,
            risk_message=_PROJECT_RISK_MESSAGE,
            reasons_prefix=_PROJECT_REASONS_PREFIX,
        ),
        _PROJECT_ADVICE,
        _GetInsightLink(risk_insight),
    ])
  # If there are no risks to deleting a project,
  # return a standard warning message.
  return _PROJECT_WARNING_MESSAGE


def GetServiceAccountDeletionRisk(release_track, project_id, service_account):
  """Returns a risk assesment message for service account deletion.

  Args:
    release_track: Release track of the recommender.
    project_id: String project ID.
    service_account: Service Account email ID.

  Returns:
    String Active Assist risk warning message to be displayed in
    service account deletion prompt.
  """
  project_number = project_util.GetProjectNumber(project_id)
  # If special default App Engine SA, return a special warning.
  if _IsDefaultAppEngineServiceAccount(service_account):
    return _SA_DELETE_APP_ENGINE_WARNING_MESSAGE
  # If special default Compute Engine SA, return a special warning.
  if _IsDefaultComputeEngineServiceAccount(service_account, project_number):
    return _SA_DELETE_COMPUTE_ENGINE_WARNING_MESSAGE
  target_filter = (
      "targetResources: //iam.googleapis.com/projects/{0}/serviceAccounts/{1}"
  ).format(project_number, service_account)
  risk_insight = _GetRiskInsight(
      release_track, project_id, _SA_INSIGHT_TYPE, request_filter=target_filter
  )
  if risk_insight:
    return "\n".join([
        _SA_WARNING_MESSAGE,
        _GetDeletionRiskMessage(risk_insight, _SA_RISK_MESSAGE),
        _SA_ADVICE,
        _GetInsightLink(risk_insight),
    ])
  # If there are no risks to deleting a service account,
  # return a standard warning message.
  return _SA_WARNING_MESSAGE


def GetIamPolicyBindingDeletionRisk(
    release_track, project_id, member, member_role
):
  """Returns a risk assesment message for IAM policy binding deletion.

  Args:
    release_track: Release track of the recommender.
    project_id: String project ID.
    member: IAM policy binding member.
    member_role: IAM policy binding member role.

  Returns:
    String Active Assist risk warning message to be displayed in IAM policy
    binding deletion prompt.
    If no risk exists, then returns 'None'.
  """
  # Remove prefixes like "user:", "group:", etc. from member
  # because the recommender generates a member id only.
  member = member[(member.find(":") + 1) :]
  policy_matcher = _GetIamPolicyBindingMatcher(member, member_role)
  risk_insight = _GetRiskInsight(
      release_track,
      project_id,
      _POLICY_BINDING_INSIGHT_TYPE,
      matcher=policy_matcher,
  )
  if risk_insight:
    risk_message = "{} {}".format(
        _GetDeletionRiskMessage(
            risk_insight,
            _POLICY_BINDING_DELETE_RISK_MESSAGE.format(member_role),
            add_new_line=False,
        ),
        _GetPolicyBindingDeletionAdvice(
            _GetPolicyBindingMinimalRoles(risk_insight)
        ),
    )
    return "\n".join([
        _POLICY_BINDING_DELETE_WARNING_MESSAGE.format(member_role),
        risk_message,
        _GetInsightLink(risk_insight),
    ])
  # If there are no risks to deleting the IAM policy binding,
  # return a standard warning message.
  return _POLICY_BINDING_DELETE_WARNING_MESSAGE.format(member_role)
