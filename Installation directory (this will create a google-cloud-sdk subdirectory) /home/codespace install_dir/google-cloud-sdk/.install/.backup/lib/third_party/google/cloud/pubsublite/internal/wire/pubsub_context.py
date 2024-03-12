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

from base64 import b64encode
from typing import Mapping, Optional, NamedTuple

import logging
import pkg_resources
from cloudsdk.google.protobuf import struct_pb2  # pytype: disable=pyi-error


_LOGGER = logging.getLogger(__name__)


class _Semver(NamedTuple):
    major: int
    minor: int


def _version() -> _Semver:
    try:
        version = pkg_resources.get_distribution("google-cloud-pubsublite").version
    except pkg_resources.DistributionNotFound:
        _LOGGER.info(
            "Failed to extract the google-cloud-pubsublite semver version. DistributionNotFound."
        )
        return _Semver(0, 0)
    splits = version.split(".")
    if len(splits) != 3:
        _LOGGER.info(f"Failed to extract semver from {version}.")
        return _Semver(0, 0)
    return _Semver(int(splits[0]), int(splits[1]))


def pubsub_context(framework: Optional[str] = None) -> Mapping[str, str]:
    """Construct the pubsub context mapping for the given framework."""
    context = struct_pb2.Struct()
    context.fields["language"].string_value = "PYTHON"
    if framework:
        context.fields["framework"].string_value = framework
    version = _version()
    context.fields["major_version"].number_value = version.major
    context.fields["minor_version"].number_value = version.minor
    encoded = b64encode(context.SerializeToString()).decode("utf-8")
    return {"x-goog-pubsub-context": encoded}
