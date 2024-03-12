# -*- coding: utf-8 -*-
# Copyright (c) 2012 Thomas Parslow http://almostobsolete.net/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

from boto.glacier.layer1 import Layer1
from boto.glacier.vault import Vault


class Layer2(object):
    """
    Provides a more pythonic and friendly interface to Glacier based on Layer1
    """

    def __init__(self, *args, **kwargs):
        # Accept a passed in layer1, mainly to allow easier testing
        if "layer1" in kwargs:
            self.layer1 = kwargs["layer1"]
        else:
            self.layer1 = Layer1(*args, **kwargs)

    def create_vault(self, name):
        """Creates a vault.

        :type name: str
        :param name: The name of the vault

        :rtype: :class:`boto.glacier.vault.Vault`
        :return: A Vault object representing the vault.
        """
        self.layer1.create_vault(name)
        return self.get_vault(name)

    def delete_vault(self, name):
        """Delete a vault.

        This operation deletes a vault. Amazon Glacier will delete a
        vault only if there are no archives in the vault as per the
        last inventory and there have been no writes to the vault
        since the last inventory. If either of these conditions is not
        satisfied, the vault deletion fails (that is, the vault is not
        removed) and Amazon Glacier returns an error.

        This operation is idempotent, you can send the same request
        multiple times and it has no further effect after the first
        time Amazon Glacier delete the specified vault.

        :type vault_name: str
        :param vault_name: The name of the vault to delete.
        """
        return self.layer1.delete_vault(name)

    def get_vault(self, name):
        """
        Get an object representing a named vault from Glacier. This
        operation does not check if the vault actually exists.

        :type name: str
        :param name: The name of the vault

        :rtype: :class:`boto.glacier.vault.Vault`
        :return: A Vault object representing the vault.
        """
        response_data = self.layer1.describe_vault(name)
        return Vault(self.layer1, response_data)

    def list_vaults(self):
        """
        Return a list of all vaults associated with the account ID.

        :rtype: List of :class:`boto.glacier.vault.Vault`
        :return: A list of Vault objects.
        """
        vaults = []
        marker = None
        while True:
            response_data = self.layer1.list_vaults(marker=marker, limit=1000)
            vaults.extend([Vault(self.layer1, rd) for rd in response_data['VaultList']])
            marker = response_data.get('Marker')
            if not marker:
                break

        return vaults
