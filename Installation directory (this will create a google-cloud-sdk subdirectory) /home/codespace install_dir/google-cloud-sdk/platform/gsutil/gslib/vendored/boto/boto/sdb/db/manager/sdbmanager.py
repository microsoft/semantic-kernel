# Copyright (c) 2006,2007,2008 Mitch Garnaat http://garnaat.org/
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
import boto
import re
from boto.utils import find_class
import uuid
from boto.sdb.db.key import Key
from boto.sdb.db.blob import Blob
from boto.sdb.db.property import ListProperty, MapProperty
from datetime import datetime, date, time
from boto.exception import SDBPersistenceError, S3ResponseError
from boto.compat import map, six, long_type

ISO8601 = '%Y-%m-%dT%H:%M:%SZ'


class TimeDecodeError(Exception):
    pass


class SDBConverter(object):
    """
    Responsible for converting base Python types to format compatible
    with underlying database.  For SimpleDB, that means everything
    needs to be converted to a string when stored in SimpleDB and from
    a string when retrieved.

    To convert a value, pass it to the encode or decode method.  The
    encode method will take a Python native value and convert to DB
    format.  The decode method will take a DB format value and convert
    it to Python native format.  To find the appropriate method to
    call, the generic encode/decode methods will look for the
    type-specific method by searching for a method
    called"encode_<type name>" or "decode_<type name>".
    """
    def __init__(self, manager):
        # Do a delayed import to prevent possible circular import errors.
        from boto.sdb.db.model import Model
        self.model_class = Model
        self.manager = manager
        self.type_map = {bool: (self.encode_bool, self.decode_bool),
                         int: (self.encode_int, self.decode_int),
                         float: (self.encode_float, self.decode_float),
                         self.model_class: (
                            self.encode_reference, self.decode_reference
                         ),
                         Key: (self.encode_reference, self.decode_reference),
                         datetime: (self.encode_datetime, self.decode_datetime),
                         date: (self.encode_date, self.decode_date),
                         time: (self.encode_time, self.decode_time),
                         Blob: (self.encode_blob, self.decode_blob),
                         str: (self.encode_string, self.decode_string),
                      }
        if six.PY2:
            self.type_map[long] = (self.encode_long, self.decode_long)

    def encode(self, item_type, value):
        try:
            if self.model_class in item_type.mro():
                item_type = self.model_class
        except:
            pass
        if item_type in self.type_map:
            encode = self.type_map[item_type][0]
            return encode(value)
        return value

    def decode(self, item_type, value):
        if item_type in self.type_map:
            decode = self.type_map[item_type][1]
            return decode(value)
        return value

    def encode_list(self, prop, value):
        if value in (None, []):
            return []
        if not isinstance(value, list):
            # This is a little trick to avoid encoding when it's just a single value,
            # since that most likely means it's from a query
            item_type = getattr(prop, "item_type")
            return self.encode(item_type, value)
        # Just enumerate(value) won't work here because
        # we need to add in some zero padding
        # We support lists up to 1,000 attributes, since
        # SDB technically only supports 1024 attributes anyway
        values = {}
        for k, v in enumerate(value):
            values["%03d" % k] = v
        return self.encode_map(prop, values)

    def encode_map(self, prop, value):
        import urllib
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError('Expected a dict value, got %s' % type(value))
        new_value = []
        for key in value:
            item_type = getattr(prop, "item_type")
            if self.model_class in item_type.mro():
                item_type = self.model_class
            encoded_value = self.encode(item_type, value[key])
            if encoded_value is not None:
                new_value.append('%s:%s' % (urllib.quote(key), encoded_value))
        return new_value

    def encode_prop(self, prop, value):
        if isinstance(prop, ListProperty):
            return self.encode_list(prop, value)
        elif isinstance(prop, MapProperty):
            return self.encode_map(prop, value)
        else:
            return self.encode(prop.data_type, value)

    def decode_list(self, prop, value):
        if not isinstance(value, list):
            value = [value]
        if hasattr(prop, 'item_type'):
            item_type = getattr(prop, "item_type")
            dec_val = {}
            for val in value:
                if val is not None:
                    k, v = self.decode_map_element(item_type, val)
                    try:
                        k = int(k)
                    except:
                        k = v
                    dec_val[k] = v
            value = dec_val.values()
        return value

    def decode_map(self, prop, value):
        if not isinstance(value, list):
            value = [value]
        ret_value = {}
        item_type = getattr(prop, "item_type")
        for val in value:
            k, v = self.decode_map_element(item_type, val)
            ret_value[k] = v
        return ret_value

    def decode_map_element(self, item_type, value):
        """Decode a single element for a map"""
        import urllib
        key = value
        if ":" in value:
            key, value = value.split(':', 1)
            key = urllib.unquote(key)
        if self.model_class in item_type.mro():
            value = item_type(id=value)
        else:
            value = self.decode(item_type, value)
        return (key, value)

    def decode_prop(self, prop, value):
        if isinstance(prop, ListProperty):
            return self.decode_list(prop, value)
        elif isinstance(prop, MapProperty):
            return self.decode_map(prop, value)
        else:
            return self.decode(prop.data_type, value)

    def encode_int(self, value):
        value = int(value)
        value += 2147483648
        return '%010d' % value

    def decode_int(self, value):
        try:
            value = int(value)
        except:
            boto.log.error("Error, %s is not an integer" % value)
            value = 0
        value = int(value)
        value -= 2147483648
        return int(value)

    def encode_long(self, value):
        value = long_type(value)
        value += 9223372036854775808
        return '%020d' % value

    def decode_long(self, value):
        value = long_type(value)
        value -= 9223372036854775808
        return value

    def encode_bool(self, value):
        if value == True or str(value).lower() in ("true", "yes"):
            return 'true'
        else:
            return 'false'

    def decode_bool(self, value):
        if value.lower() == 'true':
            return True
        else:
            return False

    def encode_float(self, value):
        """
        See http://tools.ietf.org/html/draft-wood-ldapext-float-00.
        """
        s = '%e' % value
        l = s.split('e')
        mantissa = l[0].ljust(18, '0')
        exponent = l[1]
        if value == 0.0:
            case = '3'
            exponent = '000'
        elif mantissa[0] != '-' and exponent[0] == '+':
            case = '5'
            exponent = exponent[1:].rjust(3, '0')
        elif mantissa[0] != '-' and exponent[0] == '-':
            case = '4'
            exponent = 999 + int(exponent)
            exponent = '%03d' % exponent
        elif mantissa[0] == '-' and exponent[0] == '-':
            case = '2'
            mantissa = '%f' % (10 + float(mantissa))
            mantissa = mantissa.ljust(18, '0')
            exponent = exponent[1:].rjust(3, '0')
        else:
            case = '1'
            mantissa = '%f' % (10 + float(mantissa))
            mantissa = mantissa.ljust(18, '0')
            exponent = 999 - int(exponent)
            exponent = '%03d' % exponent
        return '%s %s %s' % (case, exponent, mantissa)

    def decode_float(self, value):
        case = value[0]
        exponent = value[2:5]
        mantissa = value[6:]
        if case == '3':
            return 0.0
        elif case == '5':
            pass
        elif case == '4':
            exponent = '%03d' % (int(exponent) - 999)
        elif case == '2':
            mantissa = '%f' % (float(mantissa) - 10)
            exponent = '-' + exponent
        else:
            mantissa = '%f' % (float(mantissa) - 10)
            exponent = '%03d' % abs((int(exponent) - 999))
        return float(mantissa + 'e' + exponent)

    def encode_datetime(self, value):
        if isinstance(value, six.string_types):
            return value
        if isinstance(value, datetime):
            return value.strftime(ISO8601)
        else:
            return value.isoformat()

    def decode_datetime(self, value):
        """Handles both Dates and DateTime objects"""
        if value is None:
            return value
        try:
            if "T" in value:
                if "." in value:
                    # Handle true "isoformat()" dates, which may have a microsecond on at the end of them
                    return datetime.strptime(value.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                else:
                    return datetime.strptime(value, ISO8601)
            else:
                value = value.split("-")
                return date(int(value[0]), int(value[1]), int(value[2]))
        except Exception:
            return None

    def encode_date(self, value):
        if isinstance(value, six.string_types):
            return value
        return value.isoformat()

    def decode_date(self, value):
        try:
            value = value.split("-")
            return date(int(value[0]), int(value[1]), int(value[2]))
        except:
            return None

    encode_time = encode_date

    def decode_time(self, value):
        """ converts strings in the form of HH:MM:SS.mmmmmm
            (created by datetime.time.isoformat()) to
            datetime.time objects.

            Timzone-aware strings ("HH:MM:SS.mmmmmm+HH:MM") won't
            be handled right now and will raise TimeDecodeError.
        """
        if '-' in value or '+' in value:
            # TODO: Handle tzinfo
            raise TimeDecodeError("Can't handle timezone aware objects: %r" % value)
        tmp = value.split('.')
        arg = map(int, tmp[0].split(':'))
        if len(tmp) == 2:
            arg.append(int(tmp[1]))
        return time(*arg)

    def encode_reference(self, value):
        if value in (None, 'None', '', ' '):
            return None
        if isinstance(value, six.string_types):
            return value
        else:
            return value.id

    def decode_reference(self, value):
        if not value or value == "None":
            return None
        return value

    def encode_blob(self, value):
        if not value:
            return None
        if isinstance(value, six.string_types):
            return value

        if not value.id:
            bucket = self.manager.get_blob_bucket()
            key = bucket.new_key(str(uuid.uuid4()))
            value.id = "s3://%s/%s" % (key.bucket.name, key.name)
        else:
            match = re.match("^s3:\/\/([^\/]*)\/(.*)$", value.id)
            if match:
                s3 = self.manager.get_s3_connection()
                bucket = s3.get_bucket(match.group(1), validate=False)
                key = bucket.get_key(match.group(2))
            else:
                raise SDBPersistenceError("Invalid Blob ID: %s" % value.id)

        if value.value is not None:
            key.set_contents_from_string(value.value)
        return value.id

    def decode_blob(self, value):
        if not value:
            return None
        match = re.match("^s3:\/\/([^\/]*)\/(.*)$", value)
        if match:
            s3 = self.manager.get_s3_connection()
            bucket = s3.get_bucket(match.group(1), validate=False)
            try:
                key = bucket.get_key(match.group(2))
            except S3ResponseError as e:
                if e.reason != "Forbidden":
                    raise
                return None
        else:
            return None
        if key:
            return Blob(file=key, id="s3://%s/%s" % (key.bucket.name, key.name))
        else:
            return None

    def encode_string(self, value):
        """Convert ASCII, Latin-1 or UTF-8 to pure Unicode"""
        if not isinstance(value, str):
            return value
        try:
            return six.text_type(value, 'utf-8')
        except:
            # really, this should throw an exception.
            # in the interest of not breaking current
            # systems, however:
            arr = []
            for ch in value:
                arr.append(six.unichr(ord(ch)))
            return u"".join(arr)

    def decode_string(self, value):
        """Decoding a string is really nothing, just
        return the value as-is"""
        return value


class SDBManager(object):

    def __init__(self, cls, db_name, db_user, db_passwd,
                 db_host, db_port, db_table, ddl_dir, enable_ssl,
                 consistent=None):
        self.cls = cls
        self.db_name = db_name
        self.db_user = db_user
        self.db_passwd = db_passwd
        self.db_host = db_host
        self.db_port = db_port
        self.db_table = db_table
        self.ddl_dir = ddl_dir
        self.enable_ssl = enable_ssl
        self.s3 = None
        self.bucket = None
        self.converter = SDBConverter(self)
        self._sdb = None
        self._domain = None
        if consistent is None and hasattr(cls, "__consistent__"):
            consistent = cls.__consistent__
        self.consistent = consistent

    @property
    def sdb(self):
        if self._sdb is None:
            self._connect()
        return self._sdb

    @property
    def domain(self):
        if self._domain is None:
            self._connect()
        return self._domain

    def _connect(self):
        args = dict(aws_access_key_id=self.db_user,
                    aws_secret_access_key=self.db_passwd,
                    is_secure=self.enable_ssl)
        try:
            region = [x for x in boto.sdb.regions() if x.endpoint == self.db_host][0]
            args['region'] = region
        except IndexError:
            pass
        self._sdb = boto.connect_sdb(**args)
        # This assumes that the domain has already been created
        # It's much more efficient to do it this way rather than
        # having this make a roundtrip each time to validate.
        # The downside is that if the domain doesn't exist, it breaks
        self._domain = self._sdb.lookup(self.db_name, validate=False)
        if not self._domain:
            self._domain = self._sdb.create_domain(self.db_name)

    def _object_lister(self, cls, query_lister):
        for item in query_lister:
            obj = self.get_object(cls, item.name, item)
            if obj:
                yield obj

    def encode_value(self, prop, value):
        if value is None:
            return None
        if not prop:
            return str(value)
        return self.converter.encode_prop(prop, value)

    def decode_value(self, prop, value):
        return self.converter.decode_prop(prop, value)

    def get_s3_connection(self):
        if not self.s3:
            self.s3 = boto.connect_s3(self.db_user, self.db_passwd)
        return self.s3

    def get_blob_bucket(self, bucket_name=None):
        s3 = self.get_s3_connection()
        bucket_name = "%s-%s" % (s3.aws_access_key_id, self.domain.name)
        bucket_name = bucket_name.lower()
        try:
            self.bucket = s3.get_bucket(bucket_name)
        except:
            self.bucket = s3.create_bucket(bucket_name)
        return self.bucket

    def load_object(self, obj):
        if not obj._loaded:
            a = self.domain.get_attributes(obj.id, consistent_read=self.consistent)
            if '__type__' in a:
                for prop in obj.properties(hidden=False):
                    if prop.name in a:
                        value = self.decode_value(prop, a[prop.name])
                        value = prop.make_value_from_datastore(value)
                        try:
                            setattr(obj, prop.name, value)
                        except Exception as e:
                            boto.log.exception(e)
            obj._loaded = True

    def get_object(self, cls, id, a=None):
        obj = None
        if not a:
            a = self.domain.get_attributes(id, consistent_read=self.consistent)
        if '__type__' in a:
            if not cls or a['__type__'] != cls.__name__:
                cls = find_class(a['__module__'], a['__type__'])
            if cls:
                params = {}
                for prop in cls.properties(hidden=False):
                    if prop.name in a:
                        value = self.decode_value(prop, a[prop.name])
                        value = prop.make_value_from_datastore(value)
                        params[prop.name] = value
                obj = cls(id, **params)
                obj._loaded = True
            else:
                s = '(%s) class %s.%s not found' % (id, a['__module__'], a['__type__'])
                boto.log.info('sdbmanager: %s' % s)
        return obj

    def get_object_from_id(self, id):
        return self.get_object(None, id)

    def query(self, query):
        query_str = "select * from `%s` %s" % (self.domain.name, self._build_filter_part(query.model_class, query.filters, query.sort_by, query.select))
        if query.limit:
            query_str += " limit %s" % query.limit
        rs = self.domain.select(query_str, max_items=query.limit, next_token=query.next_token)
        query.rs = rs
        return self._object_lister(query.model_class, rs)

    def count(self, cls, filters, quick=True, sort_by=None, select=None):
        """
        Get the number of results that would
        be returned in this query
        """
        query = "select count(*) from `%s` %s" % (self.domain.name, self._build_filter_part(cls, filters, sort_by, select))
        count = 0
        for row in self.domain.select(query):
            count += int(row['Count'])
            if quick:
                return count
        return count

    def _build_filter(self, property, name, op, val):
        if name == "__id__":
            name = 'itemName()'
        if name != "itemName()":
            name = '`%s`' % name
        if val is None:
            if op in ('is', '='):
                return "%(name)s is null" % {"name": name}
            elif op in ('is not', '!='):
                return "%s is not null" % name
            else:
                val = ""
        if property.__class__ == ListProperty:
            if op in ("is", "="):
                op = "like"
            elif op in ("!=", "not"):
                op = "not like"
            if not(op in ["like", "not like"] and val.startswith("%")):
                val = "%%:%s" % val
        return "%s %s '%s'" % (name, op, val.replace("'", "''"))

    def _build_filter_part(self, cls, filters, order_by=None, select=None):
        """
        Build the filter part
        """
        import types
        query_parts = []

        order_by_filtered = False

        if order_by:
            if order_by[0] == "-":
                order_by_method = "DESC"
                order_by = order_by[1:]
            else:
                order_by_method = "ASC"

        if select:
            if order_by and order_by in select:
                order_by_filtered = True
            query_parts.append("(%s)" % select)

        if isinstance(filters, six.string_types):
            query = "WHERE %s AND `__type__` = '%s'" % (filters, cls.__name__)
            if order_by in ["__id__", "itemName()"]:
                query += " ORDER BY itemName() %s" % order_by_method
            elif order_by is not None:
                query += " ORDER BY `%s` %s" % (order_by, order_by_method)
            return query

        for filter in filters:
            filter_parts = []
            filter_props = filter[0]
            if not isinstance(filter_props, list):
                filter_props = [filter_props]
            for filter_prop in filter_props:
                (name, op) = filter_prop.strip().split(" ", 1)
                value = filter[1]
                property = cls.find_property(name)
                if name == order_by:
                    order_by_filtered = True
                if types.TypeType(value) == list:
                    filter_parts_sub = []
                    for val in value:
                        val = self.encode_value(property, val)
                        if isinstance(val, list):
                            for v in val:
                                filter_parts_sub.append(self._build_filter(property, name, op, v))
                        else:
                            filter_parts_sub.append(self._build_filter(property, name, op, val))
                    filter_parts.append("(%s)" % (" OR ".join(filter_parts_sub)))
                else:
                    val = self.encode_value(property, value)
                    if isinstance(val, list):
                        for v in val:
                            filter_parts.append(self._build_filter(property, name, op, v))
                    else:
                        filter_parts.append(self._build_filter(property, name, op, val))
            query_parts.append("(%s)" % (" or ".join(filter_parts)))


        type_query = "(`__type__` = '%s'" % cls.__name__
        for subclass in self._get_all_decendents(cls).keys():
            type_query += " or `__type__` = '%s'" % subclass
        type_query += ")"
        query_parts.append(type_query)

        order_by_query = ""

        if order_by:
            if not order_by_filtered:
                query_parts.append("`%s` LIKE '%%'" % order_by)
            if order_by in ["__id__", "itemName()"]:
                order_by_query = " ORDER BY itemName() %s" % order_by_method
            else:
                order_by_query = " ORDER BY `%s` %s" % (order_by, order_by_method)

        if len(query_parts) > 0:
            return "WHERE %s %s" % (" AND ".join(query_parts), order_by_query)
        else:
            return ""


    def _get_all_decendents(self, cls):
        """Get all decendents for a given class"""
        decendents = {}
        for sc in cls.__sub_classes__:
            decendents[sc.__name__] = sc
            decendents.update(self._get_all_decendents(sc))
        return decendents

    def query_gql(self, query_string, *args, **kwds):
        raise NotImplementedError("GQL queries not supported in SimpleDB")

    def save_object(self, obj, expected_value=None):
        if not obj.id:
            obj.id = str(uuid.uuid4())

        attrs = {'__type__': obj.__class__.__name__,
                 '__module__': obj.__class__.__module__,
                 '__lineage__': obj.get_lineage()}
        del_attrs = []
        for property in obj.properties(hidden=False):
            value = property.get_value_for_datastore(obj)
            if value is not None:
                value = self.encode_value(property, value)
            if value == []:
                value = None
            if value is None:
                del_attrs.append(property.name)
                continue
            attrs[property.name] = value
            if property.unique:
                try:
                    args = {property.name: value}
                    obj2 = next(obj.find(**args))
                    if obj2.id != obj.id:
                        raise SDBPersistenceError("Error: %s must be unique!" % property.name)
                except(StopIteration):
                    pass
        # Convert the Expected value to SDB format
        if expected_value:
            prop = obj.find_property(expected_value[0])
            v = expected_value[1]
            if v is not None and not isinstance(v, bool):
                v = self.encode_value(prop, v)
            expected_value[1] = v
        self.domain.put_attributes(obj.id, attrs, replace=True, expected_value=expected_value)
        if len(del_attrs) > 0:
            self.domain.delete_attributes(obj.id, del_attrs)
        return obj

    def delete_object(self, obj):
        self.domain.delete_attributes(obj.id)

    def set_property(self, prop, obj, name, value):
        setattr(obj, name, value)
        value = prop.get_value_for_datastore(obj)
        value = self.encode_value(prop, value)
        if prop.unique:
            try:
                args = {prop.name: value}
                obj2 = next(obj.find(**args))
                if obj2.id != obj.id:
                    raise SDBPersistenceError("Error: %s must be unique!" % prop.name)
            except(StopIteration):
                pass
        self.domain.put_attributes(obj.id, {name: value}, replace=True)

    def get_property(self, prop, obj, name):
        a = self.domain.get_attributes(obj.id, consistent_read=self.consistent)

        # try to get the attribute value from SDB
        if name in a:
            value = self.decode_value(prop, a[name])
            value = prop.make_value_from_datastore(value)
            setattr(obj, prop.name, value)
            return value
        raise AttributeError('%s not found' % name)

    def set_key_value(self, obj, name, value):
        self.domain.put_attributes(obj.id, {name: value}, replace=True)

    def delete_key_value(self, obj, name):
        self.domain.delete_attributes(obj.id, name)

    def get_key_value(self, obj, name):
        a = self.domain.get_attributes(obj.id, name, consistent_read=self.consistent)
        if name in a:
            return a[name]
        else:
            return None

    def get_raw_item(self, obj):
        return self.domain.get_item(obj.id)
