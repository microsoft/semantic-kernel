# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Move local source snapshots to GCP."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import os.path
import tarfile

from googlecloudsdk.api_lib.cloudbuild import metric_names
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core.util import files

_IGNORED_FILE_MESSAGE = """\
Some files were not included in the source upload.

Check the gcloud log [{log_file}] to see which files and the contents of the
default gcloudignore file used (see `$ gcloud topic gcloudignore` to learn
more).
"""


def _ResetOwnership(tarinfo):
  tarinfo.uid = tarinfo.gid = 0
  tarinfo.uname = tarinfo.gname = 'root'
  return tarinfo


class Snapshot(storage_util.Snapshot):
  """Snapshot is a manifest of the source in a directory.
  """

  def _MakeTarball(self, archive_path):
    """Constructs a tarball of snapshot contents.

    Args:
      archive_path: Path to place tar file.

    Returns:
      tarfile.TarFile, The constructed tar file.
    """
    tf = tarfile.open(archive_path, mode='w:gz')
    for dpath in self.dirs:
      t = tf.gettarinfo(dpath)
      if os.path.islink(dpath):
        t.type = tarfile.SYMTYPE
        t.linkname = os.readlink(dpath)
      elif os.path.isdir(dpath):
        t.type = tarfile.DIRTYPE
      else:
        log.debug(
            'Adding [%s] as dir; os.path says is neither a dir nor a link.',
            dpath)
        t.type = tarfile.DIRTYPE
      t.mode = os.stat(dpath).st_mode
      tf.addfile(_ResetOwnership(t))
      log.debug('Added dir [%s]', dpath)
    for path in self.files:
      tf.add(path, filter=_ResetOwnership)
      log.debug('Added [%s]', path)
    return tf

  def CopyTarballToGCS(self,
                       storage_client,
                       gcs_object,
                       ignore_file=None,
                       hide_logs=False):
    """Copy a tarball of the snapshot to GCS.

    Args:
      storage_client: storage_api.StorageClient, The storage client to use for
        uploading.
      gcs_object: storage.objects Resource, The GCS object to write.
      ignore_file: Override .gcloudignore file to specify skip files.
      hide_logs: boolean, not print the status message if the flag is true.

    Returns:
      storage_v1_messages.Object, The written GCS object.
    """
    with metrics.RecordDuration(metric_names.UPLOAD_SOURCE):
      with files.ChDir(self.src_dir):
        with files.TemporaryDirectory() as tmp:
          archive_path = os.path.join(tmp, 'file.tgz')
          tf = self._MakeTarball(archive_path)
          tf.close()
          ignore_file_path = os.path.join(
              self.src_dir, ignore_file or gcloudignore.IGNORE_FILE_NAME)
          if self.any_files_ignored:
            if os.path.exists(ignore_file_path):
              log.info('Using ignore file [{}]'.format(ignore_file_path))
            elif not hide_logs:
              log.status.Print(
                  _IGNORED_FILE_MESSAGE.format(log_file=log.GetLogFilePath()))
          if not hide_logs:
            log.status.write(
                'Uploading tarball of [{src_dir}] to '
                '[gs://{bucket}/{object}]\n'.format(
                    src_dir=self.src_dir,
                    bucket=gcs_object.bucket,
                    object=gcs_object.object,
                ),)
          return storage_client.CopyFileToGCS(archive_path, gcs_object)
