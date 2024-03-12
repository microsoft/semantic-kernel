# Copyright 2016 Google Inc.  All rights reserved.
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

"""Contains classes used for the Django ORM storage."""

import base64
import pickle

from django.db import models
from django.utils import encoding

import oauth2client


class CredentialsField(models.Field):
    """Django ORM field for storing OAuth2 Credentials."""

    def __init__(self, *args, **kwargs):
        if 'null' not in kwargs:
            kwargs['null'] = True
        super(CredentialsField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'BinaryField'

    def from_db_value(self, value, expression, connection, context):
        """Overrides ``models.Field`` method. This converts the value
        returned from the database to an instance of this class.
        """
        return self.to_python(value)

    def to_python(self, value):
        """Overrides ``models.Field`` method. This is used to convert
        bytes (from serialization etc) to an instance of this class"""
        if value is None:
            return None
        elif isinstance(value, oauth2client.client.Credentials):
            return value
        else:
            return pickle.loads(base64.b64decode(encoding.smart_bytes(value)))

    def get_prep_value(self, value):
        """Overrides ``models.Field`` method. This is used to convert
        the value from an instances of this class to bytes that can be
        inserted into the database.
        """
        if value is None:
            return None
        else:
            return encoding.smart_text(base64.b64encode(pickle.dumps(value)))

    def value_to_string(self, obj):
        """Convert the field value from the provided model to a string.

        Used during model serialization.

        Args:
            obj: db.Model, model object

        Returns:
            string, the serialized field value
        """
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)
