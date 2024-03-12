# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""The gen-config command."""
# TODO(b/172812887) - Delete this command entirely; it's PY2 only.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import shutil
import tempfile

from gae_ext_runtime import ext_runtime

from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import deployables
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

from googlecloudsdk.third_party.appengine.api import appinfo

from ruamel import yaml
import six


_DEPRECATION_MSG = """\
This command is deprecated and will soon be removed.

{fingerprinting}

To create a custom runtime, please follow the instructions at
https://cloud.google.com/appengine/docs/flexible/custom-runtimes/
""".format(fingerprinting=deployables.FINGERPRINTING_WARNING)


# TODO(b/28509217): Move back into command class when `preview` is gone.
def _Args(parser):
  """Add arguments for `gcloud app gen-config`."""
  parser.add_argument(
      'source_dir',
      nargs='?',
      help='The source directory to fingerprint.',
      default=files.GetCWD())
  parser.add_argument(
      '--config',
      default=None,
      help=('The yaml file defining the service configuration.  This is '
            'normally one of the generated files, but when generating a '
            'custom runtime there can be an app.yaml containing parameters.'))

  rt_list = [r for r in appinfo.GetAllRuntimes() if r not in ['vm', 'custom']]
  parser.add_argument(
      '--runtime',
      default=None,
      help=('Generate config files for a given runtime. Can be used in '
            'conjunction with --custom. Allowed runtimes are: ' +
            ', '.join(rt_list) + '.'))
  parser.add_argument(
      '--custom',
      action='store_true',
      default=False,
      help=('If true, generate config files for a custom runtime.  This '
            'will produce a Dockerfile, a .dockerignore file and an app.yaml '
            '(possibly other files as well, depending on the runtime).'))


def _Run(args):
  """Run the `gcloud app gen-config` command."""
  if args.config:
    # If the user has specified an config file, use that.
    config_filename = args.config
  else:
    # Otherwise, check for an app.yaml in the source directory.
    config_filename = os.path.join(args.source_dir, 'app.yaml')
    if not os.path.exists(config_filename):
      config_filename = None

  # If there was an config file either specified by the user or in the source
  # directory, load it.
  if config_filename:
    try:
      myi = yaml_parsing.ServiceYamlInfo.FromFile(config_filename)
      config = myi.parsed
    except IOError as ex:
      log.error('Unable to open %s: %s', config_filename, ex)
      return
  else:
    config = None

  fingerprinter.GenerateConfigs(
      args.source_dir,
      ext_runtime.Params(appinfo=config, custom=args.custom,
                         runtime=args.runtime),
      config_filename)

  # If the user has a config file, make sure that they're using a custom
  # runtime.
  if config and args.custom and config.GetEffectiveRuntime() != 'custom':
    alter = console_io.PromptContinue(
        default=False,
        message=output_helpers.RUNTIME_MISMATCH_MSG.format(config_filename),
        prompt_string='Would you like to update it now?')
    if alter:
      _AlterRuntime(config_filename, 'custom')
      log.status.Print('[{0}] has been updated.'.format(config_filename))
    else:
      log.status.Print('Please update [{0}] manually by changing the runtime '
                       'field to custom.'.format(config_filename))


@base.Deprecate(is_removed=False, warning=_DEPRECATION_MSG)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class GenConfig(base.Command):
  """Generate missing configuration files for a source directory."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    if six.PY3:
      raise exceptions.NotSupportedPy3Exception(
          'This command does not support python3.')
    _Run(args)


def _AlterRuntime(config_filename, runtime):
  try:
    # 0. Take backup
    with tempfile.NamedTemporaryFile(prefix='app.yaml.') as f:
      backup_fname = f.name
    log.status.Print(
        'Copying original config [{0}] to backup location [{1}].'.format(
            config_filename, backup_fname))
    shutil.copyfile(config_filename, backup_fname)
    # 1. Open and parse file using ruamel
    with files.FileReader(config_filename) as yaml_file:
      encoding = yaml_file.encoding
      config = yaml.load(yaml_file, yaml.RoundTripLoader)
    # 2. Alter the ruamel in-memory object representing the yaml file
    config['runtime'] = runtime
    # 3. Create an in-memory file buffer and write yaml file to it
    raw_buf = io.BytesIO()
    tmp_yaml_buf = io.TextIOWrapper(raw_buf, encoding)
    yaml.dump(config, tmp_yaml_buf, Dumper=yaml.RoundTripDumper)
    # 4. Overwrite the original app.yaml
    with files.BinaryFileWriter(config_filename) as yaml_file:
      tmp_yaml_buf.seek(0)
      yaml_file.write(raw_buf.getvalue())
  except Exception as e:
    raise fingerprinter.AlterConfigFileError(e)

_DETAILED_HELP = {
    'DESCRIPTION': """\
    This command generates all relevant config files (app.yaml, Dockerfile and a
    build Dockerfile) for your application in the current directory or emits an
    error message if the source directory contents are not recognized.
    """,
    'EXAMPLES': """\
    To generate configs for the current directory:

      $ {command}

    To generate configs for ~/my_app:

      $ {command} ~/my_app
    """
}

GenConfig.detailed_help = _DETAILED_HELP
