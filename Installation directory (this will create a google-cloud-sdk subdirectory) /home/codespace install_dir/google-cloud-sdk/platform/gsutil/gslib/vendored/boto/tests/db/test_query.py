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
from boto.sdb.db.property import ListProperty, StringProperty, ReferenceProperty, IntegerProperty
from boto.sdb.db.model import Model
import time

class SimpleModel(Model):
    """Simple Test Model"""
    name = StringProperty()
    strs = ListProperty(str)
    num = IntegerProperty()

class SubModel(SimpleModel):
    """Simple Subclassed Model"""
    ref = ReferenceProperty(SimpleModel, collection_name="reverse_ref")


class TestQuerying(object):
    """Test different querying capabilities"""

    def setup_class(cls):
        """Setup this class"""
        cls.objs = []

        o = SimpleModel()
        o.name = "Simple Object"
        o.strs = ["B", "A", "C", "Foo"]
        o.num = 1
        o.put()
        cls.objs.append(o)

        o2 = SimpleModel()
        o2.name = "Referenced Object"
        o2.num = 2
        o2.put()
        cls.objs.append(o2)

        o3 = SubModel()
        o3.name = "Sub Object"
        o3.num = 3
        o3.ref = o2
        o3.put()
        cls.objs.append(o3)

        time.sleep(3)



    def teardown_class(cls):
        """Remove our objects"""
        for o in cls.objs:
            try:
                o.delete()
            except:
                pass

    def test_find(self):
        """Test using the "Find" method"""
        assert(SimpleModel.find(name="Simple Object").next().id == self.objs[0].id)
        assert(SimpleModel.find(name="Referenced Object").next().id == self.objs[1].id)
        assert(SimpleModel.find(name="Sub Object").next().id == self.objs[2].id)

    def test_like_filter(self):
        """Test a "like" filter"""
        query = SimpleModel.all()
        query.filter("name like", "% Object")
        assert(query.count() == 3)

        query = SimpleModel.all()
        query.filter("name not like", "% Object")
        assert(query.count() == 0)

    def test_equals_filter(self):
        """Test an "=" and "!=" filter"""
        query = SimpleModel.all()
        query.filter("name =", "Simple Object")
        assert(query.count() == 1)

        query = SimpleModel.all()
        query.filter("name !=", "Simple Object")
        assert(query.count() == 2)

    def test_or_filter(self):
        """Test a filter function as an "or" """
        query = SimpleModel.all()
        query.filter("name =", ["Simple Object", "Sub Object"])
        assert(query.count() == 2)

    def test_and_filter(self):
        """Test Multiple filters which are an "and" """
        query = SimpleModel.all()
        query.filter("name like", "% Object")
        query.filter("name like", "Simple %")
        assert(query.count() == 1)

    def test_none_filter(self):
        """Test filtering for a value that's not set"""
        query = SimpleModel.all()
        query.filter("ref =", None)
        assert(query.count() == 2)

    def test_greater_filter(self):
        """Test filtering Using >, >="""
        query = SimpleModel.all()
        query.filter("num >", 1)
        assert(query.count() == 2)

        query = SimpleModel.all()
        query.filter("num >=", 1)
        assert(query.count() == 3)

    def test_less_filter(self):
        """Test filtering Using <, <="""
        query = SimpleModel.all()
        query.filter("num <", 3)
        assert(query.count() == 2)

        query = SimpleModel.all()
        query.filter("num <=", 3)
        assert(query.count() == 3)

    def test_query_on_list(self):
        """Test querying on a list"""
        assert(SimpleModel.find(strs="A").next().id == self.objs[0].id)
        assert(SimpleModel.find(strs="B").next().id == self.objs[0].id)
        assert(SimpleModel.find(strs="C").next().id == self.objs[0].id)

    def test_like(self):
        """Test with a "like" expression"""
        query = SimpleModel.all()
        query.filter("strs like", "%oo%")
        print query.get_query()
        assert(query.count() == 1)
