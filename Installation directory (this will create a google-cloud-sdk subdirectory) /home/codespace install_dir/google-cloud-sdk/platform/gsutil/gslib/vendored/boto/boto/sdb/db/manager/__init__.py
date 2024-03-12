# Copyright (c) 2006,2007,2008 Mitch Garnaat http://garnaat.org/
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


def get_manager(cls):
    """
    Returns the appropriate Manager class for a given Model class.  It
    does this by looking in the boto config for a section like this::

        [DB]
        db_type = SimpleDB
        db_user = <aws access key id>
        db_passwd = <aws secret access key>
        db_name = my_domain
        [DB_TestBasic]
        db_type = SimpleDB
        db_user = <another aws access key id>
        db_passwd = <another aws secret access key>
        db_name = basic_domain
        db_port = 1111

    The values in the DB section are "generic values" that will be used
    if nothing more specific is found.  You can also create a section for
    a specific Model class that gives the db info for that class.
    In the example above, TestBasic is a Model subclass.
    """
    db_user = boto.config.get('DB', 'db_user', None)
    db_passwd = boto.config.get('DB', 'db_passwd', None)
    db_type = boto.config.get('DB', 'db_type', 'SimpleDB')
    db_name = boto.config.get('DB', 'db_name', None)
    db_table = boto.config.get('DB', 'db_table', None)
    db_host = boto.config.get('DB', 'db_host', "sdb.amazonaws.com")
    db_port = boto.config.getint('DB', 'db_port', 443)
    enable_ssl = boto.config.getbool('DB', 'enable_ssl', True)
    sql_dir = boto.config.get('DB', 'sql_dir', None)
    debug = boto.config.getint('DB', 'debug', 0)
    # first see if there is a fully qualified section name in the Boto config
    module_name = cls.__module__.replace('.', '_')
    db_section = 'DB_' + module_name + '_' + cls.__name__
    if not boto.config.has_section(db_section):
        db_section = 'DB_' + cls.__name__
    if boto.config.has_section(db_section):
        db_user = boto.config.get(db_section, 'db_user', db_user)
        db_passwd = boto.config.get(db_section, 'db_passwd', db_passwd)
        db_type = boto.config.get(db_section, 'db_type', db_type)
        db_name = boto.config.get(db_section, 'db_name', db_name)
        db_table = boto.config.get(db_section, 'db_table', db_table)
        db_host = boto.config.get(db_section, 'db_host', db_host)
        db_port = boto.config.getint(db_section, 'db_port', db_port)
        enable_ssl = boto.config.getint(db_section, 'enable_ssl', enable_ssl)
        debug = boto.config.getint(db_section, 'debug', debug)
    elif hasattr(cls, "_db_name") and cls._db_name is not None:
        # More specific then the generic DB config is any _db_name class property
        db_name = cls._db_name
    elif hasattr(cls.__bases__[0], "_manager"):
        return cls.__bases__[0]._manager
    if db_type == 'SimpleDB':
        from boto.sdb.db.manager.sdbmanager import SDBManager
        return SDBManager(cls, db_name, db_user, db_passwd,
                          db_host, db_port, db_table, sql_dir, enable_ssl)
    elif db_type == 'XML':
        from boto.sdb.db.manager.xmlmanager import XMLManager
        return XMLManager(cls, db_name, db_user, db_passwd,
                          db_host, db_port, db_table, sql_dir, enable_ssl)
    else:
        raise ValueError('Unknown db_type: %s' % db_type)
