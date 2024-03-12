import logging
import time
from datetime import datetime

from boto.sdb.db.model import Model
from boto.sdb.db.property import StringProperty, IntegerProperty, BooleanProperty
from boto.sdb.db.property import DateTimeProperty, FloatProperty, ReferenceProperty
from boto.sdb.db.property import PasswordProperty, ListProperty, MapProperty
from boto.exception import SDBPersistenceError

logging.basicConfig()
log = logging.getLogger('test_db')
log.setLevel(logging.DEBUG)

_objects = {}

#
# This will eventually be moved to the boto.tests module and become a real unit test
# but for now it will live here.  It shows examples of each of the Property types in
# use and tests the basic operations.
#
class TestBasic(Model):

    name = StringProperty()
    size = IntegerProperty()
    foo = BooleanProperty()
    date = DateTimeProperty()

class TestFloat(Model):

    name = StringProperty()
    value = FloatProperty()

class TestRequired(Model):

    req = StringProperty(required=True, default='foo')

class TestReference(Model):

    ref = ReferenceProperty(reference_class=TestBasic, collection_name='refs')

class TestSubClass(TestBasic):

    answer = IntegerProperty()

class TestPassword(Model):
    password = PasswordProperty()

class TestList(Model):

    name = StringProperty()
    nums = ListProperty(int)

class TestMap(Model):

    name = StringProperty()
    map = MapProperty()

class TestListReference(Model):

    name = StringProperty()
    basics = ListProperty(TestBasic)

class TestAutoNow(Model):

    create_date = DateTimeProperty(auto_now_add=True)
    modified_date = DateTimeProperty(auto_now=True)

class TestUnique(Model):
    name = StringProperty(unique=True)

def test_basic():
    global _objects
    t = TestBasic()
    t.name = 'simple'
    t.size = -42
    t.foo = True
    t.date = datetime.now()
    log.debug('saving object')
    t.put()
    _objects['test_basic_t'] = t
    time.sleep(5)
    log.debug('now try retrieving it')
    tt = TestBasic.get_by_id(t.id)
    _objects['test_basic_tt'] = tt
    assert tt.id == t.id
    l = TestBasic.get_by_id([t.id])
    assert len(l) == 1
    assert l[0].id == t.id
    assert t.size == tt.size
    assert t.foo == tt.foo
    assert t.name == tt.name
    #assert t.date == tt.date
    return t

def test_float():
    global _objects
    t = TestFloat()
    t.name = 'float object'
    t.value = 98.6
    log.debug('saving object')
    t.save()
    _objects['test_float_t'] = t
    time.sleep(5)
    log.debug('now try retrieving it')
    tt = TestFloat.get_by_id(t.id)
    _objects['test_float_tt'] = tt
    assert tt.id == t.id
    assert tt.name == t.name
    assert tt.value == t.value
    return t

def test_required():
    global _objects
    t = TestRequired()
    _objects['test_required_t'] = t
    t.put()
    return t

def test_reference(t=None):
    global _objects
    if not t:
        t = test_basic()
    tt = TestReference()
    tt.ref = t
    tt.put()
    time.sleep(10)
    tt = TestReference.get_by_id(tt.id)
    _objects['test_reference_tt'] = tt
    assert tt.ref.id == t.id
    for o in t.refs:
        log.debug(o)

def test_subclass():
    global _objects
    t = TestSubClass()
    _objects['test_subclass_t'] = t
    t.name = 'a subclass'
    t.size = -489
    t.save()

def test_password():
    global _objects
    t = TestPassword()
    _objects['test_password_t'] = t
    t.password = "foo"
    t.save()
    time.sleep(5)
    # Make sure it stored ok
    tt = TestPassword.get_by_id(t.id)
    _objects['test_password_tt'] = tt
    #Testing password equality
    assert tt.password == "foo"
    #Testing password not stored as string
    assert str(tt.password) != "foo"

def test_list():
    global _objects
    t = TestList()
    _objects['test_list_t'] = t
    t.name = 'a list of ints'
    t.nums = [1, 2, 3, 4, 5]
    t.put()
    tt = TestList.get_by_id(t.id)
    _objects['test_list_tt'] = tt
    assert tt.name == t.name
    for n in tt.nums:
        assert isinstance(n, int)

def test_list_reference():
    global _objects
    t = TestBasic()
    t.put()
    _objects['test_list_ref_t'] = t
    tt = TestListReference()
    tt.name = "foo"
    tt.basics = [t]
    tt.put()
    time.sleep(5)
    _objects['test_list_ref_tt'] = tt
    ttt = TestListReference.get_by_id(tt.id)
    assert ttt.basics[0].id == t.id

def test_unique():
    global _objects
    t = TestUnique()
    name = 'foo' + str(int(time.time()))
    t.name = name
    t.put()
    _objects['test_unique_t'] = t
    time.sleep(10)
    tt = TestUnique()
    _objects['test_unique_tt'] = tt
    tt.name = name
    try:
        tt.put()
        assert False
    except(SDBPersistenceError):
        pass

def test_datetime():
    global _objects
    t = TestAutoNow()
    t.put()
    _objects['test_datetime_t'] = t
    time.sleep(5)
    tt = TestAutoNow.get_by_id(t.id)
    assert tt.create_date.timetuple() == t.create_date.timetuple()

def test():
    log.info('test_basic')
    t1 = test_basic()
    log.info('test_required')
    test_required()
    log.info('test_reference')
    test_reference(t1)
    log.info('test_subclass')
    test_subclass()
    log.info('test_password')
    test_password()
    log.info('test_list')
    test_list()
    log.info('test_list_reference')
    test_list_reference()
    log.info("test_datetime")
    test_datetime()
    log.info('test_unique')
    test_unique()

if __name__ == "__main__":
    test()
