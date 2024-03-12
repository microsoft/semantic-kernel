# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Additional help about Access Control Lists."""

# TODO(iam-beta): Revise this to include new IAM syntax.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  Access Control Lists (ACLs) allow you to control who can read and write
  your data, and who can read and write the ACLs themselves.

  If not specified at the time an object is uploaded (e.g., via the gsutil cp
  -a option), objects will be created with a default object ACL set on the
  bucket (see "gsutil help defacl"). You can replace the ACL on an object
  or bucket using the "gsutil acl set" command, or
  modify the existing ACL using the "gsutil acl ch" command (see "gsutil help
  acl").


<B>BUCKET VS OBJECT ACLS</B>
  In Google Cloud Storage, the bucket ACL works as follows:

  - Users granted READ access are allowed to list the bucket contents and read
    bucket metadata other than its ACL.

  - Users granted WRITE access are allowed READ access and also are allowed to
    write and delete objects in that bucket, including overwriting previously
    written objects.

  - Users granted OWNER access are allowed WRITE access and also are allowed to
    read and write the bucket's ACL.

  The object ACL works as follows:

  - Users granted READ access are allowed to read the object's data and
    metadata.

  - Users granted OWNER access are allowed READ access and also are allowed to
    read and write the object's ACL.

  A couple of points are worth noting, that sometimes surprise users:

  1. There is no WRITE access for objects; attempting to set an ACL with WRITE
     permission for an object will result in an error.

  2. The bucket ACL plays no role in determining who can read objects; only the
     object ACL matters for that purpose. This is different from how things
     work in Linux file systems, where both the file and directory permission
     control file read access. It also means, for example, that someone with
     OWNER over the bucket may not have read access to objects in the bucket.
     This is by design, and supports useful cases. For example, you might want
     to set up bucket ownership so that a small group of administrators have
     OWNER on the bucket (with the ability to delete data to control storage
     costs), but not grant those users read access to the object data (which
     might be sensitive data that should only be accessed by a different
     specific group of users).


<B>ACCESSING PUBLIC OBJECTS</B>
  Objects with public READ access can be accessed anonymously by gsutil, via
  a browser, or via Cloud Storage APIs. For more details on accessing public
  objects, see:

    https://cloud.google.com/storage/docs/access-public-data


<B>CANNED ACLS</B>
  The simplest way to set an ACL on a bucket or object is using a "canned
  ACL". The available canned ACLs are:

  project-private
    Gives permission to the project team based on their roles. Anyone who is
    part of the team has READ permission, and project owners and project editors
    have OWNER permission. This is the default ACL for newly created
    buckets. This is also the default ACL for newly created objects unless the
    default object ACL for that bucket has been changed. For more details see
    "gsutil help projects".

  private
    Gives the requester (and only the requester) OWNER permission for a
    bucket or object.

  public-read
    Gives all users (whether logged in or anonymous) READ permission. When
    you apply this to an object, anyone on the Internet can read the object
    without authenticating.

    NOTE: By default, publicly readable objects are served with a Cache-Control
    header allowing such objects to be cached for 3600 seconds. If you need to
    ensure that updates become visible immediately, you should set a
    Cache-Control header of "Cache-Control:private, max-age=0, no-transform" on
    such objects. For help doing this, see 'gsutil help setmeta'.

    NOTE: Setting a bucket ACL to public-read will remove all OWNER and WRITE
    permissions from everyone except the project owner group. Setting an object
    ACL to public-read will remove all OWNER and WRITE permissions from
    everyone except the object owner. For this reason, we recommend using
    the "acl ch" command to make these changes; see "gsutil help acl ch" for
    details.

  public-read-write
    Gives all users READ and WRITE permission. This ACL applies only to buckets.
    NOTE: Setting a bucket to public-read-write will allow anyone on the
    Internet to upload anything to your bucket. You will be responsible for this
    content.

    NOTE: Setting a bucket ACL to public-read-write will remove all OWNER
    permissions from everyone except the project owner group. Setting an object
    ACL to public-read-write will remove all OWNER permissions from
    everyone except the object owner. For this reason, we recommend using
    the "acl ch" command to make these changes; see "gsutil help acl ch" for
    details.

  authenticated-read
    Gives the requester OWNER permission and gives all authenticated
    Google account holders READ permission.

  bucket-owner-read
    Gives the requester OWNER permission and gives the bucket owner READ
    permission. This is used only with objects.

  bucket-owner-full-control
    Gives the requester OWNER permission and gives the bucket owner
    OWNER permission. This is used only with objects.


<B>ACL JSON</B>
  When you use a canned ACL, it is translated into an JSON representation
  that can later be retrieved and edited to specify more fine-grained
  detail about who can read and write buckets and objects. By running
  the "gsutil acl get" command you can retrieve the ACL JSON, and edit it to
  customize the permissions.

  As an example, if you create an object in a bucket that has no default
  object ACL set and then retrieve the ACL on the object, it will look
  something like this:

  [
    {
      "entity": "group-00b4903a9740e42c29800f53bd5a9a62a2f96eb3f64a4313a115df3f3a776bf7",
      "entityId": "00b4903a9740e42c29800f53bd5a9a62a2f96eb3f64a4313a115df3f3a776bf7",
      "role": "OWNER"
    },
    {
      "entity": "group-00b4903a977fd817e9da167bc81306489181a110456bb635f466d71cf90a0d51",
      "entityId": "00b4903a977fd817e9da167bc81306489181a110456bb635f466d71cf90a0d51",
      "role": "OWNER"
    },
    {
      "entity": "00b4903a974898cc8fc309f2f2835308ba3d3df1b889d3fc7e33e187d52d8e71",
      "entityId": "00b4903a974898cc8fc309f2f2835308ba3d3df1b889d3fc7e33e187d52d8e71",
      "role": "READER"
    }
  ]

  The ACL consists collection of elements, each of which specifies an Entity
  and a Role.  Entities are the way you specify an individual or group of
  individuals, and Roles specify what access they're permitted.

  This particular ACL grants OWNER to two groups (which means members
  of those groups are allowed to read the object and read and write the ACL),
  and READ permission to a third group. The project groups are (in order)
  the project owners group, editors group, and viewers group.

  The 64 digit hex identifiers (following any prefixes like "group-") used in
  this ACL are called canonical IDs.  They are used to identify predefined
  groups associated with the project that owns the bucket: the Project Owners,
  Project Editors, and All Project Team Members groups. For more information
  the permissions and roles of these project groups, see "gsutil help projects".

  Here's an example of an ACL specified using the group-by-email and
  group-by-domain entities:

[
  {
    "entity": "group-travel-companion-owners@googlegroups.com"
    "email": "travel-companion-owners@googlegroups.com",
    "role": "OWNER",
  }
  {
    "domain": "example.com",
    "entity": "domain-example.com"
    "role": "READER",
  },
]

  This ACL grants members of an email group OWNER, and grants READ
  access to any user in a domain (which must be a Google Apps for Business
  domain). By applying email group grants to a collection of objects
  you can edit access control for large numbers of objects at once via
  http://groups.google.com. That way, for example, you can easily and quickly
  change access to a group of company objects when employees join and leave
  your company (i.e., without having to individually change ACLs across
  potentially millions of objects).


<B>SHARING SCENARIOS</B>
  For more detailed examples how to achieve various useful sharing use
  cases see https://cloud.google.com/storage/docs/collaboration
""")


class CommandOptions(HelpProvider):
  """Additional help about Access Control Lists."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='acls',
      help_name_aliases=[
          'ACL',
          'access control',
          'access control list',
          'authorization',
          'canned',
          'canned acl',
      ],
      help_type='additional_help',
      help_one_line_summary='Working With Access Control Lists',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
