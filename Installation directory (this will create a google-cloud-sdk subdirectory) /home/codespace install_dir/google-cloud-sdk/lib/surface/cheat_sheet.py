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
"""A command that prints the gcloud cheat sheet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Cheatsheet(base.TopicCommand):
  """Display gcloud cheat sheet.

  A roster of go-to `gcloud` commands for the gcloud tool, Google Cloud's
  primary command-line tool.

  ### Getting started
  Get going with the `gcloud` command-line tool

  * `gcloud init`: Initialize, authorize, and configure the `gcloud` tool.
  * `gcloud version`: Display version and installed components.
  * `gcloud components install`: Install specific components.
  * `gcloud components update`: Update your Google Cloud CLI to the latest
     version.
  * `gcloud config set` `project`: Set a default Google Cloud project to
                                   work on.
  * `gcloud info`: Display current `gcloud` tool environment details.

  ### Help
  Google Cloud CLI is happy to help

  * `gcloud help`: Search the `gcloud` tool reference documents for specific
    terms.
  * `gcloud feedback`: Provide feedback for the Google Cloud CLI team.
  * `gcloud topic`: Supplementary help material for non-command topics like
    accessibility, filtering, and formatting.

  ### Personalization
  Make the Google Cloud CLI your own; personalize your configuration with
  properties

  * `gcloud config set`: Define a property (like compute/zone) for the current
    configuration.
  * `gcloud config get`: Fetch value of a Google Cloud CLI property.
  * `gcloud config list`: Display all the properties for the current
    configuration.
  * `gcloud config configurations create`: Create a new named configuration.
  * `gcloud config configurations list`: Display a list of all available
    configurations.
  * `gcloud config configurations activate`: Switch to an existing named
    configuration.

  ### Credentials
  Grant and revoke authorization to Google Cloud CLI

  * `gcloud auth login`: Authorize Google Cloud access for the `gcloud` tool
    with Google user credentials and set current account as active.
  * `gcloud auth activate-service-account`: Like `gcloud auth login` but with
    service account credentials.
  * `gcloud auth list`: List all credentialed accounts.
  * `gcloud auth print-access-token`: Display the current account's access
    token.
  * `gcloud auth revoke`: Remove access credentials for an account.

  ### Projects
  Manage project access policies

  * `gcloud projects describe`: Display metadata for a project
    (including its ID).
  * `gcloud projects add-iam-policy-binding`: Add an IAM policy binding to a
    specified project.

  ### Identity & Access Management
  Configuring Cloud Identity & Access Management (IAM) preferences and service
  accounts

  * `gcloud iam list-grantable-roles`: List IAM grantable roles for a resource.
  * `gcloud iam roles create`: Create a custom role for a project or org.
  * `gcloud iam service-accounts create`: Create a service account for
    a project.
  * `gcloud iam service-accounts add-iam-policy-binding`: Add an IAM policy
    binding to a service account.
  * `gcloud iam service-accounts set-iam-policy`: Replace existing IAM
    policy binding.
  * `gcloud iam service-accounts keys list`: List a service account's keys.

  ### Docker & Google Kubernetes Engine (GKE)
  Manage containerized applications on Kubernetes

  * `gcloud auth configure-docker`: Register the `gcloud` tool as a Docker
    credential helper.
  * `gcloud container clusters create`: Create a cluster to run GKE containers.
  * `gcloud container clusters list`: List clusters for running GKE containers.
  * `gcloud container clusters get-credentials`: Update `kubeconfig` to get
    `kubectl` to use a GKE cluster.
  * `gcloud container images list-tags`: List tag and digest metadata for a
    container image.

  ### Virtual Machines & Compute Engine
  Create, run, and manage VMs on Google infrastructure

  * `gcloud compute zones list`: List Compute Engine zones.
  * `gcloud compute instances describe`: Display a VM instance's details.
  * `gcloud compute instances list`: List all VM instances in a project.
  * `gcloud compute disks snapshot`: Create snapshot of persistent disks.
  * `gcloud compute snapshots describe`: Display a snapshot's details.
  * `gcloud compute snapshots delete`: Delete a snapshot.
  * `gcloud compute ssh`: Connect to a VM instance by using SSH.

  ### Serverless & App Engine
  Build highly scalable applications on a fully managed serverless platform

  * `gcloud app deploy`: Deploy your app's code and configuration to the
    App Engine server.
  * `gcloud app versions list`: List all versions of all services deployed to
    the App Engine server.
  * `gcloud app browse`: Open the current app in a web browser.
  * `gcloud app create`: Create an App Engine app within your current project.
  * `gcloud app logs read`: Display the latest App Engine app logs.

  ### Miscellaneous
  Commands that might come in handy

  * `gcloud kms decrypt`: Decrypt ciphertext (to a plaintext file) using a Cloud
    Key Management Service (Cloud KMS) key.
  * `gcloud logging logs list`: List your project's logs.
  * `gcloud sql backups describe`: Display info about a Cloud SQL instance
    backup.
  * `gcloud sql export sql`: Export data from a Cloud SQL instance to a
    SQL file.

  ## EXAMPLES

   To view this cheat sheet, run:

     $ {command}
  """
