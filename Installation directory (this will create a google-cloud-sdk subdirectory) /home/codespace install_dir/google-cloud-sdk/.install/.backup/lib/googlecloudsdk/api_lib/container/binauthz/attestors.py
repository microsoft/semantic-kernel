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

"""API helpers for interacting with attestors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import util
from googlecloudsdk.command_lib.container.binauthz import exceptions
from googlecloudsdk.command_lib.kms import maps as kms_maps


class Client(object):
  """A client for interacting with attestors."""

  def __init__(self, api_version=None):
    self.client = apis.GetClientInstance(api_version)
    self.messages = apis.GetMessagesModule(api_version)
    self.api_version = api_version

  def Get(self, attestor_ref):
    """Get the specified attestor."""
    return self.client.projects_attestors.Get(
        self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
            name=attestor_ref.RelativeName(),
        ))

  def List(self, project_ref, limit=None, page_size=None):
    """List the attestors associated with the current project."""
    return list_pager.YieldFromList(
        self.client.projects_attestors,
        self.messages.BinaryauthorizationProjectsAttestorsListRequest(
            parent=project_ref.RelativeName(),),
        batch_size=page_size or 100,  # Default batch_size.
        limit=limit,
        field='attestors',
        batch_size_attribute='pageSize')

  def _GetNoteClass(self):
    return (self.messages.UserOwnedGrafeasNote
            if self.api_version == apis.V1 else
            self.messages.UserOwnedDrydockNote)

  def GetNotePropertyName(self):
    return ('userOwnedGrafeasNote'
            if self.api_version == apis.V1 else
            'userOwnedDrydockNote')

  def GetNoteAttr(self, attestor):
    """Return the Attestor's version-dependent Note attribute."""
    if self.api_version == apis.V1:
      return attestor.userOwnedGrafeasNote
    else:
      return attestor.userOwnedDrydockNote

  def Create(self, attestor_ref, note_ref, description=None):
    """Create an attestors associated with the current project."""
    project_ref = attestor_ref.Parent(util.PROJECTS_COLLECTION)
    return self.client.projects_attestors.Create(
        self.messages.BinaryauthorizationProjectsAttestorsCreateRequest(
            attestor=self.messages.Attestor(
                name=attestor_ref.RelativeName(),
                description=description,
                **{self.GetNotePropertyName(): self._GetNoteClass()(
                    noteReference=note_ref.RelativeName(),
                )}
            ),
            attestorId=attestor_ref.Name(),
            parent=project_ref.RelativeName(),
        ))

  def AddPgpKey(self, attestor_ref, pgp_pubkey_content, comment=None):
    """Add a PGP key to an attestor.

    Args:
      attestor_ref: ResourceSpec, The attestor to be updated.
      pgp_pubkey_content: The contents of the PGP public key file.
      comment: The comment on the public key.

    Returns:
      The added public key.

    Raises:
      AlreadyExistsError: If a public key with the same key content was found on
          the attestor.
    """
    attestor = self.Get(attestor_ref)

    existing_pub_keys = set(
        public_key.asciiArmoredPgpPublicKey
        for public_key in self.GetNoteAttr(attestor).publicKeys)
    if pgp_pubkey_content in existing_pub_keys:
      raise exceptions.AlreadyExistsError(
          'Provided public key already present on attestor [{}]'.format(
              attestor.name))

    existing_ids = set(
        public_key.id
        for public_key in self.GetNoteAttr(attestor).publicKeys)

    self.GetNoteAttr(attestor).publicKeys.append(
        self.messages.AttestorPublicKey(
            asciiArmoredPgpPublicKey=pgp_pubkey_content,
            comment=comment))

    updated_attestor = self.client.projects_attestors.Update(attestor)

    return next(
        public_key
        for public_key in self.GetNoteAttr(updated_attestor).publicKeys
        if public_key.id not in existing_ids)

  def AddPkixKey(self, attestor_ref, pkix_pubkey_content, pkix_sig_algorithm,
                 id_override=None, comment=None):
    """Add a key to an attestor.

    Args:
      attestor_ref: ResourceSpec, The attestor to be updated.
      pkix_pubkey_content: The PEM-encoded PKIX public key.
      pkix_sig_algorithm: The PKIX public key signature algorithm.
      id_override: If provided, the key ID to use instead of the API-generated
          one.
      comment: The comment on the public key.

    Returns:
      The added public key.

    Raises:
      AlreadyExistsError: If a public key with the same key content was found on
          the attestor.
    """
    attestor = self.Get(attestor_ref)

    existing_ids = set(
        public_key.id
        for public_key in self.GetNoteAttr(attestor).publicKeys)
    if id_override is not None and id_override in existing_ids:
      raise exceptions.AlreadyExistsError(
          'Public key with ID [{}] already present on attestor [{}]'.format(
              id_override, attestor.name))

    self.GetNoteAttr(attestor).publicKeys.append(
        self.messages.AttestorPublicKey(
            id=id_override,
            pkixPublicKey=self.messages.PkixPublicKey(
                publicKeyPem=pkix_pubkey_content,
                signatureAlgorithm=pkix_sig_algorithm),
            comment=comment))

    updated_attestor = self.client.projects_attestors.Update(attestor)

    return next(
        public_key
        for public_key in self.GetNoteAttr(updated_attestor).publicKeys
        if public_key.id not in existing_ids)

  def RemoveKey(self, attestor_ref, pubkey_id):
    """Remove a key on an attestor.

    Args:
      attestor_ref: ResourceSpec, The attestor to be updated.
      pubkey_id: The ID of the key to remove.

    Raises:
      NotFoundError: If an expected public key could not be located by ID.
    """
    attestor = self.Get(attestor_ref)

    existing_ids = set(
        public_key.id
        for public_key in self.GetNoteAttr(attestor).publicKeys)
    if pubkey_id not in existing_ids:
      raise exceptions.NotFoundError(
          'No matching public key found on attestor [{}]'.format(
              attestor.name))

    self.GetNoteAttr(attestor).publicKeys = [
        public_key
        for public_key in self.GetNoteAttr(attestor).publicKeys
        if public_key.id != pubkey_id]

    self.client.projects_attestors.Update(attestor)

  def UpdateKey(
      self, attestor_ref, pubkey_id, pgp_pubkey_content=None, comment=None):
    """Update a key on an attestor.

    Args:
      attestor_ref: ResourceSpec, The attestor to be updated.
      pubkey_id: The ID of the key to update.
      pgp_pubkey_content: The contents of the public key file.
      comment: The comment on the public key.

    Returns:
      The updated public key.

    Raises:
      NotFoundError: If an expected public key could not be located by ID.
      InvalidStateError: If multiple public keys matched the provided ID.
      InvalidArgumentError: If a non-PGP key is updated with pgp_pubkey_content.
    """
    attestor = self.Get(attestor_ref)

    existing_keys = [
        public_key
        for public_key in self.GetNoteAttr(attestor).publicKeys
        if public_key.id == pubkey_id]

    if not existing_keys:
      raise exceptions.NotFoundError(
          'No matching public key found on attestor [{}]'.format(
              attestor.name))
    if len(existing_keys) > 1:
      raise exceptions.InvalidStateError(
          'Multiple matching public keys found on attestor [{}]'.format(
              attestor.name))

    existing_key = existing_keys[0]
    if pgp_pubkey_content is not None:
      if not existing_key.asciiArmoredPgpPublicKey:
        raise exceptions.InvalidArgumentError(
            'Cannot update a non-PGP PublicKey with a PGP public key')
      existing_key.asciiArmoredPgpPublicKey = pgp_pubkey_content
    if comment is not None:
      existing_key.comment = comment

    updated_attestor = self.client.projects_attestors.Update(attestor)

    return next(
        public_key
        for public_key in self.GetNoteAttr(updated_attestor).publicKeys
        if public_key.id == pubkey_id)

  def Update(self, attestor_ref, description=None):
    """Update an attestor.

    Args:
      attestor_ref: ResourceSpec, The attestor to be updated.
      description: string, If provided, the new attestor description.

    Returns:
      The updated attestor.
    """
    attestor = self.Get(attestor_ref)

    if description is not None:
      attestor.description = description

    return self.client.projects_attestors.Update(attestor)

  def Delete(self, attestor_ref):
    """Delete the specified attestor."""
    req = self.messages.BinaryauthorizationProjectsAttestorsDeleteRequest(
        name=attestor_ref.RelativeName(),
    )

    self.client.projects_attestors.Delete(req)

  def ConvertFromKmsSignatureAlgorithm(self, kms_algorithm):
    """Convert a KMS SignatureAlgorithm into a Binauthz SignatureAlgorithm."""
    binauthz_enum = self.messages.PkixPublicKey.SignatureAlgorithmValueValuesEnum
    kms_enum = kms_maps.ALGORITHM_ENUM
    alg_map = {
        kms_enum.RSA_SIGN_PSS_2048_SHA256.name:
            binauthz_enum.RSA_PSS_2048_SHA256,
        kms_enum.RSA_SIGN_PSS_3072_SHA256.name:
            binauthz_enum.RSA_PSS_3072_SHA256,
        kms_enum.RSA_SIGN_PSS_4096_SHA256.name:
            binauthz_enum.RSA_PSS_4096_SHA256,
        kms_enum.RSA_SIGN_PSS_4096_SHA512.name:
            binauthz_enum.RSA_PSS_4096_SHA512,
        kms_enum.RSA_SIGN_PKCS1_2048_SHA256.name:
            binauthz_enum.RSA_SIGN_PKCS1_2048_SHA256,
        kms_enum.RSA_SIGN_PKCS1_3072_SHA256.name:
            binauthz_enum.RSA_SIGN_PKCS1_3072_SHA256,
        kms_enum.RSA_SIGN_PKCS1_4096_SHA256.name:
            binauthz_enum.RSA_SIGN_PKCS1_4096_SHA256,
        kms_enum.RSA_SIGN_PKCS1_4096_SHA512.name:
            binauthz_enum.RSA_SIGN_PKCS1_4096_SHA512,
        kms_enum.EC_SIGN_P256_SHA256.name:
            binauthz_enum.ECDSA_P256_SHA256,
        kms_enum.EC_SIGN_P384_SHA384.name:
            binauthz_enum.ECDSA_P384_SHA384,
    }
    try:
      return alg_map[kms_algorithm.name]
    except KeyError:
      raise exceptions.InvalidArgumentError(
          'Unsupported PkixPublicKey signature algorithm: "{}"'.format(
              kms_algorithm.name))
