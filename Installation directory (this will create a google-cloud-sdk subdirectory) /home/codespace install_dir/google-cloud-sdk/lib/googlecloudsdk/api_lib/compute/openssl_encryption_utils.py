# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Utilities for encryption functions using openssl."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import subprocess
import tempfile

from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.core import log

import six


DEFAULT_KEY_LENGTH = 2048


class OpenSSLException(exceptions.Error):
  """Exception for problems with OpenSSL functions."""


def StripKey(key):
  """Returns key with header, footer and all newlines removed."""
  key = key.strip()
  key_lines = key.split(b'\n')
  if (not key_lines[0].startswith(b'-----')
      or not key_lines[-1].startswith(b'-----')):
    raise OpenSSLException(
        'The following key does not appear to be in PEM format: \n{0}'
        .format(key))
  return b''.join(key_lines[1:-1])


class OpensslCrypt(object):
  """Base Class for OpenSSL encryption functions."""

  def __init__(self, openssl_executable):
    self.openssl_executable = openssl_executable

  def RunOpenSSL(self, cmd_args, cmd_input=None):
    """Run an openssl command with optional input and return the output."""

    command = [self.openssl_executable]
    command.extend(cmd_args)

    try:
      p = subprocess.Popen(command, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      output, stderr = p.communicate(cmd_input)
      log.debug('Ran command "{0}" with standard error of:\n{1}'
                .format(' '.join(command), stderr))
    except OSError as e:
      # This should be rare. Generally, OSError will show up when openssl
      # doesn't exist or can't be executed. However, in the code, we use
      # "FindExecutableOnPath" which already checks for these things.
      raise OpenSSLException(
          '[{0}] exited with [{1}].'.format(command[0], e.strerror))

    if p.returncode:
      # This will happen whenever there is an openssl failure (e.g. a failure
      # to decrypt a message with the given key).
      raise OpenSSLException('[{0}] exited with return code [{1}]:\n{2}.'
                             .format(command[0], p.returncode, stderr))
    return output

  def GetKeyPair(self, key_length=DEFAULT_KEY_LENGTH):
    """Returns an RSA key pair (private key)."""
    return self.RunOpenSSL(['genrsa', six.text_type(key_length)])

  def GetPublicKey(self, key):
    """Returns a public key from a key pair."""
    return self.RunOpenSSL(['rsa', '-pubout'], cmd_input=key)

  def DecryptMessage(self, key, enc_message, destroy_key=False):
    """Returns a decrypted message using the provided key.

    Args:
      key: An openssl key pair (private key).
      enc_message: a base64 encoded encrypted message.
      destroy_key: Unused for OpenSSL.
    Returns:
      Decrypted version of enc_message
    """
    del destroy_key
    encrypted_message_data = base64.b64decode(enc_message)

    # Write the private key to a temporary file for decryption
    # This file is created with 600 permissions.
    with tempfile.NamedTemporaryFile() as tf:
      tf.write(key)
      tf.flush()
      openssl_args = ['rsautl', '-decrypt', '-oaep', '-inkey', tf.name]
      message = self.RunOpenSSL(openssl_args, cmd_input=encrypted_message_data)
    return message

  def GetModulusExponentFromPublicKey(self, public_key,
                                      key_length=DEFAULT_KEY_LENGTH):
    """Returns a base64 encoded modulus and exponent from the public key."""
    key = StripKey(public_key)
    decoded_key = base64.b64decode(key)
    # OpenSSL Public key format is:
    #   32 bytes of header info (can be shorter for smaller keys)
    #   1  byte that has a leading zero for the modulus (This is only true for
    #      keys with a modulus that evenly splits on byte boundries. For keys
    #      where key_length % 8 = 0, we ignore this byte)
    #   XX bytes of modulus (Variable -- 256 bytes for a 2048 bit key)
    #   2  bytes of exponent header
    #   3  bytes of exponent

    # The exponent is the last 3 bytes of the key
    exponent = decoded_key[-3:]

    # The modulus is 5 bytes from the end of the key and is the number of bytes
    # needed to contain the bits of key length
    key_bytes = key_length // 8
    if key_length % 8:
      key_bytes += 1

    modulus_start = -5 - key_bytes
    modulus = decoded_key[modulus_start:-5]

    b64_mod = base64.b64encode(modulus)
    b64_exp = base64.b64encode(exponent)

    return (b64_mod, b64_exp)
