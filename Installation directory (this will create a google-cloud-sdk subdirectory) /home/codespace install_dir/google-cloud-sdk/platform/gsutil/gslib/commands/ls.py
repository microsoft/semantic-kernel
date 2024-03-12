# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implementation of Unix-like ls command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import re

import six
from gslib.cloud_api import NotFoundException
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.storage_url import ContainsWildcard
from gslib.storage_url import StorageUrlFromString
from gslib.utils.constants import NO_MAX
from gslib.utils.constants import S3_DELETE_MARKER_GUID
from gslib.utils.constants import UTF8
from gslib.utils.ls_helper import ENCRYPTED_FIELDS
from gslib.utils.ls_helper import LsHelper
from gslib.utils.ls_helper import PrintFullInfoAboutObject
from gslib.utils.ls_helper import UNENCRYPTED_FULL_LISTING_FIELDS
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.text_util import InsistAscii
from gslib.utils import text_util
from gslib.utils.translation_helper import AclTranslation
from gslib.utils.translation_helper import LabelTranslation
from gslib.utils.unit_util import MakeHumanReadable

# Regex that assists with converting JSON timestamp to ls-style output.
# This excludes timestamp fractional seconds, for example:
# 2013-07-03 20:32:53.048000+00:00
JSON_TIMESTAMP_RE = re.compile(r'([^\s]*)\s([^\.\+]*).*')

_SYNOPSIS = """
  gsutil ls [-a] [-b] [-d] [-l] [-L] [-r] [-p proj_id] url...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """

<B>DESCRIPTION</B>
Retrieves a list of providers, buckets, or objects matching the criteria,
ordered in the list lexicographically by name.


<B>LISTING PROVIDERS, BUCKETS, SUBDIRECTORIES, AND OBJECTS</B>
  If you run ``gsutil ls`` without URLs, it lists all of the Google Cloud Storage
  buckets under your default project ID (or all of the Cloud Storage buckets
  under the project you specify with the ``-p`` flag):

    gsutil ls

  If you specify one or more provider URLs, ``gsutil ls`` lists buckets at each
  listed provider:

    gsutil ls gs://

  gsutil currently supports ``gs://`` and ``s3://`` as valid providers

  If you specify bucket URLs, or use `URI wildcards
  <https://cloud.google.com/storage/docs/wildcards>`_ to capture a set of
  buckets, ``gsutil ls`` lists objects at the top level of each bucket, along
  with the names of each subdirectory. For example:

    gsutil ls gs://bucket

  might produce output like:

    gs://bucket/obj1.htm
    gs://bucket/obj2.htm
    gs://bucket/images1/
    gs://bucket/images2/

  The "/" at the end of the last 2 URLs tells you they are subdirectories,
  which you can list using:

    gsutil ls gs://bucket/images*

  If you specify object URLs, ``gsutil ls`` lists the specified objects. For
  example:

    gsutil ls gs://bucket/*.txt

  lists all files whose name matches the above wildcard at the top level of
  the bucket.

  For more details, see `URI wildcards
  <https://cloud.google.com/storage/docs/wildcards>`_.


<B>DIRECTORY BY DIRECTORY, FLAT, and RECURSIVE LISTINGS</B>
  Listing a bucket or subdirectory (as illustrated near the end of the previous
  section) only shows the objects and names of subdirectories it contains. You
  can list all objects in a bucket by using the -r option. For example:

    gsutil ls -r gs://bucket

  lists the top-level objects and buckets, then the objects and buckets under
  gs://bucket/images1, then those under gs://bucket/images2, etc.

  If you want to see all objects in the bucket in one "flat" listing use the
  recursive ("**") wildcard, like:

    gsutil ls -r gs://bucket/**

  or, for a flat listing of a subdirectory:

    gsutil ls -r gs://bucket/dir/**

  If you want to see only the subdirectory itself, use the -d option:

    gsutil ls -d gs://bucket/dir


