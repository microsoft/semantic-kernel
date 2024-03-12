# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""The public key management group for attestors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class PublicKeys(base.Group):
  r"""Create and manage public keys associated with Attestation Authorities.

  ## BACKGROUND

  PGP is an encryption standard used by Binary Authorization to create and
  verify attestations. A PGP identity is encapsulated by a "key" which can be
  used to sign arbitrary data and/or verify signatures to be valid. As with
  other asymmetric key cryptosystems, PGP keys have a "public" part and a
  "private" part.

  ## PGP KEY STRUCTURE

  An important feature of PGP keys is that they are hierarchical: Every "PGP
  key" is composed of a "primary" key pair and zero or more "subkey" pairs
  certified by the primary. These key pairs are collectively known as the "PGP
  key." The "public" part of this PGP key contains the public keys of all the
  constituent keys as well as all associated metadata (e.g. an email address).
  And, as might be expected, the "private" part of the PGP key contains all
  constituent private keys and metadata.

  One property of subkeys is that they may be marked as "revoked" if they are
  compromised or otherwise need to be retired. This does not remove the subkey
  from the PGP key but simply adds metadata indicating this revocation. The
  primary key pair cannot be revoked by this same mechanism.

  ### COMMON KEY STRUCTURE

  The most common key structure is to have the primary key pair only used to
  certify subkey pairs while the subkeys are used to encrypt and sign as
  necessary. This allows the PGP key as a whole to act as a durable identity
  even if an encryption key is used improperly or a signing key is compromised.

  ## USAGE IN BINARY AUTHORIZATION

  - Authorities hold a set of PGP public keys that are used to verify
    attestations.
    - These must be submitted in ASCII-armored format. With GPG, this is
      accomplished by adding the `--armor` flag to the export command.
  - If any of the public keys held by an attestor verify a given attestation,
    then the attestor considers that attestation to be valid (see gcloud alpha
    container binauthz attestations create help for more details).
    - As a result, the compromise of any constituent private key means that the
      attestor is at risk. The compromised subkey should be revoked and the PGP
      key re-uploaded or removed from the attestor.

  ## EXAMPLES

  GPG is a common tool that implements the PGP standard.
  - For general `gpg` usage examples, see gcloud alpha container binauthz help.
  - For more detailed and complete documentation, see the GPG manual:
    https://gnupg.org/documentation/manuals.html

  To get the fingerprint of the public key:

      ```sh
      $ gpg \
            --with-colons \
            --with-fingerprint \
            --force-v4-certs \
            --list-keys \
            "${ATTESTING_USER}" | grep fpr | cut --delimiter=':' --fields 10
      ```

  To export a public key:

      ```sh
      $ gpg \
            --armor \
            --export "${FINGERPRINT}" \
            --output public_key1.pgp
      ```

  To add your new key to the attestor:

      ```sh
      $ {command} add \
            --attestor my_attestor \
            --pgp-public-key-file=public_key1.pgp
      ```

  To add a subkey to your PGP key:

      ```sh
      $ gpg \
            --quick-add-key ${FINGERPRINT} \
            default \
            sign
      ... FOLLOW PROMPTS ...
      ```

  To revoke a subkey from your PGP key:

      ```sh
      $ gpg \
            --edit-key ${FINGERPRINT}
      ... SNIP ...

      sec  rsa2048/8C124F0F782DA097
           created: 2018-01-01  expires: never       usage: SCEA
           trust: ultimate      validity: ultimate
      ssb  rsa3072/C9597E8F28359AE3
           created: 2018-01-01  expires: never       usage: E
      [ultimate] (1). User <attesting_user@example.com>

      gpg> key C9597E8F28359AE3
      ... SNIP ...
      gpg> revkey
      ... FOLLOW PROMPTS ...

      ```

  To update the modified PGP key on the attestor:

      ```sh
      $ {command} update \
            ${FINGERPRINT} \
            --attestor=my_attestor \
            --pgp-public-key-file=public_key1_updated.pgp
      ```

  To remove this new key from the attestor:

      ```sh
      $ {command} remove \
            ${FINGERPRINT} \
            --attestor my_attestor
      ```
  """
