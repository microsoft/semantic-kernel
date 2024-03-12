# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""The gcloud app group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'brief': 'Manage your App Engine deployments.',
    'DESCRIPTION': """
        The gcloud app command group lets you deploy and manage your Google App
        Engine apps. These commands replace their equivalents in the appcfg
        tool.

        App Engine is a platform for building scalable web applications
        and mobile backends. App Engine provides you with built-in services and
        APIs such as NoSQL datastores, memcache, and a user authentication API,
        common to most applications.

        More information on App Engine can be found here:
        https://cloud.google.com/appengine and detailed documentation can be
        found here: https://cloud.google.com/appengine/docs/
        """,
    'EXAMPLES': """\
        To run your app locally in the development application server
        to simulate your application running in production App Engine with
        sandbox restrictions and services provided by App Engine SDK libraries,
        use the `dev_appserver.py` command and your app's `app.yaml`
        configuration file to run:

          $ dev_appserver.py ~/my_app/app.yaml

        For an in-depth look into using the local development server, follow
        this guide : https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server

        To deploy the code and configuration of your app to the App Engine
        server, run:

          $ {command} deploy ~/my_app/app.yaml

        To list all versions of all services of your existing deployments, run:

          $ {command} versions list
       """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class AppengineGA(base.Group):
  """Manage your App Engine deployments."""

  category = base.COMPUTE_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190524958):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
    base.OptOutRequests()  # TODO(b/168048260): Remove to migrate to requests.

AppengineGA.detailed_help = DETAILED_HELP