<B>LISTING OBJECT DETAILS</B>
  If you specify the -l option, gsutil outputs additional information about
  each matching provider, bucket, subdirectory, or object. For example:

    gsutil ls -l gs://bucket/*.html gs://bucket/*.txt

  prints the object size, creation time stamp, and name of each matching
  object, along with the total count and sum of sizes of all matching objects:

       2276224  2020-03-02T19:25:17Z  gs://bucket/obj1.html
       3914624  2020-03-02T19:30:27Z  gs://bucket/obj2.html
           131  2020-03-02T19:37:45Z  gs://bucket/obj3.txt
    TOTAL: 3 objects, 6190979 bytes (5.9 MiB)

  Note that the total listed in parentheses above is in mebibytes (or gibibytes,
  tebibytes, etc.), which corresponds to the unit of billing measurement for
  Google Cloud Storage.

  You can get a listing of all the objects in the top-level bucket directory
  (along with the total count and sum of sizes) using a command like:

    gsutil ls -l gs://bucket

  To print additional detail about objects and buckets use the gsutil ls -L
  option. For example:

    gsutil ls -L gs://bucket/obj1

  prints something like:

    gs://bucket/obj1:
            Creation time:                    Fri, 26 May 2017 22:55:44 GMT
            Update time:                      Tue, 18 Jul 2017 12:31:18 GMT
            Storage class:                    STANDARD
            Content-Length:                   60183
            Content-Type:                     image/jpeg
            Hash (crc32c):                    zlUhtg==
            Hash (md5):                       Bv86IAzFzrD1Z2io/c7yqA==
            ETag:                             5ca67960a586723b7344afffc81
            Generation:                       1378862725952000
            Metageneration:                   1
            ACL:                              [
      {
        "entity": "project-owners-867484910061",
        "projectTeam": {
          "projectNumber": "867484910061",
          "team": "owners"
        },
        "role": "OWNER"
      },
      {
        "email": "jane@gmail.com",
        "entity": "user-jane@gmail.com",
        "role": "OWNER"
      }
    ]
    TOTAL: 1 objects, 60183 bytes (58.77 KiB)

  Note that results may contain additional fields, such as custom metadata or
  a storage class update time, if they are applicable to the object.

  Also note that some fields, such as update time, are not available with the
  (non-default) XML API.

  See also "gsutil help acl" for getting a more readable version of the ACL.


<B>LISTING BUCKET DETAILS</B>
  If you want to see information about the bucket itself, use the -b
  option. For example:

    gsutil ls -L -b gs://bucket

  prints something like:

    gs://bucket/ :
            Storage class:                STANDARD
            Location constraint:          US
            Versioning enabled:           False
            Logging configuration:        None
            Website configuration:        None
            CORS configuration:           None
            Lifecycle configuration:      None
            Requester Pays enabled:       True
            Labels:                       None
            Default KMS key:              None
            Time created:                 Thu, 14 Jan 2016 19:25:17 GMT
            Time updated:                 Thu, 08 Jun 2017 21:17:59 GMT
            Metageneration:               1
            Bucket Policy Only enabled:   False
            ACL:
              [
                {
                  "entity": "project-owners-867489160491",
                  "projectTeam": {
                    "projectNumber": "867489160491",
                    "team": "owners"
                  },
                  "role": "OWNER"
                }
              ]
            Default ACL:
              [
                {
                  "entity": "project-owners-867489160491",
                  "projectTeam": {
                    "projectNumber": "867489160491",
                    "team": "owners"
                  },
                  "role": "OWNER"
                }
              ]

  Note that some fields above (time created, time updated, metageneration) are
  not available with the (non-default) XML API.


<B>OPTIONS</B>
  -l          Prints long listing (owner, length).

  -L          Prints even more detail than -l.

              Note: If you use this option with the (non-default) XML API it
              generates an additional request per object being listed, which
              makes the -L option run much more slowly and cost more than the
              default JSON API.

  -d          List matching subdirectory names instead of contents, and do not
              recurse into matching subdirectories even if the -R option is
              specified.

  -b          Prints info about the bucket when used with a bucket URL.

  -h          When used with -l, prints object sizes in human readable format
              (e.g., 1 KiB, 234 MiB, 2 GiB, etc.)

  -p proj_id  Specifies the project ID or project number to use for listing
              buckets.

  -R, -r      Requests a recursive listing, performing at least one listing
              operation per subdirectory. If you have a large number of
              subdirectories and do not require recursive-style output ordering,
              you may be able to instead use wildcards to perform a flat
              listing, e.g.  ``gsutil ls gs://mybucket/**``, which generally
              performs fewer listing operations.

  -a          Includes non-current object versions / generations in the listing
              (only useful with a versioning-enabled bucket). If combined with
              -l option also prints metageneration for each listed object.

  -e          Include ETag in long listing (-l) output.
