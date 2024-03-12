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
"""Utils for transfer appliances commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum


class ApprovedCountries(enum.Enum):
  """Countries where Transfer Appliances are approved for use."""
  US = 'US'  # United States
  # Beginning of European Union countries
  AT = 'AT'
  BE = 'BE'
  BG = 'BG'
  HR = 'HR'
  CY = 'CY'
  CZ = 'CZ'
  DK = 'DK'
  EE = 'EE'
  FI = 'FI'
  FR = 'FR'
  DE = 'DE'
  GR = 'GR'
  HU = 'HU'
  IE = 'IE'
  IT = 'IT'
  LV = 'LV'
  LT = 'LT'
  LU = 'LU'
  MT = 'MT'
  NL = 'NL'
  PL = 'PL'
  PT = 'PT'
  RO = 'RO'
  SK = 'SK'
  SI = 'SI'
  ES = 'ES'
  SE = 'SE'
  GB = 'GB'
  # End of European Union countries
  CA = 'CA'  # Canada
  NO = 'NO'  # Norway
  CH = 'CH'  # Switzerland
  SG = 'SG'  # Singapore


class CloudRegions(enum.Enum):
  US_CENTRAL1 = 'us-central1'
  EUROPE_WEST1 = 'europe-west1'
  ASIA_SOUTHEAST1 = 'asia-southeast1'

APPROVED_COUNTRIES = [e.value for e in ApprovedCountries]
CLOUD_REGIONS = [e.value for e in CloudRegions]
COUNTRY_TO_LOCATION_MAP = {
    ApprovedCountries.US.value: CloudRegions.US_CENTRAL1.value,  # United States
    ApprovedCountries.CA.value: CloudRegions.US_CENTRAL1.value,  # Canada
    # Beginning of European Union countries
    ApprovedCountries.AT.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.BE.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.BG.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.HR.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.CY.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.CZ.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.DK.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.EE.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.FI.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.FR.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.DE.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.GR.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.HU.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.IE.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.IT.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.LV.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.LT.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.LU.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.MT.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.NL.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.PL.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.PT.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.RO.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.SK.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.SI.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.ES.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.SE.value: CloudRegions.EUROPE_WEST1.value,
    ApprovedCountries.GB.value: CloudRegions.ASIA_SOUTHEAST1.value,
    # End of European Union countries
    ApprovedCountries.NO.value: CloudRegions.EUROPE_WEST1.value,  # Norway
    ApprovedCountries.CH.value: CloudRegions.EUROPE_WEST1.value,  # Switzerland
    ApprovedCountries.SG.value: CloudRegions.ASIA_SOUTHEAST1.value,  # Singapore
}
