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

"""core.util.time timezone data and maps."""


# Abbreviations/synomyms to IANA timezone name map from
# https://en.wikipedia.org/wiki/List_of_time_zone_abbreviations.
#
# TimeZone abbreviations are not unique. We pick the ones most relevant to the
# Cloud SDK. For example, CST is used for US/Central, China standard time and
# Cuba Standard Time. Most service date/times will be UTC or have an explicit
# numeric +/-HH:MM timezone offset, so duplicates will not be a big problem.


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


ABBREVIATION_TO_IANA = {
    'ACST': 'Australia/Adelaide',
    'AEST': 'Australia/Brisbane',
    'AFT': 'Asia/Kabul',
    'AKST': 'America/Anchorage',
    'AMST': 'UTC-03',
    'ART': 'America/Argentina/La_Rioja',
    'AST': 'Atlantic/Bermuda',
    'AWST': 'Australia/Perth',
    'AZOST': 'Atlantic/Azores',
    'AZT': 'Asia/Baku',
    'BDT': 'Asia/Brunei',
    'BIOT': 'UTC+06',
    'BIT': 'UTC-12',
    'BOT': 'UTC-04',
    'BRST': 'America/Sao_Paulo',
    'BRT': 'America/Sao_Paulo',
    'BST': 'UTC+01',
    'BTT': 'UTC+06',
    'CAT': 'UTC+02',
    'CCT': 'UTC+06:30',
    'CDT': 'America/Chicago',
    'CEST': 'Europe/Belgrade',
    'CET': 'Europe/Belgrade',
    'CHAST': 'UTC+12:45',
    'CHOT': 'Asia/Choibalsan',
    'ChST': 'UTC+10',
    'CHUT': 'UTC+10',
    'CIST': 'UTC-08',
    'CIT': 'UTC+08',
    'CKT': 'UTC-10',
    'CLST': 'UTC-03',
    'CLT': 'UTC-04',
    'COST': 'UTC-04',
    'COT': 'UTC-05',
    'CST': 'America/Chicago',
    'CT': 'Asia/Hong_Kong',
    'CVT': 'Atlantic/Cape_Verde',
    'CWST': 'UTC+08:45',
    'CXT': 'Indian/Christmas',
    'DAVT': 'Antarctica/Davis',
    'DDUT': 'Antarctica/DumontDUrville',
    'DFT': 'UTC+01',
    'EASST': 'UTC-05',
    'EAST': 'UTC-06',
    'EAT': 'UTC+03',
    'ECT': 'UTC-05',
    'EDT': 'America/New_York',
    'EEST': 'Europe/Chisinau',
    'EET': 'Europe/Chisinau',
    'EGST': 'UTC+00',
    'EGT': 'UTC-01',
    'EIT': 'UTC+09',
    'EST': 'America/New_York',
    'FET': 'Europe/Minsk',
    'FJT': 'Pacific/Fiji',
    'FKST': 'UTC-03',
    'FKT': 'UTC-04',
    'FNT': 'UTC-02',
    'GALT': 'Pacific/Galapagos',
    'GAMT': 'UTC-09',
    'GET': 'Asia/Tbilisi',
    'GFT': 'UTC-03',
    'GILT': 'UTC+12',
    'GIT': 'UTC-09',
    'GMT': 'UTC',
    'GST': 'Atlantic/South_Georgia',
    'GYT': 'America/Guyana',
    'HAEC': 'UTC+02',
    'HAST': 'Pacific/Honolulu',
    'HKT': 'Asia/Hong_Kong',
    'HMT': 'UTC+05',
    'HOVT': 'UTC+07',
    'HST': 'Pacific/Honolulu',
    'IBST': 'UTC',
    'ICT': 'UTC+07',
    'IOT': 'UTC+03',
    'IRKT': 'Asia/Irkutsk',
    'IRST': 'Asia/Tehran',
    'IST': 'Asia/Jerusalem',
    'JST': 'Asia/Tokyo',
    'KGT': 'UTC+06',
    'KOST': 'Pacific/Kosrae',
    'KRAT': 'Asia/Krasnoyarsk',
    'KST': 'Asia/Seoul',
    'LHST': 'UTC+11',
    'LINT': 'Pacific/Kiritimati',
    'MAGT': 'Asia/Magadan',
    'MART': 'UTC-09:30',
    'MAWT': 'Antarctica/Mawson',
    'MDT': 'America/Phoenix',
    'MEST': 'Europe/Belgrade',
    'MET': 'Europe/Belgrade',
    'MHT': 'UTC+12',
    'MIST': 'Antarctica/Macquarie',
    'MIT': 'UTC-09:30',
    'MMT': 'Asia/Rangoon',
    'MSK': 'Europe/Moscow',
    'MST': 'America/Phoenix',
    'MUT': 'Indian/Mahe',
    'MVT': 'Indian/Maldives',
    'MYT': 'UTC+08',
    'NCT': 'Pacific/Noumea',
    'NFT': 'Pacific/Norfolk',
    'NPT': 'Asia/Katmandu',
    'NST': 'America/St_Johns',
    'NT': 'America/St_Johns',
    'NUT': 'Pacific/Niue',
    'NZST': 'Pacific/Auckland',
    'OMST': 'Asia/Omsk',
    'ORAT': 'Asia/Oral',
    'PDT': 'America/Los_Angeles',
    'PETT': 'Asia/Kamchatka',
    'PET': 'UTC-05',
    'PGT': 'UTC+10',
    'PHOT': 'UTC+13',
    'PKT': 'Asia/Karachi',
    'PMST': 'UTC-03',
    'PONT': 'UTC+11',
    'PST': 'America/Los_Angeles',
    'PYST': 'America/Asuncion',
    'PYT': 'America/Asuncion',
    'RET': 'Indian/Reunion',
    'ROTT': 'Antarctica/Rothera',
    'SAKT': 'Asia/Sakhalin',
    'SAMT': 'Europe/Samara',
    'SAST': 'Africa/Johannesburg',
    'SBT': 'Pacific/Norfolk',
    'SGT': 'Asia/Kuala_Lumpur',
    'SLST': 'Asia/Colombo',
    'SRET': 'Asia/Srednekolymsk',
    'SST': 'Asia/Kuala_Lumpur',
    'SYOT': 'UTC+03',
    'TAHT': 'Pacific/Tahiti',
    'TFT': 'Indian/Kerguelen',
    'THA': 'UTC+07',
    'TJT': 'UTC+05',
    'TKT': 'UTC+13',
    'TLT': 'UTC+09',
    'TMT': 'UTC+05',
    'TOT': 'Pacific/Tongatapu',
    'TVT': 'UTC+12',
    'UCT': 'UTC',
    'ULAT': 'Asia/Ulaanbaatar',
    'US/Central': 'America/Chicago',
    'US/Eastern': 'America/New_York',
    'US/Mountain': 'America/Phoenix',
    'US/Pacific': 'America/Los_Angeles',
    'USZ1': 'Europe/Kaliningrad',
    'UYST': 'UTC-02',
    'UYT': 'UTC-03',
    'UZT': 'UTC+05',
    'VET': 'America/Caracas',
    'VLAT': 'Asia/Vladivostok',
    'VOLT': 'Europe/Volgograd',
    'VOST': 'Antarctica/Vostok',
    'VUT': 'UTC+11',
    'WAKT': 'Pacific/Wake',
    'WAST': 'Africa/Algiers',
    'WAT': 'Africa/Algiers',
    'WEST': 'Europe/Amsterdam',
    'WET': 'Europe/Amsterdam',
    'WIT': 'UTC+07',
    'WST': 'UTC+08',
    'YAKT': 'Asia/Yakutsk',
    'YEKT': 'Asia/Yekaterinburg',
    'Z': 'UTC',
}

