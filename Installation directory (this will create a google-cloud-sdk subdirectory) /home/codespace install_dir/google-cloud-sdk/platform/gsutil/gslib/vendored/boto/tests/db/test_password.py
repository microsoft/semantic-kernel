# Copyright (c) 2010 Robert Mela
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
 

import unittest
import logging
import time

log= logging.getLogger('password_property_test')
log.setLevel(logging.DEBUG)

class PasswordPropertyTest(unittest.TestCase):
    """Test the PasswordProperty"""

    def tearDown(self):
        cls=self.test_model()
        for obj in cls.all(): obj.delete()

    def hmac_hashfunc(self):
        import hmac
        def hashfunc(msg):
            return hmac.new('mysecret', msg)
        return hashfunc

    def test_model(self,hashfunc=None):
        from boto.utils import Password
        from boto.sdb.db.model import Model
        from boto.sdb.db.property import PasswordProperty
        import hashlib
        class MyModel(Model):
            password=PasswordProperty(hashfunc=hashfunc)
        return MyModel

    def test_custom_password_class(self):
        from boto.utils import Password
        from boto.sdb.db.model import Model
        from boto.sdb.db.property import PasswordProperty
        import hmac, hashlib


        myhashfunc = hashlib.md5
	## Define a new Password class
        class MyPassword(Password):
            hashfunc = myhashfunc #hashlib.md5 #lambda cls,msg: hmac.new('mysecret',msg)

	## Define a custom password property using the new Password class

        class MyPasswordProperty(PasswordProperty):
            data_type=MyPassword
            type_name=MyPassword.__name__

	## Define a model using the new password property

        class MyModel(Model):
            password=MyPasswordProperty()#hashfunc=hashlib.md5)

        obj = MyModel()
        obj.password = 'bar'
        expected = myhashfunc('bar').hexdigest() #hmac.new('mysecret','bar').hexdigest()
        log.debug("\npassword=%s\nexpected=%s" % (obj.password, expected))
        self.assertTrue(obj.password == 'bar' )
        obj.save()
        id= obj.id
        time.sleep(5)
        obj = MyModel.get_by_id(id)
        self.assertEquals(obj.password, 'bar')
        self.assertEquals(str(obj.password), expected)
                          #hmac.new('mysecret','bar').hexdigest())
 
        
    def test_aaa_default_password_property(self):
        cls = self.test_model()
        obj = cls(id='passwordtest')
        obj.password = 'foo'
        self.assertEquals('foo', obj.password)
        obj.save()
        time.sleep(5)
        obj = cls.get_by_id('passwordtest')
        self.assertEquals('foo', obj.password)

    def test_password_constructor_hashfunc(self):
        import hmac
        myhashfunc=lambda msg: hmac.new('mysecret', msg)
        cls = self.test_model(hashfunc=myhashfunc)
        obj = cls()
        obj.password='hello'
        expected = myhashfunc('hello').hexdigest()
        self.assertEquals(obj.password, 'hello')
        self.assertEquals(str(obj.password), expected)
        obj.save()
        id = obj.id
        time.sleep(5)
        obj = cls.get_by_id(id)
        log.debug("\npassword=%s" % obj.password)
        self.assertTrue(obj.password == 'hello')

       
 
if __name__ == '__main__':
    import sys, os
    curdir = os.path.dirname( os.path.abspath(__file__) )
    srcroot = curdir + "/../.."
    sys.path = [ srcroot ] + sys.path
    logging.basicConfig()
    log.setLevel(logging.INFO)
    suite = unittest.TestLoader().loadTestsFromTestCase(PasswordPropertyTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

    import boto
 
