# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Definitions of shared DNS record types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from dns import rdatatype
from googlecloudsdk.api_lib.dns import svcb_stub

# Extended (i.e. Cloud DNS specific/internal) record types supported by Cloud
# DNS.  Note that since these are internal to Cloud DNS, they do not have a wire
# value like the standard types below.
CLOUD_DNS_EXTENDED_TYPES = frozenset(['ALIAS'])

# Standard record types supported by Cloud DNS. See
# https://cloud.google.com/dns/docs/overview#supported_dns_record_types
SUPPORTED_TYPES = frozenset((
    rdatatype.A,
    rdatatype.AAAA,
    rdatatype.CAA,
    rdatatype.CNAME,
    rdatatype.DNSKEY,
    rdatatype.DS,
    svcb_stub.HTTPS,  # Replace after updating to dnspython 2.x.
    rdatatype.IPSECKEY,
    rdatatype.MX,
    rdatatype.NAPTR,
    rdatatype.NS,
    rdatatype.PTR,
    rdatatype.SOA,
    rdatatype.SPF,
    rdatatype.SRV,
    svcb_stub.SVCB,  # Replace after updating to dnspython 2.x.
    rdatatype.SSHFP,
    rdatatype.TLSA,
    rdatatype.TXT,
))