# IANA timezone name to Windows timezone name map. Generated from
# http://unicode.org/repos/cldr/trunk/common/supplemental/windowsZones.xml.
# The mapping is imperfect (many to one) but its the best Windows can do.
IANA_TO_WINDOWS = {
    # (UTC-12:00) International Date Line West
    'Etc/GMT+12': 'Dateline Standard Time',

    # (UTC-11:00) Coordinated Universal Time-11
    'Etc/GMT+11': 'UTC-11',
    'Pacific/Midway': 'UTC-11',
    'Pacific/Niue': 'UTC-11',
    'Pacific/Pago_Pago': 'UTC-11',

    # (UTC-10:00) Hawaii
    'Etc/GMT+10': 'Hawaiian Standard Time',
    'Pacific/Honolulu': 'Hawaiian Standard Time',
    'Pacific/Johnston': 'Hawaiian Standard Time',
    'Pacific/Rarotonga': 'Hawaiian Standard Time',
    'Pacific/Tahiti': 'Hawaiian Standard Time',

    # (UTC-09:00) Alaska
    'America/Anchorage': 'Alaskan Standard Time',
    'America/Juneau': 'Alaskan Standard Time',
    'America/Metlakatla': 'Alaskan Standard Time',
    'America/Nome': 'Alaskan Standard Time',
    'America/Sitka': 'Alaskan Standard Time',
    'America/Yakutat': 'Alaskan Standard Time',

    # (UTC-08:00) Baja California

    # Unmappable

    # (UTC-08:00) Pacific Time (US & Canada)
    'America/Dawson': 'Pacific Standard Time',
    'America/Los_Angeles': 'Pacific Standard Time',
    'America/Santa_Isabel': 'Pacific Standard Time',
    'America/Tijuana': 'Pacific Standard Time',
    'America/Vancouver': 'Pacific Standard Time',
    'America/Whitehorse': 'Pacific Standard Time',
    'PST8PDT': 'Pacific Standard Time',

    # (UTC-07:00) Arizona
    'America/Creston': 'US Mountain Standard Time',
    'America/Dawson_Creek': 'US Mountain Standard Time',
    'America/Fort_Nelson': 'US Mountain Standard Time',
    'America/Hermosillo': 'US Mountain Standard Time',
    'America/Phoenix': 'US Mountain Standard Time',
    'Etc/GMT+7': 'US Mountain Standard Time',

    # (UTC-07:00) Chihuahua, La Paz, Mazatlan
    'America/Chihuahua': 'Mountain Standard Time (Mexico)',
    'America/Mazatlan': 'Mountain Standard Time (Mexico)',

    # (UTC-07:00) Mountain Time (US & Canada)
    'America/Boise': 'Mountain Standard Time',
    'America/Cambridge_Bay': 'Mountain Standard Time',
    'America/Denver': 'Mountain Standard Time',
    'America/Edmonton': 'Mountain Standard Time',
    'America/Inuvik': 'Mountain Standard Time',
    'America/Ojinaga': 'Mountain Standard Time',
    'America/Yellowknife': 'Mountain Standard Time',
    'MST7MDT': 'Mountain Standard Time',

    # (UTC-06:00) Central America
    'America/Belize': 'Central America Standard Time',
    'America/Costa_Rica': 'Central America Standard Time',
    'America/El_Salvador': 'Central America Standard Time',
    'America/Guatemala': 'Central America Standard Time',
    'America/Managua': 'Central America Standard Time',
    'America/Tegucigalpa': 'Central America Standard Time',
    'Etc/GMT+6': 'Central America Standard Time',
    'Pacific/Galapagos': 'Central America Standard Time',

    # (UTC-06:00) Central Time (US & Canada)
    'America/Chicago': 'Central Standard Time',
    'America/Indiana/Knox': 'Central Standard Time',
    'America/Indiana/Tell_City': 'Central Standard Time',
    'America/Matamoros': 'Central Standard Time',
    'America/Menominee': 'Central Standard Time',
    'America/North_Dakota/Beulah': 'Central Standard Time',
    'America/North_Dakota/Center': 'Central Standard Time',
    'America/North_Dakota/New_Salem': 'Central Standard Time',
    'America/Rainy_River': 'Central Standard Time',
    'America/Rankin_Inlet': 'Central Standard Time',
    'America/Resolute': 'Central Standard Time',
    'America/Winnipeg': 'Central Standard Time',
    'CST6CDT': 'Central Standard Time',

    # (UTC-06:00) Guadalajara, Mexico City, Monterrey
    'America/Bahia_Banderas': 'Central Standard Time (Mexico)',
    'America/Merida': 'Central Standard Time (Mexico)',
    'America/Mexico_City': 'Central Standard Time (Mexico)',
    'America/Monterrey': 'Central Standard Time (Mexico)',

    # (UTC-06:00) Saskatchewan
    'America/Regina': 'Canada Central Standard Time',
    'America/Swift_Current': 'Canada Central Standard Time',

    # (UTC-05:00) Bogota, Lima, Quito, Rio Branco
    'America/Bogota': 'SA Pacific Standard Time',
    'America/Cayman': 'SA Pacific Standard Time',
    'America/Coral_Harbour': 'SA Pacific Standard Time',
    'America/Eirunepe': 'SA Pacific Standard Time',
    'America/Guayaquil': 'SA Pacific Standard Time',
    'America/Jamaica': 'SA Pacific Standard Time',
    'America/Lima': 'SA Pacific Standard Time',
    'America/Panama': 'SA Pacific Standard Time',
    'America/Rio_Branco': 'SA Pacific Standard Time',
    'Etc/GMT+5': 'SA Pacific Standard Time',
    'Pacific/Easter': 'SA Pacific Standard Time',

    # (UTC-05:00) Chetumal
    'America/Cancun': 'Eastern Standard Time (Mexico)',

    # (UTC-05:00) Eastern Time (US & Canada)
    'America/Detroit': 'Eastern Standard Time',
    'America/Havana': 'Eastern Standard Time',
    'America/Indiana/Petersburg': 'Eastern Standard Time',
    'America/Indiana/Vincennes': 'Eastern Standard Time',
    'America/Indiana/Winamac': 'Eastern Standard Time',
    'America/Iqaluit': 'Eastern Standard Time',
    'America/Kentucky/Monticello': 'Eastern Standard Time',
    'America/Louisville': 'Eastern Standard Time',
    'America/Montreal': 'Eastern Standard Time',
    'America/Nassau': 'Eastern Standard Time',
    'America/New_York': 'Eastern Standard Time',
    'America/Nipigon': 'Eastern Standard Time',
    'America/Pangnirtung': 'Eastern Standard Time',
    'America/Port-au-Prince': 'Eastern Standard Time',
    'America/Thunder_Bay': 'Eastern Standard Time',
    'America/Toronto': 'Eastern Standard Time',
    'EST5EDT': 'Eastern Standard Time',

    # (UTC-05:00) Indiana (East)
    'America/Indiana/Marengo': 'US Eastern Standard Time',
    'America/Indianapolis': 'US Eastern Standard Time',
    'America/Indiana/Vevay': 'US Eastern Standard Time',

    # (UTC-04:30) Caracas
    'America/Caracas': 'Venezuela Standard Time',

    # (UTC-04:00) Asuncion
    'America/Asuncion': 'Paraguay Standard Time',

    # (UTC-04:00) Atlantic Time (Canada)
    'America/Glace_Bay': 'Atlantic Standard Time',
    'America/Goose_Bay': 'Atlantic Standard Time',
    'America/Halifax': 'Atlantic Standard Time',
    'America/Moncton': 'Atlantic Standard Time',
    'America/Thule': 'Atlantic Standard Time',
    'Atlantic/Bermuda': 'Atlantic Standard Time',

    # (UTC-04:00) Cuiaba
    'America/Campo_Grande': 'Central Brazilian Standard Time',
    'America/Cuiaba': 'Central Brazilian Standard Time',

    # (UTC-04:00) Georgetown, La Paz, Manaus, San Juan
    'America/Anguilla': 'SA Western Standard Time',
    'America/Antigua': 'SA Western Standard Time',
    'America/Aruba': 'SA Western Standard Time',
    'America/Barbados': 'SA Western Standard Time',
    'America/Blanc-Sablon': 'SA Western Standard Time',
    'America/Boa_Vista': 'SA Western Standard Time',
    'America/Curacao': 'SA Western Standard Time',
    'America/Dominica': 'SA Western Standard Time',
    'America/Grand_Turk': 'SA Western Standard Time',
    'America/Grenada': 'SA Western Standard Time',
    'America/Guadeloupe': 'SA Western Standard Time',
    'America/Guyana': 'SA Western Standard Time',
    'America/Kralendijk': 'SA Western Standard Time',
    'America/La_Paz': 'SA Western Standard Time',
    'America/Lower_Princes': 'SA Western Standard Time',
    'America/Manaus': 'SA Western Standard Time',
    'America/Marigot': 'SA Western Standard Time',
    'America/Martinique': 'SA Western Standard Time',
    'America/Montserrat': 'SA Western Standard Time',
    'America/Port_of_Spain': 'SA Western Standard Time',
    'America/Porto_Velho': 'SA Western Standard Time',
    'America/Puerto_Rico': 'SA Western Standard Time',
    'America/Santo_Domingo': 'SA Western Standard Time',
    'America/St_Barthelemy': 'SA Western Standard Time',
    'America/St_Kitts': 'SA Western Standard Time',
    'America/St_Lucia': 'SA Western Standard Time',
    'America/St_Thomas': 'SA Western Standard Time',
    'America/St_Vincent': 'SA Western Standard Time',
    'America/Tortola': 'SA Western Standard Time',
    'Etc/GMT+4': 'SA Western Standard Time',

    # (UTC-03:30) Newfoundland
    'America/St_Johns': 'Newfoundland Standard Time',

    # (UTC-03:00) Brasilia
    'America/Sao_Paulo': 'E. South America Standard Time',

    # (UTC-03:00) Cayenne, Fortaleza
    'America/Araguaina': 'SA Eastern Standard Time',
    'America/Belem': 'SA Eastern Standard Time',
    'America/Cayenne': 'SA Eastern Standard Time',
    'America/Fortaleza': 'SA Eastern Standard Time',
    'America/Maceio': 'SA Eastern Standard Time',
    'America/Paramaribo': 'SA Eastern Standard Time',
    'America/Recife': 'SA Eastern Standard Time',
    'America/Santarem': 'SA Eastern Standard Time',
    'Antarctica/Rothera': 'SA Eastern Standard Time',
    'Atlantic/Stanley': 'SA Eastern Standard Time',
    'Etc/GMT+3': 'SA Eastern Standard Time',

    # (UTC-03:00) City of Buenos Aires
    'America/Argentina/La_Rioja': 'Argentina Standard Time',
    'America/Argentina/Rio_Gallegos': 'Argentina Standard Time',
    'America/Argentina/Salta': 'Argentina Standard Time',
    'America/Argentina/San_Juan': 'Argentina Standard Time',
    'America/Argentina/San_Luis': 'Argentina Standard Time',
    'America/Argentina/Tucuman': 'Argentina Standard Time',
    'America/Argentina/Ushuaia': 'Argentina Standard Time',
    'America/Buenos_Aires': 'Argentina Standard Time',
    'America/Catamarca': 'Argentina Standard Time',
    'America/Cordoba': 'Argentina Standard Time',
    'America/Jujuy': 'Argentina Standard Time',
    'America/Mendoza': 'Argentina Standard Time',

    # (UTC-03:00) Greenland
    'America/Godthab': 'Greenland Standard Time',

    # (UTC-03:00) Montevideo
    'America/Montevideo': 'Montevideo Standard Time',

    # (UTC-03:00) Salvador
    'America/Bahia': 'Bahia Standard Time',

    # (UTC-03:00) Santiago
    'America/Santiago': 'Pacific SA Standard Time',
    'Antarctica/Palmer': 'Pacific SA Standard Time',

    # (UTC-02:00) Coordinated Universal Time-02
    'America/Noronha': 'UTC-02',
    'Atlantic/South_Georgia': 'UTC-02',
    'Etc/GMT+2': 'UTC-02',

    # (UTC-01:00) Azores
    'America/Scoresbysund': 'Azores Standard Time',
    'Atlantic/Azores': 'Azores Standard Time',

    # (UTC-01:00) Cabo Verde Is.
    'Atlantic/Cape_Verde': 'Cape Verde Standard Time',
    'Etc/GMT+1': 'Cape Verde Standard Time',

    # (UTC) Casablanca
    'Africa/Casablanca': 'Morocco Standard Time',
    'Africa/El_Aaiun': 'Morocco Standard Time',

    # (UTC) Coordinated Universal Time
    'America/Danmarkshavn': 'UTC',
    'Etc/GMT': 'UTC',

    # (UTC) Dublin, Edinburgh, Lisbon, London
    'Atlantic/Canary': 'GMT Standard Time',
    'Atlantic/Faeroe': 'GMT Standard Time',
    'Atlantic/Madeira': 'GMT Standard Time',
    'Europe/Dublin': 'GMT Standard Time',
    'Europe/Guernsey': 'GMT Standard Time',
    'Europe/Isle_of_Man': 'GMT Standard Time',
    'Europe/Jersey': 'GMT Standard Time',
    'Europe/Lisbon': 'GMT Standard Time',
    'Europe/London': 'GMT Standard Time',

    # (UTC) Monrovia, Reykjavik
    'Africa/Abidjan': 'Greenwich Standard Time',
    'Africa/Accra': 'Greenwich Standard Time',
    'Africa/Bamako': 'Greenwich Standard Time',
    'Africa/Banjul': 'Greenwich Standard Time',
    'Africa/Bissau': 'Greenwich Standard Time',
    'Africa/Conakry': 'Greenwich Standard Time',
    'Africa/Dakar': 'Greenwich Standard Time',
    'Africa/Freetown': 'Greenwich Standard Time',
    'Africa/Lome': 'Greenwich Standard Time',
    'Africa/Monrovia': 'Greenwich Standard Time',
    'Africa/Nouakchott': 'Greenwich Standard Time',
    'Africa/Ouagadougou': 'Greenwich Standard Time',
    'Africa/Sao_Tome': 'Greenwich Standard Time',
    'Atlantic/Reykjavik': 'Greenwich Standard Time',
    'Atlantic/St_Helena': 'Greenwich Standard Time',

    # (UTC+01:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna
    'Arctic/Longyearbyen': 'W. Europe Standard Time',
    'Europe/Amsterdam': 'W. Europe Standard Time',
    'Europe/Andorra': 'W. Europe Standard Time',
    'Europe/Berlin': 'W. Europe Standard Time',
    'Europe/Busingen': 'W. Europe Standard Time',
    'Europe/Gibraltar': 'W. Europe Standard Time',
    'Europe/Luxembourg': 'W. Europe Standard Time',
    'Europe/Malta': 'W. Europe Standard Time',
    'Europe/Monaco': 'W. Europe Standard Time',
    'Europe/Oslo': 'W. Europe Standard Time',
    'Europe/Rome': 'W. Europe Standard Time',
    'Europe/San_Marino': 'W. Europe Standard Time',
    'Europe/Stockholm': 'W. Europe Standard Time',
    'Europe/Vaduz': 'W. Europe Standard Time',
    'Europe/Vatican': 'W. Europe Standard Time',
    'Europe/Vienna': 'W. Europe Standard Time',
    'Europe/Zurich': 'W. Europe Standard Time',

    # (UTC+01:00) Belgrade, Bratislava, Budapest, Ljubljana, Prague
    'Europe/Belgrade': 'Central Europe Standard Time',
    'Europe/Bratislava': 'Central Europe Standard Time',
    'Europe/Budapest': 'Central Europe Standard Time',
    'Europe/Ljubljana': 'Central Europe Standard Time',
    'Europe/Podgorica': 'Central Europe Standard Time',
    'Europe/Prague': 'Central Europe Standard Time',
    'Europe/Tirane': 'Central Europe Standard Time',

    # (UTC+01:00) Brussels, Copenhagen, Madrid, Paris
    'Africa/Ceuta': 'Romance Standard Time',
    'Europe/Brussels': 'Romance Standard Time',
    'Europe/Copenhagen': 'Romance Standard Time',
    'Europe/Madrid': 'Romance Standard Time',
    'Europe/Paris': 'Romance Standard Time',

    # (UTC+01:00) Sarajevo, Skopje, Warsaw, Zagreb
    'Europe/Sarajevo': 'Central European Standard Time',
    'Europe/Skopje': 'Central European Standard Time',
    'Europe/Warsaw': 'Central European Standard Time',
    'Europe/Zagreb': 'Central European Standard Time',

    # (UTC+01:00) West Central Africa
    'Africa/Algiers': 'W. Central Africa Standard Time',
    'Africa/Bangui': 'W. Central Africa Standard Time',
    'Africa/Brazzaville': 'W. Central Africa Standard Time',
    'Africa/Douala': 'W. Central Africa Standard Time',
    'Africa/Kinshasa': 'W. Central Africa Standard Time',
    'Africa/Lagos': 'W. Central Africa Standard Time',
    'Africa/Libreville': 'W. Central Africa Standard Time',
    'Africa/Luanda': 'W. Central Africa Standard Time',
    'Africa/Malabo': 'W. Central Africa Standard Time',
    'Africa/Ndjamena': 'W. Central Africa Standard Time',
    'Africa/Niamey': 'W. Central Africa Standard Time',
    'Africa/Porto-Novo': 'W. Central Africa Standard Time',
    'Africa/Tunis': 'W. Central Africa Standard Time',
    'Etc/GMT-1': 'W. Central Africa Standard Time',

    # (UTC+01:00) Windhoek
    'Africa/Windhoek': 'Namibia Standard Time',

    # (UTC+02:00) Amman
    'Asia/Amman': 'Jordan Standard Time',

    # (UTC+02:00) Athens, Bucharest
    'Asia/Nicosia': 'GTB Standard Time',
    'Europe/Athens': 'GTB Standard Time',
    'Europe/Bucharest': 'GTB Standard Time',

    # (UTC+02:00) Beirut
    'Asia/Beirut': 'Middle East Standard Time',

    # (UTC+02:00) Cairo
    'Africa/Cairo': 'Egypt Standard Time',

    # (UTC+02:00) Damascus
    'Asia/Damascus': 'Syria Standard Time',

    # (UTC+02:00) E. Europe
    'Europe/Chisinau': 'E. Europe Standard Time',

    # (UTC+02:00) Harare, Pretoria
    'Africa/Blantyre': 'South Africa Standard Time',
    'Africa/Bujumbura': 'South Africa Standard Time',
    'Africa/Gaborone': 'South Africa Standard Time',
    'Africa/Harare': 'South Africa Standard Time',
    'Africa/Johannesburg': 'South Africa Standard Time',
    'Africa/Kigali': 'South Africa Standard Time',
    'Africa/Lubumbashi': 'South Africa Standard Time',
    'Africa/Lusaka': 'South Africa Standard Time',
    'Africa/Maputo': 'South Africa Standard Time',
    'Africa/Maseru': 'South Africa Standard Time',
    'Africa/Mbabane': 'South Africa Standard Time',
    'Etc/GMT-2': 'South Africa Standard Time',

    # (UTC+02:00) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius
    'Europe/Helsinki': 'FLE Standard Time',
    'Europe/Kiev': 'FLE Standard Time',
    'Europe/Mariehamn': 'FLE Standard Time',
    'Europe/Riga': 'FLE Standard Time',
    'Europe/Sofia': 'FLE Standard Time',
    'Europe/Tallinn': 'FLE Standard Time',
    'Europe/Uzhgorod': 'FLE Standard Time',
    'Europe/Vilnius': 'FLE Standard Time',
    'Europe/Zaporozhye': 'FLE Standard Time',

    # (UTC+02:00) Istanbul
    'Europe/Istanbul': 'Turkey Standard Time',

    # (UTC+02:00) Jerusalem
    'Asia/Jerusalem': 'Israel Standard Time',

    # (UTC+02:00) Kaliningrad (RTZ 1)
    'Europe/Kaliningrad': 'Kaliningrad Standard Time',

    # (UTC+02:00) Tripoli
    'Africa/Tripoli': 'Libya Standard Time',

    # (UTC+03:00) Baghdad
    'Asia/Baghdad': 'Arabic Standard Time',

    # (UTC+03:00) Kuwait, Riyadh
    'Asia/Aden': 'Arab Standard Time',
    'Asia/Bahrain': 'Arab Standard Time',
    'Asia/Kuwait': 'Arab Standard Time',
    'Asia/Qatar': 'Arab Standard Time',
    'Asia/Riyadh': 'Arab Standard Time',

    # (UTC+03:00) Minsk
    'Europe/Minsk': 'Belarus Standard Time',

    # (UTC+03:00) Moscow, St. Petersburg, Volgograd (RTZ 2)
    'Europe/Moscow': 'Russian Standard Time',
    'Europe/Simferopol': 'Russian Standard Time',
    'Europe/Volgograd': 'Russian Standard Time',

    # (UTC+03:00) Nairobi
    'Africa/Addis_Ababa': 'E. Africa Standard Time',
    'Africa/Asmera': 'E. Africa Standard Time',
    'Africa/Dar_es_Salaam': 'E. Africa Standard Time',
    'Africa/Djibouti': 'E. Africa Standard Time',
    'Africa/Juba': 'E. Africa Standard Time',
    'Africa/Kampala': 'E. Africa Standard Time',
    'Africa/Khartoum': 'E. Africa Standard Time',
    'Africa/Mogadishu': 'E. Africa Standard Time',
    'Africa/Nairobi': 'E. Africa Standard Time',
    'Antarctica/Syowa': 'E. Africa Standard Time',
    'Etc/GMT-3': 'E. Africa Standard Time',
    'Indian/Antananarivo': 'E. Africa Standard Time',
    'Indian/Comoro': 'E. Africa Standard Time',
    'Indian/Mayotte': 'E. Africa Standard Time',

    # (UTC+03:30) Tehran
    'Asia/Tehran': 'Iran Standard Time',

    # (UTC+04:00) Abu Dhabi, Muscat
    'Asia/Dubai': 'Arabian Standard Time',
    'Asia/Muscat': 'Arabian Standard Time',
    'Etc/GMT-4': 'Arabian Standard Time',

    # (UTC+04:00) Baku
    'Asia/Baku': 'Azerbaijan Standard Time',

    # (UTC+04:00) Izhevsk, Samara (RTZ 3)
    'Europe/Samara': 'Russia Time Zone 3',

    # (UTC+04:00) Port Louis
    'Indian/Mahe': 'Mauritius Standard Time',
    'Indian/Mauritius': 'Mauritius Standard Time',
    'Indian/Reunion': 'Mauritius Standard Time',

    # (UTC+04:00) Tbilisi
    'Asia/Tbilisi': 'Georgian Standard Time',

    # (UTC+04:00) Yerevan
    'Asia/Yerevan': 'Caucasus Standard Time',

    # (UTC+04:30) Kabul
    'Asia/Kabul': 'Afghanistan Standard Time',

    # (UTC+05:00) Ashgabat, Tashkent
    'Antarctica/Mawson': 'West Asia Standard Time',
    'Asia/Aqtau': 'West Asia Standard Time',
    'Asia/Aqtobe': 'West Asia Standard Time',
    'Asia/Ashgabat': 'West Asia Standard Time',
    'Asia/Dushanbe': 'West Asia Standard Time',
    'Asia/Oral': 'West Asia Standard Time',
    'Asia/Samarkand': 'West Asia Standard Time',
    'Asia/Tashkent': 'West Asia Standard Time',
    'Etc/GMT-5': 'West Asia Standard Time',
    'Indian/Kerguelen': 'West Asia Standard Time',
    'Indian/Maldives': 'West Asia Standard Time',

    # (UTC+05:00) Ekaterinburg (RTZ 4)
    'Asia/Yekaterinburg': 'Ekaterinburg Standard Time',

    # (UTC+05:00) Islamabad, Karachi
    'Asia/Karachi': 'Pakistan Standard Time',

    # (UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi
    'Asia/Calcutta': 'India Standard Time',

    # (UTC+05:30) Sri Jayawardenepura
    'Asia/Colombo': 'Sri Lanka Standard Time',

    # (UTC+05:45) Kathmandu
    'Asia/Katmandu': 'Nepal Standard Time',

    # (UTC+06:00) Astana
    'Antarctica/Vostok': 'Central Asia Standard Time',
    'Asia/Almaty': 'Central Asia Standard Time',
    'Asia/Bishkek': 'Central Asia Standard Time',
    'Asia/Qyzylorda': 'Central Asia Standard Time',
    'Asia/Urumqi': 'Central Asia Standard Time',
    'Etc/GMT-6': 'Central Asia Standard Time',
    'Indian/Chagos': 'Central Asia Standard Time',

    # (UTC+06:00) Dhaka
    'Asia/Dhaka': 'Bangladesh Standard Time',
    'Asia/Thimphu': 'Bangladesh Standard Time',

    # (UTC+06:00) Novosibirsk (RTZ 5)
    'Asia/Novosibirsk': 'N. Central Asia Standard Time',
    'Asia/Omsk': 'N. Central Asia Standard Time',

    # (UTC+06:30) Yangon (Rangoon)
    'Asia/Rangoon': 'Myanmar Standard Time',
    'Indian/Cocos': 'Myanmar Standard Time',

    # (UTC+07:00) Bangkok, Hanoi, Jakarta
    'Antarctica/Davis': 'SE Asia Standard Time',
    'Asia/Bangkok': 'SE Asia Standard Time',
    'Asia/Jakarta': 'SE Asia Standard Time',
    'Asia/Phnom_Penh': 'SE Asia Standard Time',
    'Asia/Pontianak': 'SE Asia Standard Time',
    'Asia/Saigon': 'SE Asia Standard Time',
    'Asia/Vientiane': 'SE Asia Standard Time',
    'Etc/GMT-7': 'SE Asia Standard Time',
    'Indian/Christmas': 'SE Asia Standard Time',

    # (UTC+07:00) Krasnoyarsk (RTZ 6)
    'Asia/Krasnoyarsk': 'North Asia Standard Time',
    'Asia/Novokuznetsk': 'North Asia Standard Time',

    # (UTC+08:00) Beijing, Chongqing, Hong Kong, Urumqi
    'Asia/Hong_Kong': 'China Standard Time',
    'Asia/Macau': 'China Standard Time',
    'Asia/Shanghai': 'China Standard Time',

    # (UTC+08:00) Irkutsk (RTZ 7)
    'Asia/Irkutsk': 'North Asia East Standard Time',

    # (UTC+08:00) Kuala Lumpur, Singapore
    'Asia/Brunei': 'Singapore Standard Time',
    'Asia/Kuala_Lumpur': 'Singapore Standard Time',
    'Asia/Kuching': 'Singapore Standard Time',
    'Asia/Makassar': 'Singapore Standard Time',
    'Asia/Manila': 'Singapore Standard Time',
    'Asia/Singapore': 'Singapore Standard Time',
    'Etc/GMT-8': 'Singapore Standard Time',

    # (UTC+08:00) Perth
    'Antarctica/Casey': 'W. Australia Standard Time',
    'Australia/Perth': 'W. Australia Standard Time',

    # (UTC+08:00) Taipei
    'Asia/Taipei': 'Taipei Standard Time',

    # (UTC+08:00) Ulaanbaatar
    'Asia/Choibalsan': 'Ulaanbaatar Standard Time',
    'Asia/Ulaanbaatar': 'Ulaanbaatar Standard Time',

    # (UTC+08:30) Pyongyang
    'Asia/Pyongyang': 'North Korea Standard Time',

    # (UTC+09:00) Osaka, Sapporo, Tokyo
    'Asia/Dili': 'Tokyo Standard Time',
    'Asia/Jayapura': 'Tokyo Standard Time',
    'Asia/Tokyo': 'Tokyo Standard Time',
    'Etc/GMT-9': 'Tokyo Standard Time',
    'Pacific/Palau': 'Tokyo Standard Time',

    # (UTC+09:00) Seoul
    'Asia/Seoul': 'Korea Standard Time',

    # (UTC+09:00) Yakutsk (RTZ 8)
    'Asia/Chita': 'Yakutsk Standard Time',
    'Asia/Khandyga': 'Yakutsk Standard Time',
    'Asia/Yakutsk': 'Yakutsk Standard Time',

    # (UTC+09:30) Adelaide
    'Australia/Adelaide': 'Cen. Australia Standard Time',
    'Australia/Broken_Hill': 'Cen. Australia Standard Time',

    # (UTC+09:30) Darwin
    'Australia/Darwin': 'AUS Central Standard Time',

    # (UTC+10:00) Brisbane
    'Australia/Brisbane': 'E. Australia Standard Time',
    'Australia/Lindeman': 'E. Australia Standard Time',

    # (UTC+10:00) Canberra, Melbourne, Sydney
    'Australia/Melbourne': 'AUS Eastern Standard Time',
    'Australia/Sydney': 'AUS Eastern Standard Time',

    # (UTC+10:00) Guam, Port Moresby
    'Antarctica/DumontDUrville': 'West Pacific Standard Time',
    'Etc/GMT-10': 'West Pacific Standard Time',
    'Pacific/Guam': 'West Pacific Standard Time',
    'Pacific/Port_Moresby': 'West Pacific Standard Time',
    'Pacific/Saipan': 'West Pacific Standard Time',
    'Pacific/Truk': 'West Pacific Standard Time',

    # (UTC+10:00) Hobart
    'Australia/Currie': 'Tasmania Standard Time',
    'Australia/Hobart': 'Tasmania Standard Time',

    # (UTC+10:00) Magadan
    'Asia/Magadan': 'Magadan Standard Time',

    # (UTC+10:00) Vladivostok, Magadan (RTZ 9)
    'Asia/Sakhalin': 'Vladivostok Standard Time',
    'Asia/Ust-Nera': 'Vladivostok Standard Time',
    'Asia/Vladivostok': 'Vladivostok Standard Time',

    # (UTC+11:00) Chokurdakh (RTZ 10)
    'Asia/Srednekolymsk': 'Russia Time Zone 10',

    # (UTC+11:00) Solomon Is., New Caledonia
    'Antarctica/Macquarie': 'Central Pacific Standard Time',
    'Etc/GMT-11': 'Central Pacific Standard Time',
    'Pacific/Bougainville': 'Central Pacific Standard Time',
    'Pacific/Efate': 'Central Pacific Standard Time',
    'Pacific/Guadalcanal': 'Central Pacific Standard Time',
    'Pacific/Kosrae': 'Central Pacific Standard Time',
    'Pacific/Norfolk': 'Central Pacific Standard Time',
    'Pacific/Noumea': 'Central Pacific Standard Time',
    'Pacific/Ponape': 'Central Pacific Standard Time',

    # (UTC+12:00) Anadyr, Petropavlovsk-Kamchatsky (RTZ 11)
    'Asia/Anadyr': 'Russia Time Zone 11',
    'Asia/Kamchatka': 'Russia Time Zone 11',

    # (UTC+12:00) Auckland, Wellington
    'Antarctica/McMurdo': 'New Zealand Standard Time',
    'Pacific/Auckland': 'New Zealand Standard Time',

    # (UTC+12:00) Coordinated Universal Time+12
    'Etc/GMT-12': 'UTC+12',
    'Pacific/Funafuti': 'UTC+12',
    'Pacific/Kwajalein': 'UTC+12',
    'Pacific/Majuro': 'UTC+12',
    'Pacific/Nauru': 'UTC+12',
    'Pacific/Tarawa': 'UTC+12',
    'Pacific/Wake': 'UTC+12',
    'Pacific/Wallis': 'UTC+12',

    # (UTC+12:00) Fiji
    'Pacific/Fiji': 'Fiji Standard Time',

    # (UTC+13:00) Nuku'alofa
    'Etc/GMT-13': 'Tonga Standard Time',
    'Pacific/Enderbury': 'Tonga Standard Time',
    'Pacific/Fakaofo': 'Tonga Standard Time',
    'Pacific/Tongatapu': 'Tonga Standard Time',

    # (UTC+13:00) Samoa
    'Pacific/Apia': 'Samoa Standard Time',

    # (UTC+14:00) Kiritimati Island

    'Etc/GMT-14': 'Line Islands Standard Time',
    'Pacific/Kiritimati': 'Line Islands Standard Time',
}
