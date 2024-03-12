# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""OAuth 2.0 utilities for SQLAlchemy.

Utilities for using OAuth 2.0 in conjunction with a SQLAlchemy.

Configuration
=============

In order to use this storage, you'll need to create table
with :class:`oauth2client.contrib.sqlalchemy.CredentialsType` column.
It's recommended to either put this column on some sort of user info
table or put the column in a table with a belongs-to relationship to
a user info table.

Here's an example of a simple table with a :class:`CredentialsType`
column that's related to a user table by the `user_id` key.

.. code-block:: python

    from sqlalchemy import Column, ForeignKey, Integer
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship

    from oauth2client.contrib.sqlalchemy import CredentialsType


    Base = declarative_base()


    class Credentials(Base):
        __tablename__ = 'credentials'

        user_id = Column(Integer, ForeignKey('user.id'))
        credentials = Column(CredentialsType)


    class User(Base):
        id = Column(Integer, primary_key=True)
        # bunch of other columns
        credentials = relationship('Credentials')


Usage
=====

With tables ready, you are now able to store credentials in database.
We will reuse tables defined above.

.. code-block:: python

    from sqlalchemy.orm import Session

    from oauth2client.client import OAuth2Credentials
    from oauth2client.contrib.sql_alchemy import Storage

    session = Session()
    user = session.query(User).first()
    storage = Storage(
        session=session,
        model_class=Credentials,
        # This is the key column used to identify
        # the row that stores the credentials.
        key_name='user_id',
        key_value=user.id,
        property_name='credentials',
    )

    # Store
    credentials = OAuth2Credentials(...)
    storage.put(credentials)

    # Retrieve
    credentials = storage.get()

    # Delete
    storage.delete()

"""

from __future__ import absolute_import

import sqlalchemy.types

from oauth2client import client


class CredentialsType(sqlalchemy.types.PickleType):
    """Type representing credentials.

    Alias for :class:`sqlalchemy.types.PickleType`.
    """


class Storage(client.Storage):
    """Store and retrieve a single credential to and from SQLAlchemy.
    This helper presumes the Credentials
    have been stored as a Credentials column
    on a db model class.
    """

    def __init__(self, session, model_class, key_name,
                 key_value, property_name):
        """Constructor for Storage.

        Args:
            session: An instance of :class:`sqlalchemy.orm.Session`.
            model_class: SQLAlchemy declarative mapping.
            key_name: string, key name for the entity that has the credentials
            key_value: key value for the entity that has the credentials
            property_name: A string indicating which property on the
                           ``model_class`` to store the credentials.
                           This property must be a
                           :class:`CredentialsType` column.
        """
        super(Storage, self).__init__()

        self.session = session
        self.model_class = model_class
        self.key_name = key_name
        self.key_value = key_value
        self.property_name = property_name

    def locked_get(self):
        """Retrieve stored credential.

        Returns:
            A :class:`oauth2client.Credentials` instance or `None`.
        """
        filters = {self.key_name: self.key_value}
        query = self.session.query(self.model_class).filter_by(**filters)
        entity = query.first()

        if entity:
            credential = getattr(entity, self.property_name)
            if credential and hasattr(credential, 'set_store'):
                credential.set_store(self)
            return credential
        else:
            return None

    def locked_put(self, credentials):
        """Write a credentials to the SQLAlchemy datastore.

        Args:
            credentials: :class:`oauth2client.Credentials`
        """
        filters = {self.key_name: self.key_value}
        query = self.session.query(self.model_class).filter_by(**filters)
        entity = query.first()

        if not entity:
            entity = self.model_class(**filters)

        setattr(entity, self.property_name, credentials)
        self.session.add(entity)

    def locked_delete(self):
        """Delete credentials from the SQLAlchemy datastore."""
        filters = {self.key_name: self.key_value}
        self.session.query(self.model_class).filter_by(**filters).delete()
