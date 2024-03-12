# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os

import pytest  # type: ignore
import six

from google.auth import _service_account_info
from google.auth import crypt


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SERVICE_ACCOUNT_JSON_FILE = os.path.join(DATA_DIR, "service_account.json")
GDCH_SERVICE_ACCOUNT_JSON_FILE = os.path.join(DATA_DIR, "gdch_service_account.json")

with open(SERVICE_ACCOUNT_JSON_FILE, "r") as fh:
    SERVICE_ACCOUNT_INFO = json.load(fh)

with open(GDCH_SERVICE_ACCOUNT_JSON_FILE, "r") as fh:
    GDCH_SERVICE_ACCOUNT_INFO = json.load(fh)


def test_from_dict():
    signer = _service_account_info.from_dict(SERVICE_ACCOUNT_INFO)
    assert isinstance(signer, crypt.RSASigner)
    assert signer.key_id == SERVICE_ACCOUNT_INFO["private_key_id"]


def test_from_dict_es256_signer():
    signer = _service_account_info.from_dict(
        GDCH_SERVICE_ACCOUNT_INFO, use_rsa_signer=False
    )
    assert isinstance(signer, crypt.ES256Signer)
    assert signer.key_id == GDCH_SERVICE_ACCOUNT_INFO["private_key_id"]


def test_from_dict_bad_private_key():
    info = SERVICE_ACCOUNT_INFO.copy()
    info["private_key"] = "garbage"

    with pytest.raises(ValueError) as excinfo:
        _service_account_info.from_dict(info)

    assert excinfo.match(r"key")


def test_from_dict_bad_format():
    with pytest.raises(ValueError) as excinfo:
        _service_account_info.from_dict({}, require=("meep",))

    assert excinfo.match(r"missing fields")


def test_from_filename():
    info, signer = _service_account_info.from_filename(SERVICE_ACCOUNT_JSON_FILE)

    for key, value in six.iteritems(SERVICE_ACCOUNT_INFO):
        assert info[key] == value

    assert isinstance(signer, crypt.RSASigner)
    assert signer.key_id == SERVICE_ACCOUNT_INFO["private_key_id"]


def test_from_filename_es256_signer():
    _, signer = _service_account_info.from_filename(
        GDCH_SERVICE_ACCOUNT_JSON_FILE, use_rsa_signer=False
    )

    assert isinstance(signer, crypt.ES256Signer)
    assert signer.key_id == GDCH_SERVICE_ACCOUNT_INFO["private_key_id"]