""")


class ListingStyle(object):
  """Enum class for specifying listing style."""
  SHORT = 'SHORT'
  LONG = 'LONG'
  LONG_LONG = 'LONG_LONG'


class LsCommand(Command):
  """Implementation of gsutil ls command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'ls',
      command_name_aliases=[
          'dir',
          'list',
      ],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=NO_MAX,
      supported_sub_args='aebdlLhp:rR',
      file_url_ok=False,
      provider_url_ok=True,
      urls_start_arg=0,
      gs_api_support=[
          ApiSelector.XML,
          ApiSelector.JSON,
      ],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudURLsArgument(),
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='ls',
      help_name_aliases=[
          'dir',
          'list',
      ],
      help_type='command_help',
      help_one_line_summary='List providers, buckets, or objects',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  # TODO(b/206151616) Add mappings for remaining flags.
  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'ls', '--fetch-encrypted-object-hashes'],
      flag_map={
          '-r': GcloudStorageFlag('-r'),
          '-R': GcloudStorageFlag('-r'),
          '-l': GcloudStorageFlag('-l'),
          '-L': GcloudStorageFlag('-L'),
          '-b': GcloudStorageFlag('-b'),
          '-e': GcloudStorageFlag('-e'),
          '-a': GcloudStorageFlag('-a'),
          '-h': GcloudStorageFlag('--readable-sizes'),
          '-p': GcloudStorageFlag('--project'),
      },
  )

  def _PrintBucketInfo(self, bucket_blr, listing_style):
    """Print listing info for given bucket.

    Args:
      bucket_blr: BucketListingReference for the bucket being listed
      listing_style: ListingStyle enum describing type of output desired.

    Returns:
      Tuple (total objects, total bytes) in the bucket.
    """
    if (listing_style == ListingStyle.SHORT or
        listing_style == ListingStyle.LONG):
      text_util.print_to_fd(bucket_blr)
      return
    # listing_style == ListingStyle.LONG_LONG:
    # We're guaranteed by the caller that the root object is populated.
    bucket = bucket_blr.root_object
    location_constraint = bucket.location
    storage_class = bucket.storageClass
    fields = {
        'bucket': bucket_blr.url_string,
        'storage_class': storage_class,
        'location_constraint': location_constraint,
        'acl': AclTranslation.JsonFromMessage(bucket.acl),
        'default_acl': AclTranslation.JsonFromMessage(bucket.defaultObjectAcl),
        'versioning': bucket.versioning and bucket.versioning.enabled,
        'website_config': 'Present' if bucket.website else 'None',
        'logging_config': 'Present' if bucket.logging else 'None',
        'cors_config': 'Present' if bucket.cors else 'None',
        'lifecycle_config': 'Present' if bucket.lifecycle else 'None',
        'requester_pays': bucket.billing and bucket.billing.requesterPays
    }
    if bucket.retentionPolicy:
      fields['retention_policy'] = 'Present'
    if bucket.labels:
      fields['labels'] = LabelTranslation.JsonFromMessage(bucket.labels,
                                                          pretty_print=True)
    else:
      fields['labels'] = 'None'
    if bucket.encryption and bucket.encryption.defaultKmsKeyName:
      fields['default_kms_key'] = bucket.encryption.defaultKmsKeyName
    else:
      fields['default_kms_key'] = 'None'
    fields['encryption_config'] = 'Present' if bucket.encryption else 'None'
    # Fields not available in all APIs (e.g. the XML API)
    if bucket.autoclass and bucket.autoclass.enabled:
      fields['autoclass_enabled_date'] = (
          bucket.autoclass.toggleTime.strftime('%a, %d %b %Y'))
    if bucket.locationType:
      fields['location_type'] = bucket.locationType
    if bucket.customPlacementConfig:
      fields['custom_placement_locations'] = (
          bucket.customPlacementConfig.dataLocations)
    if bucket.metageneration:
      fields['metageneration'] = bucket.metageneration
    if bucket.timeCreated:
      fields['time_created'] = bucket.timeCreated.strftime(
          '%a, %d %b %Y %H:%M:%S GMT')
    if bucket.updated:
      fields['updated'] = bucket.updated.strftime('%a, %d %b %Y %H:%M:%S GMT')
    if bucket.defaultEventBasedHold:
      fields['default_eventbased_hold'] = bucket.defaultEventBasedHold
    if bucket.iamConfiguration:
      if bucket.iamConfiguration.bucketPolicyOnly:
        enabled = bucket.iamConfiguration.bucketPolicyOnly.enabled
        fields['bucket_policy_only_enabled'] = enabled
      if bucket.iamConfiguration.publicAccessPrevention:
        fields[
            'public_access_prevention'] = bucket.iamConfiguration.publicAccessPrevention
    if bucket.rpo:
      fields['rpo'] = bucket.rpo
    if bucket.satisfiesPZS:
      fields['satisfies_pzs'] = bucket.satisfiesPZS

    # For field values that are multiline, add indenting to make it look
    # prettier.
    for key in fields:
      previous_value = fields[key]
      if (not isinstance(previous_value, six.string_types) or
          '\n' not in previous_value):
        continue
      new_value = previous_value.replace('\n', '\n\t  ')
      # Start multiline values on a new line if they aren't already.
      if not new_value.startswith('\n'):
        new_value = '\n\t  ' + new_value
      fields[key] = new_value

    # Only display certain properties if the given API returned them (JSON API
    # returns many fields that the XML API does not).
    autoclass_line = ''
    location_type_line = ''
    custom_placement_locations_line = ''
    metageneration_line = ''
    time_created_line = ''
    time_updated_line = ''
    default_eventbased_hold_line = ''
    retention_policy_line = ''
    bucket_policy_only_enabled_line = ''
    public_access_prevention_line = ''
    rpo_line = ''
    satisifies_pzs_line = ''
    if 'autoclass_enabled_date' in fields:
      autoclass_line = '\tAutoclass:\t\t\tEnabled on {autoclass_enabled_date}\n'
    if 'location_type' in fields:
      location_type_line = '\tLocation type:\t\t\t{location_type}\n'
    if 'custom_placement_locations' in fields:
      custom_placement_locations_line = (
          '\tPlacement locations:\t\t{custom_placement_locations}\n')
    if 'metageneration' in fields:
      metageneration_line = '\tMetageneration:\t\t\t{metageneration}\n'
    if 'time_created' in fields:
      time_created_line = '\tTime created:\t\t\t{time_created}\n'
    if 'updated' in fields:
      time_updated_line = '\tTime updated:\t\t\t{updated}\n'
    if 'default_eventbased_hold' in fields:
      default_eventbased_hold_line = (
          '\tDefault Event-Based Hold:\t{default_eventbased_hold}\n')
    if 'retention_policy' in fields:
      retention_policy_line = '\tRetention Policy:\t\t{retention_policy}\n'
    if 'bucket_policy_only_enabled' in fields:
      bucket_policy_only_enabled_line = ('\tBucket Policy Only enabled:\t'
                                         '{bucket_policy_only_enabled}\n')
    if 'public_access_prevention' in fields:
      public_access_prevention_line = ('\tPublic access prevention:\t'
                                       '{public_access_prevention}\n')
    if 'rpo' in fields:
      rpo_line = ('\tRPO:\t\t\t\t{rpo}\n')
    if 'satisfies_pzs' in fields:
      satisifies_pzs_line = '\tSatisfies PZS:\t\t\t{satisfies_pzs}\n'

    text_util.print_to_fd(
        ('{bucket} :\n'
         '\tStorage class:\t\t\t{storage_class}\n' + location_type_line +
         '\tLocation constraint:\t\t{location_constraint}\n' +
         custom_placement_locations_line +
         '\tVersioning enabled:\t\t{versioning}\n'
         '\tLogging configuration:\t\t{logging_config}\n'
         '\tWebsite configuration:\t\t{website_config}\n'
         '\tCORS configuration: \t\t{cors_config}\n'
         '\tLifecycle configuration:\t{lifecycle_config}\n'
         '\tRequester Pays enabled:\t\t{requester_pays}\n' +
         retention_policy_line + default_eventbased_hold_line +
         '\tLabels:\t\t\t\t{labels}\n' +
         '\tDefault KMS key:\t\t{default_kms_key}\n' + time_created_line +
         time_updated_line + metageneration_line +
         bucket_policy_only_enabled_line + autoclass_line +
         public_access_prevention_line + rpo_line + satisifies_pzs_line +
         '\tACL:\t\t\t\t{acl}\n'
         '\tDefault ACL:\t\t\t{default_acl}').format(**fields))
    if bucket_blr.storage_url.scheme == 's3':
      text_util.print_to_fd(
          'Note: this is an S3 bucket so configuration values may be '
          'blank. To retrieve bucket configuration values, use '
          'individual configuration commands such as gsutil acl get '
          '<bucket>.')

  def _PrintLongListing(self, bucket_listing_ref):
    """Prints an object with ListingStyle.LONG."""
    obj = bucket_listing_ref.root_object
    url_str = bucket_listing_ref.url_string
    if (obj.metadata and
        S3_DELETE_MARKER_GUID in obj.metadata.additionalProperties):
      size_string = '0'
      num_bytes = 0
      num_objs = 0
      url_str += '<DeleteMarker>'
    else:
      size_string = (MakeHumanReadable(obj.size)
                     if self.human_readable else str(obj.size))
      num_bytes = obj.size
      num_objs = 1

    timestamp = JSON_TIMESTAMP_RE.sub(r'\1T\2Z', str(obj.timeCreated))
    printstr = '%(size)10s  %(timestamp)s  %(url)s'
    encoded_etag = None
    encoded_metagen = None
    if self.all_versions:
      printstr += '  metageneration=%(metageneration)s'
      encoded_metagen = str(obj.metageneration)
    if self.include_etag:
      printstr += '  etag=%(etag)s'
      encoded_etag = obj.etag
    format_args = {
        'size': size_string,
        'timestamp': timestamp,
        'url': url_str,
        'metageneration': encoded_metagen,
        'etag': encoded_etag
    }
    text_util.print_to_fd(printstr % format_args)
    return (num_objs, num_bytes)

  def RunCommand(self):
    """Command entry point for the ls command."""
    got_nomatch_errors = False
    got_bucket_nomatch_errors = False
    listing_style = ListingStyle.SHORT
    get_bucket_info = False
    self.recursion_requested = False
    self.all_versions = False
    self.include_etag = False
    self.human_readable = False
    self.list_subdir_contents = True
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-a':
          self.all_versions = True
        elif o == '-e':
          self.include_etag = True
        elif o == '-b':
          get_bucket_info = True
        elif o == '-h':
          self.human_readable = True
        elif o == '-l':
          listing_style = ListingStyle.LONG
        elif o == '-L':
          listing_style = ListingStyle.LONG_LONG
        elif o == '-p':
          # Project IDs are sent as header values when using gs and s3 XML APIs.
          InsistAscii(a, 'Invalid non-ASCII character found in project ID')
          self.project_id = a
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
        elif o == '-d':
          self.list_subdir_contents = False

    if not self.args:
      # default to listing all gs buckets
      self.args = ['gs://']

    total_objs = 0
    total_bytes = 0

    def MaybePrintBucketHeader(blr):
      if len(self.args) > 1:
        text_util.print_to_fd('%s:' % six.ensure_text(blr.url_string))

    print_bucket_header = MaybePrintBucketHeader

    for url_str in self.args:
      storage_url = StorageUrlFromString(url_str)
      if storage_url.IsFileUrl():
        raise CommandException('Only cloud URLs are supported for %s' %
                               self.command_name)
      bucket_fields = None
      if (listing_style == ListingStyle.SHORT or
          listing_style == ListingStyle.LONG):
        bucket_fields = ['id']
      elif listing_style == ListingStyle.LONG_LONG:
        bucket_fields = [
            'acl',
            'autoclass',
            'billing',
            'cors',
            'customPlacementConfig',
            'defaultObjectAcl',
            'encryption',
            'iamConfiguration',
            'labels',
            'location',
            'locationType',
            'logging',
            'lifecycle',
            'metageneration',
            'retentionPolicy',
            'defaultEventBasedHold',
            'rpo',
            'satisfiesPZS',
            'storageClass',
            'timeCreated',
            'updated',
            'versioning',
            'website',
        ]
      if storage_url.IsProvider():
        # Provider URL: use bucket wildcard to list buckets.
        for blr in self.WildcardIterator(
            '%s://*' %
            storage_url.scheme).IterBuckets(bucket_fields=bucket_fields):
          self._PrintBucketInfo(blr, listing_style)
      elif storage_url.IsBucket() and get_bucket_info:
        # ls -b bucket listing request: List info about bucket(s).
        total_buckets = 0
        for blr in self.WildcardIterator(url_str).IterBuckets(
            bucket_fields=bucket_fields):
          if not ContainsWildcard(url_str) and not blr.root_object:
            # Iterator does not make an HTTP call for non-wildcarded
            # listings with fields=='id'. Ensure the bucket exists by calling
            # GetBucket.
            self.gsutil_api.GetBucket(blr.storage_url.bucket_name,
                                      fields=['id'],
                                      provider=storage_url.scheme)
          self._PrintBucketInfo(blr, listing_style)
          total_buckets += 1
        if not ContainsWildcard(url_str) and not total_buckets:
          got_bucket_nomatch_errors = True
      else:
        # URL names a bucket, object, or object subdir ->
        # list matching object(s) / subdirs.
        def _PrintPrefixLong(blr):
          text_util.print_to_fd('%-33s%s' %
                                ('', six.ensure_text(blr.url_string)))

        if listing_style == ListingStyle.SHORT:
          # ls helper by default readies us for a short listing.
          listing_helper = LsHelper(
              self.WildcardIterator,
              self.logger,
              all_versions=self.all_versions,
              print_bucket_header_func=print_bucket_header,
              should_recurse=self.recursion_requested,
              list_subdir_contents=self.list_subdir_contents)
        elif listing_style == ListingStyle.LONG:
          bucket_listing_fields = [
              'name',
              'size',
              'timeCreated',
              'updated',
          ]
          if self.all_versions:
            bucket_listing_fields.extend([
                'generation',
                'metageneration',
            ])
          if self.include_etag:
            bucket_listing_fields.append('etag')

          listing_helper = LsHelper(
              self.WildcardIterator,
              self.logger,
              print_object_func=self._PrintLongListing,
              print_dir_func=_PrintPrefixLong,
              print_bucket_header_func=print_bucket_header,
              all_versions=self.all_versions,
              should_recurse=self.recursion_requested,
              fields=bucket_listing_fields,
              list_subdir_contents=self.list_subdir_contents)

        elif listing_style == ListingStyle.LONG_LONG:
          # List all fields
          bucket_listing_fields = (UNENCRYPTED_FULL_LISTING_FIELDS +
                                   ENCRYPTED_FIELDS)
          listing_helper = LsHelper(
              self.WildcardIterator,
              self.logger,
              print_object_func=PrintFullInfoAboutObject,
              print_dir_func=_PrintPrefixLong,
              print_bucket_header_func=print_bucket_header,
              all_versions=self.all_versions,
              should_recurse=self.recursion_requested,
              fields=bucket_listing_fields,
              list_subdir_contents=self.list_subdir_contents)
        else:
          raise CommandException('Unknown listing style: %s' % listing_style)

        exp_dirs, exp_objs, exp_bytes = (
            listing_helper.ExpandUrlAndPrint(storage_url))
        if storage_url.IsObject() and exp_objs == 0 and exp_dirs == 0:
          got_nomatch_errors = True
        total_bytes += exp_bytes
        total_objs += exp_objs

    if total_objs and listing_style != ListingStyle.SHORT:
      text_util.print_to_fd(
          'TOTAL: %d objects, %d bytes (%s)' %
          (total_objs, total_bytes, MakeHumanReadable(float(total_bytes))))
    if got_nomatch_errors:
      raise CommandException('One or more URLs matched no objects.')
    if got_bucket_nomatch_errors:
      raise NotFoundException('One or more bucket URLs matched no buckets.')

    return 0
