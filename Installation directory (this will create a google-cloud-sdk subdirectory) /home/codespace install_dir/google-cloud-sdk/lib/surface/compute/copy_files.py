# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Implements the command for copying files from and to virtual machines."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scp_utils
from googlecloudsdk.core import log

ENCOURAGE_SCP_INFO = (
    'Consider using the `gcloud compute scp` command instead, which '
    'includes support for internal IP connections and Identity-Aware '
    'Proxy tunneling.')


class CopyFiles(base.Command):
  """Copy files to and from Google Compute Engine virtual machines via scp."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    scp_utils.BaseScpHelper.Args(parser)

  def Run(self, args):
    """See scp_utils.BaseScpCommand.Run."""
    log.warning(ENCOURAGE_SCP_INFO)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    scp_helper = scp_utils.BaseScpHelper()
    return scp_helper.RunScp(holder, args, recursive=True,
                             release_track=self.ReleaseTrack())


# pylint:disable=line-too-long
CopyFiles.detailed_help = {
    'DESCRIPTION':
        """\
        *{command}* copies files between a virtual machine instance and your
        local machine using the scp command. This command does not work for
        Windows VMs.

        To denote a remote file, prefix the file name with the virtual machine
        instance name (e.g., _example-instance_:~/_FILE_). To denote a local
        file, do not add a prefix to the file name (e.g., ~/_FILE_).

        If a file contains a colon (``:''), you must specify it by either using
        an absolute path or a path that begins with
        ``./''.

        Under the covers, *scp(1)* or pscp (on Windows) is used to facilitate
        the transfer.

        When the destination is local, all sources must be the same virtual
        machine instance. When the destination is remote, all sources must be
        local.
        """,
    'EXAMPLES':
        """\
          To copy a remote directory '~/REMOTE-DIR' on the instance of
          'example-instance' to '~/LOCAL-DIR' on the local host, run:

            $ {command} example-instance:~/REMOTE-DIR ~/LOCAL-DIR --zone=us-central1-a

          To copy files from your local host to a virtual machine, run:

            $ {command} ~/LOCAL-FILE-1 ~/LOCAL-FILE-2 example-instance:~/REMOTE-DIR --zone=us-central1-a

        """
}
