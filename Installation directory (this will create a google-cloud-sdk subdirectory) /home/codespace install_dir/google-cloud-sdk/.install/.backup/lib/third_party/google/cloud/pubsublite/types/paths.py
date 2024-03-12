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

from typing import NamedTuple, Union

from google.api_core.exceptions import InvalidArgument

from google.cloud.pubsublite.types.location import CloudZone, CloudRegion


def _parse_location(to_parse: str) -> Union[CloudRegion, CloudZone]:
    try:
        return CloudZone.parse(to_parse)
    except InvalidArgument:
        pass
    try:
        return CloudRegion.parse(to_parse)
    except InvalidArgument:
        pass
    raise InvalidArgument("Invalid location name: " + to_parse)


class LocationPath(NamedTuple):
    project: Union[int, str]
    location: Union[CloudRegion, CloudZone]

    def __str__(self):
        return f"projects/{self.project}/locations/{self.location}"

    @staticmethod
    def parse(to_parse: str) -> "LocationPath":
        splits = to_parse.split("/")
        if len(splits) != 6 or splits[0] != "projects" or splits[2] != "locations":
            raise InvalidArgument(
                "Location path must be formatted like projects/{project_number}/locations/{location} but was instead "
                + to_parse
            )
        return LocationPath(splits[1], _parse_location(splits[3]))


class TopicPath(NamedTuple):
    project: Union[int, str]
    location: Union[CloudRegion, CloudZone]
    name: str

    def __str__(self):
        return f"projects/{self.project}/locations/{self.location}/topics/{self.name}"

    def to_location_path(self):
        return LocationPath(self.project, self.location)

    @staticmethod
    def parse(to_parse: str) -> "TopicPath":
        splits = to_parse.split("/")
        if (
            len(splits) != 6
            or splits[0] != "projects"
            or splits[2] != "locations"
            or splits[4] != "topics"
        ):
            raise InvalidArgument(
                "Topic path must be formatted like projects/{project_number}/locations/{location}/topics/{name} but was instead "
                + to_parse
            )
        return TopicPath(splits[1], _parse_location(splits[3]), splits[5])


class SubscriptionPath(NamedTuple):
    project: Union[int, str]
    location: Union[CloudRegion, CloudZone]
    name: str

    def __str__(self):
        return f"projects/{self.project}/locations/{self.location}/subscriptions/{self.name}"

    def to_location_path(self):
        return LocationPath(self.project, self.location)

    @staticmethod
    def parse(to_parse: str) -> "SubscriptionPath":
        splits = to_parse.split("/")
        if (
            len(splits) != 6
            or splits[0] != "projects"
            or splits[2] != "locations"
            or splits[4] != "subscriptions"
        ):
            raise InvalidArgument(
                "Subscription path must be formatted like projects/{project_number}/locations/{location}/subscriptions/{name} but was instead "
                + to_parse
            )
        return SubscriptionPath(splits[1], _parse_location(splits[3]), splits[5])


class ReservationPath(NamedTuple):
    project: Union[int, str]
    location: CloudRegion
    name: str

    def __str__(self):
        return f"projects/{self.project}/locations/{self.location}/reservations/{self.name}"

    def to_location_path(self):
        return LocationPath(self.project, self.location)

    @staticmethod
    def parse(to_parse: str) -> "ReservationPath":
        splits = to_parse.split("/")
        if (
            len(splits) != 6
            or splits[0] != "projects"
            or splits[2] != "locations"
            or splits[4] != "reservations"
        ):
            raise InvalidArgument(
                "Reservation path must be formatted like projects/{project_number}/locations/{location}/reservations/{name} but was instead "
                + to_parse
            )
        return ReservationPath(splits[1], CloudRegion.parse(splits[3]), splits[5])
