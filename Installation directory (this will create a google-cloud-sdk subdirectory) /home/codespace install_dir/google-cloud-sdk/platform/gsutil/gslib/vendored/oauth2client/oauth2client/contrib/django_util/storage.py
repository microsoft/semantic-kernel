# Copyright 2015 Google Inc.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains a storage module that stores credentials using the Django ORM."""

from oauth2client import client


class DjangoORMStorage(client.Storage):
    """Store and retrieve a single credential to and from the Django datastore.

    This Storage helper presumes the Credentials
    have been stored as a CredentialsField
    on a db model class.
    """

    def __init__(self, model_class, key_name, key_value, property_name):
        """Constructor for Storage.

        Args:
            model: string, fully qualified name of db.Model model class.
            key_name: string, key name for the entity that has the credentials
            key_value: string, key value for the entity that has the
               credentials.
            property_name: string, name of the property that is an
                           CredentialsProperty.
        """
        super(DjangoORMStorage, self).__init__()
        self.model_class = model_class
        self.key_name = key_name
        self.key_value = key_value
        self.property_name = property_name

    def locked_get(self):
        """Retrieve stored credential from the Django ORM.

        Returns:
            oauth2client.Credentials retrieved from the Django ORM, associated
             with the ``model``, ``key_value``->``key_name`` pair used to query
             for the model, and ``property_name`` identifying the
             ``CredentialsProperty`` field, all of which are defined in the
             constructor for this Storage object.

        """
        query = {self.key_name: self.key_value}
        entities = self.model_class.objects.filter(**query)
        if len(entities) > 0:
            credential = getattr(entities[0], self.property_name)
            if getattr(credential, 'set_store', None) is not None:
                credential.set_store(self)
            return credential
        else:
            return None

    def locked_put(self, credentials):
        """Write a Credentials to the Django datastore.

        Args:
            credentials: Credentials, the credentials to store.
        """
        entity, _ = self.model_class.objects.get_or_create(
            **{self.key_name: self.key_value})

        setattr(entity, self.property_name, credentials)
        entity.save()

    def locked_delete(self):
        """Delete Credentials from the datastore."""
        query = {self.key_name: self.key_value}
        self.model_class.objects.filter(**query).delete()
