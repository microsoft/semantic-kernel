# Copyright (c) 2010 Chris Moyer http://coredumped.org/
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
from boto.sdb.db.property import ListProperty
from boto.sdb.db.model import Model
import time

class SimpleListModel(Model):
    """Test the List Property"""
    nums = ListProperty(int)
    strs = ListProperty(str)

class TestLists(object):
    """Test the List property"""

    def setup_class(cls):
        """Setup this class"""
        cls.objs = []

    def teardown_class(cls):
        """Remove our objects"""
        for o in cls.objs:
            try:
                o.delete()
            except:
                pass

    def test_list_order(self):
        """Testing the order of lists"""
        t = SimpleListModel()
        t.nums = [5, 4, 1, 3, 2]
        t.strs = ["B", "C", "A", "D", "Foo"]
        t.put()
        self.objs.append(t)
        time.sleep(3)
        t = SimpleListModel.get_by_id(t.id)
        assert(t.nums == [5, 4, 1, 3, 2])
        assert(t.strs == ["B", "C", "A", "D", "Foo"])

    def test_old_compat(self):
        """Testing to make sure the old method of encoding lists will still return results"""
        t = SimpleListModel()
        t.put()
        self.objs.append(t)
        time.sleep(3)
        item = t._get_raw_item()
        item['strs'] = ["A", "B", "C"]
        item.save()
        time.sleep(3)
        t = SimpleListModel.get_by_id(t.id)
        i1 = sorted(item['strs'])
        i2 = t.strs
        i2.sort()
        assert(i1 == i2)

    def test_query_equals(self):
        """We noticed a slight problem with querying, since the query uses the same encoder,
        it was asserting that the value was at the same position in the list, not just "in" the list"""
        t = SimpleListModel()
        t.strs = ["Bizzle", "Bar"]
        t.put()
        self.objs.append(t)
        time.sleep(3)
        assert(SimpleListModel.find(strs="Bizzle").count() == 1)
        assert(SimpleListModel.find(strs="Bar").count() == 1)
        assert(SimpleListModel.find(strs=["Bar", "Bizzle"]).count() == 1)

    def test_query_not_equals(self):
        """Test a not equal filter"""
        t = SimpleListModel()
        t.strs = ["Fizzle"]
        t.put()
        self.objs.append(t)
        time.sleep(3)
        print SimpleListModel.all().filter("strs !=", "Fizzle").get_query()
        for tt in SimpleListModel.all().filter("strs !=", "Fizzle"):
            print tt.strs
            assert("Fizzle" not in tt.strs)
