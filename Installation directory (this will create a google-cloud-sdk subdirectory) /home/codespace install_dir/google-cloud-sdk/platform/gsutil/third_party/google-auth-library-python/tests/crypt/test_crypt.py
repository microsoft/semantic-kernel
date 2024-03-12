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

import os

from google.auth import crypt


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# To generate privatekey.pem, privatekey.pub, and public_cert.pem:
#   $ openssl req -new -newkey rsa:1024 -x509 -nodes -out public_cert.pem \
#   >    -keyout privatekey.pem
#   $ openssl rsa -in privatekey.pem -pubout -out privatekey.pub

with open(os.path.join(DATA_DIR, "privatekey.pem"), "rb") as fh:
    PRIVATE_KEY_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "public_cert.pem"), "rb") as fh:
    PUBLIC_CERT_BYTES = fh.read()

# To generate other_cert.pem:
#   $ openssl req -new -newkey rsa:1024 -x509 -nodes -out other_cert.pem

with open(os.path.join(DATA_DIR, "other_cert.pem"), "rb") as fh:
    OTHER_CERT_BYTES = fh.read()


def test_verify_signature():
    to_sign = b"foo"
    signer = crypt.RSASigner.from_string(PRIVATE_KEY_BYTES)
    signature = signer.sign(to_sign)

    assert crypt.verify_signature(to_sign, signature, PUBLIC_CERT_BYTES)

    # List of certs
    assert crypt.verify_signature(
        to_sign, signature, [OTHER_CERT_BYTES, PUBLIC_CERT_BYTES]
    )


def test_verify_signature_failure():
    to_sign = b"foo"
    signer = crypt.RSASigner.from_string(PRIVATE_KEY_BYTES)
    signature = signer.sign(to_sign)

    assert not crypt.verify_signature(to_sign, signature, OTHER_CERT_BYTES)
