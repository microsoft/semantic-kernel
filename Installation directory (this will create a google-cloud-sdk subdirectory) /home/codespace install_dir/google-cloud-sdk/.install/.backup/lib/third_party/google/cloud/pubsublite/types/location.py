# Copyright 2020 Google LLC
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

from typing import NamedTuple

from google.api_core.exceptions import InvalidArgument


class CloudRegion(NamedTuple):
    name: str

    def __str__(self):
        return self.name

    @staticmethod
    def parse(to_parse: str):
        splits = to_parse.split("-")
        if len(splits) != 2:
            raise InvalidArgument("Invalid region name: " + to_parse)
        return CloudRegion(name=splits[0] + "-" + splits[1])

    @property
    def region(self):
        return self


class CloudZone(NamedTuple):
    region: CloudRegion
    zone_id: str

    def __str__(self):
        return f"{self.region.name}-{self.zone_id}"

    @staticmethod
    def parse(to_parse: str):
        splits = to_parse.split("-")
        if len(splits) != 3 or len(splits[2]) != 1:
            raise InvalidArgument("Invalid zone name: " + to_parse)
        region = CloudRegion(name=splits[0] + "-" + splits[1])
        return CloudZone(region, zone_id=splits[2])
