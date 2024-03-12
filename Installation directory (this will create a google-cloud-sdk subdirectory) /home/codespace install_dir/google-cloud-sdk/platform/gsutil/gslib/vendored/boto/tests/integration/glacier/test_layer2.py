# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
import time
from tests.unit import unittest

from boto.glacier.layer2 import Layer1, Layer2


class TestGlacierLayer2(unittest.TestCase):
    glacier = True

    def setUp(self):
        self.layer2 = Layer2()
        self.vault_name = 'testvault%s' % int(time.time())

    def test_create_delete_vault(self):
        vault = self.layer2.create_vault(self.vault_name)
        retrieved_vault = self.layer2.get_vault(self.vault_name)
        self.layer2.delete_vault(self.vault_name)
        self.assertEqual(vault.name, retrieved_vault.name)
        self.assertEqual(vault.arn, retrieved_vault.arn)
        self.assertEqual(vault.creation_date, retrieved_vault.creation_date)
        self.assertEqual(vault.last_inventory_date,
                         retrieved_vault.last_inventory_date)
        self.assertEqual(vault.number_of_archives,
                         retrieved_vault.number_of_archives)
