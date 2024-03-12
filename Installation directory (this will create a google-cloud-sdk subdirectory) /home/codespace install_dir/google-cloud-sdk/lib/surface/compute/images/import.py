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
"""Import image command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import enum
import os.path
import string
import uuid

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.images import flags
from googlecloudsdk.command_lib.compute.images import os_choices
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
import six

_WORKFLOWS_URL = ('https://github.com/GoogleCloudPlatform/compute-image-import/'
                  'tree/main/daisy_workflows/image_import')
_OUTPUT_FILTER = [
    '[Daisy', '[import-', '[onestep-', 'starting build', '  import', 'ERROR'
]


class CloudProvider(enum.Enum):
  UNKNOWN = 0
  AWS = 1


def _HasAwsArgs(args):
  return (args.aws_access_key_id or args.aws_secret_access_key or
          args.aws_session_token or args.aws_region or args.aws_ami_id or
          args.aws_ami_export_location or args.aws_source_ami_file_path)


def _HasExternalCloudProvider(args):
  return _GetExternalCloudProvider(args) != CloudProvider.UNKNOWN


def _GetExternalCloudProvider(args):
  if _HasAwsArgs(args):
    return CloudProvider.AWS
  return CloudProvider.UNKNOWN


def _AppendTranslateWorkflowArg(args, import_args):
  if args.os:
    daisy_utils.AppendArg(import_args, 'os', args.os)
  daisy_utils.AppendArg(import_args, 'custom_translate_workflow',
                        args.custom_workflow)


def _AppendAwsArgs(args, import_args):
  """Appends args related to AWS image import."""

  daisy_utils.AppendArg(import_args, 'aws_access_key_id',
                        args.aws_access_key_id)
  daisy_utils.AppendArg(import_args, 'aws_secret_access_key',
                        args.aws_secret_access_key)
  daisy_utils.AppendArg(import_args, 'aws_session_token',
                        args.aws_session_token)
  daisy_utils.AppendArg(import_args, 'aws_region', args.aws_region)

  if args.aws_ami_id:
    daisy_utils.AppendArg(import_args, 'aws_ami_id', args.aws_ami_id)
  if args.aws_ami_export_location:
    daisy_utils.AppendArg(import_args, 'aws_ami_export_location',
                          args.aws_ami_export_location)
  if args.aws_source_ami_file_path:
    daisy_utils.AppendArg(import_args, 'aws_source_ami_file_path',
                          args.aws_source_ami_file_path)


def _CheckImageName(image_name):
  """Checks for a valid GCE image name."""
  name_message = ('Name must start with a lowercase letter followed by up to '
                  '63 lowercase letters, numbers, or hyphens, and cannot end '
                  'with a hyphen.')
  name_ok = True
  valid_chars = string.digits + string.ascii_lowercase + '-'
  if len(image_name) > 64:
    name_ok = False
  elif image_name[0] not in string.ascii_lowercase:
    name_ok = False
  elif not all(char in valid_chars for char in image_name):
    name_ok = False
  elif image_name[-1] == '-':
    name_ok = False

  if not name_ok:
    raise exceptions.InvalidArgumentException('IMAGE_NAME', name_message)


def _CheckForExistingImage(image_name,
                           compute_holder,
                           arg_name='IMAGE_NAME',
                           expect_to_exist=False):
  """Check if image already exists."""

  # Don't perform a check for image name used in E2E test as passing an invalid
  # name to the backend is currently the only way to perform a quick sanity E2E
  # check on the backend. Alternative is not to perform the check on whether
  # image exists at all which would lead to worse customer experience. No
  # security issue with this as the backend does the same check on whether an
  # image exists or not.
  expect_to_exist_image_name_exclusions = ['sample-image-123']
  if expect_to_exist and image_name in expect_to_exist_image_name_exclusions:
    return

  image_ref = resources.REGISTRY.Parse(
      image_name,
      collection='compute.images',
      params={'project': properties.VALUES.core.project.GetOrFail})

  image_expander = image_utils.ImageExpander(compute_holder.client,
                                             compute_holder.resources)
  try:
    _ = image_expander.GetImage(image_ref)
    image_exists = True
  except utils.ImageNotFoundError:
    image_exists = False

  if not expect_to_exist and image_exists:
    message = 'The image [{0}] already exists.'.format(image_name)
    raise exceptions.InvalidArgumentException(arg_name, message)
  elif expect_to_exist and not image_exists:
    message = 'The image [{0}] does not exist.'.format(image_name)
    raise exceptions.InvalidArgumentException(arg_name, message)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Import(base.CreateCommand):
  """Import an image into Compute Engine."""

  _OS_CHOICES = os_choices.OS_CHOICES_IMAGE_IMPORT_GA

  def __init__(self, *args, **kwargs):
    self.storage_client = storage_api.StorageClient()
    super(Import, self).__init__(*args, **kwargs)

  @classmethod
  def Args(cls, parser):
    compute_holder = cls._GetComputeApiHolder(no_http=True)
    compute_client = compute_holder.client
    messages = compute_client.messages

    Import.DISK_IMAGE_ARG = flags.MakeDiskImageArg()
    Import.DISK_IMAGE_ARG.AddArgument(parser, operation_type='create')

    flags.compute_flags.AddZoneFlag(
        parser,
        'image',
        'import',
        help_text='Zone to use when importing the image. When you import '
        'an image, the import tool creates and uses temporary VMs '
        'in your project for the import process. Use this flag to '
        'specify the zone to use for these temporary VMs.')

    source = parser.add_mutually_exclusive_group(required=True, sort_args=False)

    import_from_local_or_gcs = source.add_mutually_exclusive_group(
        help='Image import from local file, Cloud Storage or '
        'Compute Engine image.'
    )
    import_from_local_or_gcs.add_argument(
        '--source-file',
        help=("""A local file, or the Cloud Storage URI of the virtual
              disk file to import. For example: ``gs://my-bucket/my-image.vmdk''
              or ``./my-local-image.vmdk''. For more information about Cloud
            Storage URIs, see
            https://cloud.google.com/storage/docs/request-endpoints#json-api.
            """),
    )
    flags.SOURCE_IMAGE_ARG.AddArgument(
        import_from_local_or_gcs, operation_type='import')

    import_from_aws = source.add_group(help='Image import from AWS.')
    daisy_utils.AddAWSImageImportSourceArgs(import_from_aws)

    image_utils.AddGuestOsFeaturesArgForImport(parser, messages)

    workflow = parser.add_mutually_exclusive_group()
    os_group = workflow.add_group()
    daisy_utils.AddByolArg(os_group)
    os_group.add_argument(
        '--os',
        choices=sorted(cls._OS_CHOICES),
        help='Specifies the OS of the disk image being imported.')

    workflow.add_argument(
        '--data-disk',
        help=('Specifies that the disk has no bootable OS installed on it. '
              'Imports the disk without making it bootable or installing '
              'Google tools on it.'),
        action='store_true')
    workflow.add_argument(
        '--custom-workflow',
        help=("""\
              Specifies a custom workflow to use for image translation. Workflow
              should be relative to the image_import directory here: []({0}).
              For example: `debian/translate_debian_9.wf.json'""".format(
                  _WORKFLOWS_URL)),
        hidden=True)

    daisy_utils.AddCommonDaisyArgs(
        parser,
        operation='an import',
        extra_timeout_help=("""

          If you are importing a large image that takes longer than 24 hours to
          import, either use the RAW disk format to reduce the time needed for
          converting the image, or split the data into several smaller images.
          """))

    parser.add_argument(
        '--guest-environment',
        action='store_true',
        default=True,
        help='Installs the guest environment on the image.'
        ' See '
        'https://cloud.google.com/compute/docs/images/guest-environment.')

    parser.add_argument(
        '--network',
        help=(
            'Name of the network in your project to use for the image '
            'import. When you import an image, the import tool creates and '
            'uses temporary VMs in your project for the import process. Use '
            'this flag to specify the network to use for these temporary VMs.'),
    )

    parser.add_argument(
        '--subnet',
        help=("""\
      Name of the subnetwork in your project to use for the image import. When
      you import an image, the import tool creates and uses temporary VMs in
      your project for the import process. Use this flag to specify the
      subnetwork to use for these temporary VMs.
          * If the network resource is in legacy mode, do not provide this
            property.
          * If the network is in auto subnet mode, specifying the subnetwork is
            optional.
          * If the network is in custom subnet mode, then this field must be
            specified.
        """),
    )

    parser.add_argument(
        '--family', help='Family to set for the imported image.')

    parser.add_argument(
        '--description', help='Description to set for the imported image.')

    parser.display_info.AddCacheUpdater(flags.ImagesCompleter)

    parser.add_argument(
        '--storage-location',
        help="""\
      Specifies a Cloud Storage location, either regional or multi-regional,
      where image content is to be stored. If not specified, the multi-region
      location closest to the source is chosen automatically.
      """)

    parser.add_argument(
        '--sysprep-windows',
        action='store_true',
        hidden=True,
        help='Whether to generalize the image using Windows Sysprep.')

    daisy_utils.AddNoAddressArg(
        parser, 'image import',
        'https://cloud.google.com/compute/docs/import/importing-virtual-disks#no-external-ip'
    )

    daisy_utils.AddComputeServiceAccountArg(
        parser, 'image import',
        daisy_utils.IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)

    daisy_utils.AddCloudBuildServiceAccountArg(
        parser,
        'image import',
        daisy_utils.IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
    )

  @classmethod
  def _GetComputeApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    compute_holder = self._GetComputeApiHolder()

    # Fail early if the requested image name is invalid or already exists.
    _CheckImageName(args.image_name)
    _CheckForExistingImage(args.image_name, compute_holder)

    stager = self._CreateImportStager(args, compute_holder)
    import_metadata = stager.Stage()

    log.warning('Importing image. This may take up to 2 hours.')

    tags = ['gce-daisy-image-import']

    return self._RunImageImport(args, import_metadata, tags, _OUTPUT_FILTER)

  def _RunImageImport(self, args, import_args, tags, output_filter):
    image_tag = daisy_utils.GetDefaultBuilderVersion()
    if hasattr(args, 'docker_image_tag'):
      image_tag = args.docker_image_tag

    if _HasExternalCloudProvider(args):
      return daisy_utils.RunOnestepImageImport(
          args,
          import_args,
          tags,
          _OUTPUT_FILTER,
          release_track=self.ReleaseTrack().id.lower()
          if self.ReleaseTrack() else None,
          docker_image_tag=image_tag)
    return daisy_utils.RunImageImport(
        args,
        import_args,
        tags,
        _OUTPUT_FILTER,
        release_track=self.ReleaseTrack().id.lower()
        if self.ReleaseTrack() else None,
        docker_image_tag=image_tag)

  def _CreateImportStager(self, args, compute_holder):
    if _HasExternalCloudProvider(args):
      return ImportFromExternalCloudProviderStager(self.storage_client,
                                                   compute_holder, args)

    if args.source_image:
      return ImportFromImageStager(self.storage_client, compute_holder, args)

    if daisy_utils.IsLocalFile(args.source_file):
      return ImportFromLocalFileStager(self.storage_client, compute_holder,
                                       args)

    try:
      gcs_uri = daisy_utils.MakeGcsObjectUri(args.source_file)
    except storage_util.InvalidObjectNameError:
      raise exceptions.InvalidArgumentException(
          'source-file', 'must be a path to an object in Google Cloud Storage')
    else:
      return ImportFromGSFileStager(self.storage_client, compute_holder, args,
                                    gcs_uri)


@six.add_metaclass(abc.ABCMeta)
class BaseImportStager(object):
  """Base class for image import stager.

  An abstract class which is responsible for preparing import parameters, such
  as Daisy parameters and workflow, as well as creating Daisy scratch bucket in
  the appropriate location.
  """

  def __init__(self, storage_client, compute_holder, args):
    self.storage_client = storage_client
    self.compute_holder = compute_holder
    self.args = args
    self.daisy_bucket = self.GetAndCreateDaisyBucket()

  def Stage(self):
    """Prepares for import args.

    It supports running new import wrapper (gce_vm_image_import).

    Returns:
      import_args - array of strings, import args.
    """
    import_args = []
    messages = self.compute_holder.client.messages

    daisy_utils.AppendArg(import_args, 'zone',
                          properties.VALUES.compute.zone.Get())
    if self.args.storage_location:
      daisy_utils.AppendArg(import_args, 'storage_location',
                            self.args.storage_location)
    daisy_utils.AppendArg(import_args, 'scratch_bucket_gcs_path',
                          'gs://{0}/'.format(self.daisy_bucket))
    daisy_utils.AppendArg(import_args, 'timeout',
                          '{}s'.format(daisy_utils.GetDaisyTimeout(self.args)))

    daisy_utils.AppendArg(import_args, 'client_id', 'gcloud')
    daisy_utils.AppendArg(import_args, 'image_name', self.args.image_name)
    daisy_utils.AppendBoolArg(import_args, 'no_guest_environment',
                              not self.args.guest_environment)
    daisy_utils.AppendNetworkAndSubnetArgs(self.args, import_args)
    daisy_utils.AppendArg(import_args, 'description', self.args.description)
    daisy_utils.AppendArg(import_args, 'family', self.args.family)
    if 'byol' in self.args:
      daisy_utils.AppendBoolArg(import_args, 'byol', self.args.byol)

    # The value of the attribute 'guest_os_features' can be can be a list, None,
    # or the attribute may not be present at all.
    # We treat the case when it is None or when it is not present as if the list
    # of features is empty. We need to use the trailing `or ()` rather than
    # give () as a default value to getattr() to handle the case where
    # args.guest_os_features is present, but it is None.
    guest_os_features = getattr(self.args, 'guest_os_features', None) or ()
    uefi_compatible = (
        messages.GuestOsFeature.TypeValueValuesEnum.UEFI_COMPATIBLE.name
        in guest_os_features)
    if uefi_compatible:
      daisy_utils.AppendBoolArg(import_args, 'uefi_compatible', True)

    if 'sysprep_windows' in self.args:
      daisy_utils.AppendBoolArg(import_args, 'sysprep_windows',
                                self.args.sysprep_windows)
    if 'no_address' in self.args:
      daisy_utils.AppendBoolArg(import_args, 'no_external_ip',
                                self.args.no_address)
    if 'compute_service_account' in self.args:
      daisy_utils.AppendArg(import_args, 'compute_service_account',
                            self.args.compute_service_account)
    return import_args

  def GetAndCreateDaisyBucket(self):
    return daisy_utils.CreateDaisyBucketInProject(
        self.GetBucketLocation(),
        self.storage_client,
        enable_uniform_level_access=True)

  def GetBucketLocation(self):
    if self.args.storage_location:
      return self.args.storage_location

    return None


class ImportFromExternalCloudProviderStager(BaseImportStager):
  """Image import stager from an external cloud provider."""

  def Stage(self):
    import_args = []

    _AppendAwsArgs(self.args, import_args)
    _AppendTranslateWorkflowArg(self.args, import_args)

    import_args.extend(
        super(ImportFromExternalCloudProviderStager, self).Stage())
    return import_args

  def GetBucketLocation(self):
    if self.args.zone:
      return daisy_utils.GetRegionFromZone(self.args.zone)
    return super(ImportFromExternalCloudProviderStager,
                 self).GetBucketLocation()


class ImportFromImageStager(BaseImportStager):
  """Image import stager from an existing image."""

  def Stage(self):
    _CheckForExistingImage(
        self.args.source_image,
        self.compute_holder,
        arg_name='source-image',
        expect_to_exist=True)
    import_args = []

    daisy_utils.AppendArg(import_args, 'source_image', self.args.source_image)
    if self.args.data_disk:
      daisy_utils.AppendBoolArg(import_args, 'data_disk', self.args.data_disk)
    else:
      _AppendTranslateWorkflowArg(self.args, import_args)

    import_args.extend(super(ImportFromImageStager, self).Stage())
    return import_args

  def _GetSourceImage(self):
    ref = resources.REGISTRY.Parse(
        self.args.source_image,
        collection='compute.images',
        params={'project': properties.VALUES.core.project.GetOrFail})
    # source_name should be of the form 'global/images/image-name'.
    source_name = ref.RelativeName()[len(ref.Parent().RelativeName() + '/'):]
    return source_name

  def GetBucketLocation(self):
    if self.args.zone:
      return daisy_utils.GetRegionFromZone(self.args.zone)
    return super(ImportFromImageStager, self).GetBucketLocation()


class BaseImportFromFileStager(BaseImportStager):
  """Abstract image import stager for import from a file."""

  def Stage(self):
    self._FileStage()

    import_args = []

    # Import and (maybe) translate from the scratch bucket.
    daisy_utils.AppendArg(import_args, 'source_file', self.gcs_uri)
    if self.args.data_disk:
      daisy_utils.AppendBoolArg(import_args, 'data_disk', self.args.data_disk)
    else:
      _AppendTranslateWorkflowArg(self.args, import_args)

    import_args.extend(super(BaseImportFromFileStager, self).Stage())
    return import_args

  def _FileStage(self):
    """Prepare image file for importing."""
    # If the file is an OVA file, print a warning.
    if self.args.source_file.lower().endswith('.ova'):
      log.warning(
          'The specified input file may contain more than one virtual disk. '
          'Only the first vmdk disk will be imported. To import a .ova'
          'completely, please try \'gcloud compute instances import\''
          'instead.')
    elif (self.args.source_file.lower().endswith('.tar.gz') or
          self.args.source_file.lower().endswith('.tgz')):
      raise exceptions.BadFileException(
          '`gcloud compute images import` does not support compressed '
          'archives. Please extract your image and try again.\n If you got '
          'this file by exporting an image from Compute Engine (e.g., by '
          'using `gcloud compute images export`) then you can instead use '
          '`gcloud compute images create` to create your image from your '
          '.tar.gz file.')
    self.gcs_uri = self._CopySourceFileToScratchBucket()

  @abc.abstractmethod
  def _CopySourceFileToScratchBucket(self):
    raise NotImplementedError


class ImportFromLocalFileStager(BaseImportFromFileStager):
  """Image import stager from a local file."""

  def _CopySourceFileToScratchBucket(self):
    return self._UploadToGcs(self.args.async_, self.args.source_file,
                             self.daisy_bucket, uuid.uuid4())

  def _UploadToGcs(self, is_async, local_path, daisy_bucket, image_uuid):
    """Uploads a local file to GCS. Returns the gs:// URI to that file."""
    file_name = os.path.basename(local_path).replace(' ', '-')
    dest_path = 'gs://{0}/tmpimage/{1}-{2}'.format(daisy_bucket, image_uuid,
                                                   file_name)
    if is_async:
      log.status.Print('Async: After upload is complete, your image will be '
                       'imported from Cloud Storage asynchronously.')
    with progress_tracker.ProgressTracker('Copying [{0}] to [{1}]'.format(
        local_path, dest_path)):
      return self._UploadToGcsStorageApi(local_path, dest_path)

  def _UploadToGcsStorageApi(self, local_path, dest_path):
    """Uploads a local file to Cloud Storage using the gcloud storage api client."""
    dest_object = storage_util.ObjectReference.FromUrl(dest_path)
    self.storage_client.CopyFileToGCS(local_path, dest_object)
    return dest_path


class ImportFromGSFileStager(BaseImportFromFileStager):
  """Image import stager from a file in Cloud Storage."""

  def __init__(self, storage_client, compute_holder, args, gcs_uri):
    self.source_file_gcs_uri = gcs_uri
    super(ImportFromGSFileStager, self).__init__(storage_client, compute_holder,
                                                 args)

  def GetBucketLocation(self):
    return self.storage_client.GetBucketLocationForFile(
        self.source_file_gcs_uri)

  def _CopySourceFileToScratchBucket(self):
    image_file = os.path.basename(self.source_file_gcs_uri)
    dest_uri = 'gs://{0}/tmpimage/{1}-{2}'.format(self.daisy_bucket,
                                                  uuid.uuid4(), image_file)
    src_object = resources.REGISTRY.Parse(
        self.source_file_gcs_uri, collection='storage.objects')
    dest_object = resources.REGISTRY.Parse(
        dest_uri, collection='storage.objects')
    with progress_tracker.ProgressTracker('Copying [{0}] to [{1}]'.format(
        self.source_file_gcs_uri, dest_uri)):
      self.storage_client.Rewrite(src_object, dest_object)
    return dest_uri


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ImportBeta(Import):
  """Import an image into Compute Engine for beta releases."""

  _OS_CHOICES = os_choices.OS_CHOICES_IMAGE_IMPORT_BETA

  @classmethod
  def Args(cls, parser):
    super(ImportBeta, cls).Args(parser)
    daisy_utils.AddExtraCommonDaisyArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ImportAlpha(ImportBeta):
  """Import an image into Compute Engine for alpha releases."""

  _OS_CHOICES = os_choices.OS_CHOICES_IMAGE_IMPORT_ALPHA


Import.detailed_help = {
    'brief': 'Import an image into Compute Engine',
    'DESCRIPTION': """
        *{command}* imports Virtual Disk images, such as VMWare VMDK files
        and VHD files, into Compute Engine.

        Importing images involves four steps:
        *  Upload the virtual disk file to Cloud Storage.
        *  Import the image to Compute Engine.
        *  Detect the OS and bootloader contained on the disk.
        *  Translate the image to make a bootable image.
        This command performs all four of these steps as required,
        depending on the input arguments specified.

        Before importing an image, set up access to Cloud Storage and grant
        required roles to the user accounts and service accounts. For more
        information, see [](https://cloud.google.com/compute/docs/import/requirements-export-import-images).

        To override the detected OS, specify the `--os` flag.
        You can omit the translation step using the `--data-disk` flag.

        If you exported your disk from Compute Engine then you don't
        need to re-import it. Instead, use `{parent_command} create`
        to create more images from the disk.

        Files stored on Cloud Storage and images in Compute Engine incur
        charges. See [](https://cloud.google.com/compute/docs/images/importing-virtual-disks#resource_cleanup).
        """,

    'EXAMPLES': """
        To import a centos-7 VMDK file, run:

          $ {command} myimage-name --os=centos-7 --source-file=mysourcefile

        To import a data disk without operating system, run:

          $ {command} myimage-name --data-disk --source-file=mysourcefile
        """,
}
