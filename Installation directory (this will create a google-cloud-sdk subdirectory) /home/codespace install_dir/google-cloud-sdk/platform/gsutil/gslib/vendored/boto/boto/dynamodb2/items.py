from copy import deepcopy


class NEWVALUE(object):
    # A marker for new data added.
    pass


class Item(object):
    """
    An object representing the item data within a DynamoDB table.

    An item is largely schema-free, meaning it can contain any data. The only
    limitation is that it must have data for the fields in the ``Table``'s
    schema.

    This object presents a dictionary-like interface for accessing/storing
    data. It also tries to intelligently track how data has changed throughout
    the life of the instance, to be as efficient as possible about updates.

    Empty items, or items that have no data, are considered falsey.

    """
    def __init__(self, table, data=None, loaded=False):
        """
        Constructs an (unsaved) ``Item`` instance.

        To persist the data in DynamoDB, you'll need to call the ``Item.save``
        (or ``Item.partial_save``) on the instance.

        Requires a ``table`` parameter, which should be a ``Table`` instance.
        This is required, as DynamoDB's API is focus around all operations
        being table-level. It's also for persisting schema around many objects.

        Optionally accepts a ``data`` parameter, which should be a dictionary
        of the fields & values of the item. Alternatively, an ``Item`` instance
        may be provided from which to extract the data.

        Optionally accepts a ``loaded`` parameter, which should be a boolean.
        ``True`` if it was preexisting data loaded from DynamoDB, ``False`` if
        it's new data from the user. Default is ``False``.

        Example::

            >>> users = Table('users')
            >>> user = Item(users, data={
            ...     'username': 'johndoe',
            ...     'first_name': 'John',
            ...     'date_joined': 1248o61592,
            ... })

            # Change existing data.
            >>> user['first_name'] = 'Johann'
            # Add more data.
            >>> user['last_name'] = 'Doe'
            # Delete data.
            >>> del user['date_joined']

            # Iterate over all the data.
            >>> for field, val in user.items():
            ...     print "%s: %s" % (field, val)
            username: johndoe
            first_name: John
            date_joined: 1248o61592

        """
        self.table = table
        self._loaded = loaded
        self._orig_data = {}
        self._data = data
        self._dynamizer = table._dynamizer

        if isinstance(self._data, Item):
            self._data = self._data._data
        if self._data is None:
            self._data = {}

        if self._loaded:
            self._orig_data = deepcopy(self._data)

    def __getitem__(self, key):
        return self._data.get(key, None)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        if not key in self._data:
            return

        del self._data[key]

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __iter__(self):
        for key in self._data:
            yield self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __bool__(self):
        return bool(self._data)

    __nonzero__ = __bool__

    def _determine_alterations(self):
        """
        Checks the ``-orig_data`` against the ``_data`` to determine what
        changes to the data are present.

        Returns a dictionary containing the keys ``adds``, ``changes`` &
        ``deletes``, containing the updated data.
        """
        alterations = {
            'adds': {},
            'changes': {},
            'deletes': [],
        }

        orig_keys = set(self._orig_data.keys())
        data_keys = set(self._data.keys())

        # Run through keys we know are in both for changes.
        for key in orig_keys.intersection(data_keys):
            if self._data[key] != self._orig_data[key]:
                if self._is_storable(self._data[key]):
                    alterations['changes'][key] = self._data[key]
                else:
                    alterations['deletes'].append(key)

        # Run through additions.
        for key in data_keys.difference(orig_keys):
            if self._is_storable(self._data[key]):
                alterations['adds'][key] = self._data[key]

        # Run through deletions.
        for key in orig_keys.difference(data_keys):
            alterations['deletes'].append(key)

        return alterations

    def needs_save(self, data=None):
        """
        Returns whether or not the data has changed on the ``Item``.

        Optionally accepts a ``data`` argument, which accepts the output from
        ``self._determine_alterations()`` if you've already called it. Typically
        unnecessary to do. Default is ``None``.

        Example:

            >>> user.needs_save()
            False
            >>> user['first_name'] = 'Johann'
            >>> user.needs_save()
            True

        """
        if data is None:
            data = self._determine_alterations()

        needs_save = False

        for kind in ['adds', 'changes', 'deletes']:
            if len(data[kind]):
                needs_save = True
                break

        return needs_save

    def mark_clean(self):
        """
        Marks an ``Item`` instance as no longer needing to be saved.

        Example:

            >>> user.needs_save()
            False
            >>> user['first_name'] = 'Johann'
            >>> user.needs_save()
            True
            >>> user.mark_clean()
            >>> user.needs_save()
            False

        """
        self._orig_data = deepcopy(self._data)

    def mark_dirty(self):
        """
        DEPRECATED: Marks an ``Item`` instance as needing to be saved.

        This method is no longer necessary, as the state tracking on ``Item``
        has been improved to automatically detect proper state.
        """
        return

    def load(self, data):
        """
        This is only useful when being handed raw data from DynamoDB directly.
        If you have a Python datastructure already, use the ``__init__`` or
        manually set the data instead.

        Largely internal, unless you know what you're doing or are trying to
        mix the low-level & high-level APIs.
        """
        self._data = {}

        for field_name, field_value in data.get('Item', {}).items():
            self[field_name] = self._dynamizer.decode(field_value)

        self._loaded = True
        self._orig_data = deepcopy(self._data)

    def get_keys(self):
        """
        Returns a Python-style dict of the keys/values.

        Largely internal.
        """
        key_fields = self.table.get_key_fields()
        key_data = {}

        for key in key_fields:
            key_data[key] = self[key]

        return key_data

    def get_raw_keys(self):
        """
        Returns a DynamoDB-style dict of the keys/values.

        Largely internal.
        """
        raw_key_data = {}

        for key, value in self.get_keys().items():
            raw_key_data[key] = self._dynamizer.encode(value)

        return raw_key_data

    def build_expects(self, fields=None):
        """
        Builds up a list of expecations to hand off to DynamoDB on save.

        Largely internal.
        """
        expects = {}

        if fields is None:
            fields = list(self._data.keys()) + list(self._orig_data.keys())

        # Only uniques.
        fields = set(fields)

        for key in fields:
            expects[key] = {
                'Exists': True,
            }
            value = None

            # Check for invalid keys.
            if not key in self._orig_data and not key in self._data:
                raise ValueError("Unknown key %s provided." % key)

            # States:
            # * New field (only in _data)
            # * Unchanged field (in both _data & _orig_data, same data)
            # * Modified field (in both _data & _orig_data, different data)
            # * Deleted field (only in _orig_data)
            orig_value = self._orig_data.get(key, NEWVALUE)
            current_value = self._data.get(key, NEWVALUE)

            if orig_value == current_value:
                # Existing field unchanged.
                value = current_value
            else:
                if key in self._data:
                    if not key in self._orig_data:
                        # New field.
                        expects[key]['Exists'] = False
                    else:
                        # Existing field modified.
                        value = orig_value
                else:
                   # Existing field deleted.
                    value = orig_value

            if value is not None:
                expects[key]['Value'] = self._dynamizer.encode(value)

        return expects

    def _is_storable(self, value):
        # We need to prevent ``None``, empty string & empty set from
        # heading to DDB, but allow false-y values like 0 & False make it.
        if not value:
            if not value in (0, 0.0, False):
                return False

        return True

    def prepare_full(self):
        """
        Runs through all fields & encodes them to be handed off to DynamoDB
        as part of an ``save`` (``put_item``) call.

        Largely internal.
        """
        # This doesn't save on its own. Rather, we prepare the datastructure
        # and hand-off to the table to handle creation/update.
        final_data = {}

        for key, value in self._data.items():
            if not self._is_storable(value):
                continue

            final_data[key] = self._dynamizer.encode(value)

        return final_data

    def prepare_partial(self):
        """
        Runs through **ONLY** the changed/deleted fields & encodes them to be
        handed off to DynamoDB as part of an ``partial_save`` (``update_item``)
        call.

        Largely internal.
        """
        # This doesn't save on its own. Rather, we prepare the datastructure
        # and hand-off to the table to handle creation/update.
        final_data = {}
        fields = set()
        alterations = self._determine_alterations()

        for key, value in alterations['adds'].items():
            final_data[key] = {
                'Action': 'PUT',
                'Value': self._dynamizer.encode(self._data[key])
            }
            fields.add(key)

        for key, value in alterations['changes'].items():
            final_data[key] = {
                'Action': 'PUT',
                'Value': self._dynamizer.encode(self._data[key])
            }
            fields.add(key)

        for key in alterations['deletes']:
            final_data[key] = {
                'Action': 'DELETE',
            }
            fields.add(key)

        return final_data, fields

    def partial_save(self):
        """
        Saves only the changed data to DynamoDB.

        Extremely useful for high-volume/high-write data sets, this allows
        you to update only a handful of fields rather than having to push
        entire items. This prevents many accidental overwrite situations as
        well as saves on the amount of data to transfer over the wire.

        Returns ``True`` on success, ``False`` if no save was performed or
        the write failed.

        Example::

            >>> user['last_name'] = 'Doh!'
            # Only the last name field will be sent to DynamoDB.
            >>> user.partial_save()

        """
        key = self.get_keys()
        # Build a new dict of only the data we're changing.
        final_data, fields = self.prepare_partial()

        if not final_data:
            return False

        # Remove the key(s) from the ``final_data`` if present.
        # They should only be present if this is a new item, in which
        # case we shouldn't be sending as part of the data to update.
        for fieldname, value in key.items():
            if fieldname in final_data:
                del final_data[fieldname]

                try:
                    # It's likely also in ``fields``, so remove it there too.
                    fields.remove(fieldname)
                except KeyError:
                    pass

        # Build expectations of only the fields we're planning to update.
        expects = self.build_expects(fields=fields)
        returned = self.table._update_item(key, final_data, expects=expects)
        # Mark the object as clean.
        self.mark_clean()
        return returned

    def save(self, overwrite=False):
        """
        Saves all data to DynamoDB.

        By default, this attempts to ensure that none of the underlying
        data has changed. If any fields have changed in between when the
        ``Item`` was constructed & when it is saved, this call will fail so
        as not to cause any data loss.

        If you're sure possibly overwriting data is acceptable, you can pass
        an ``overwrite=True``. If that's not acceptable, you may be able to use
        ``Item.partial_save`` to only write the changed field data.

        Optionally accepts an ``overwrite`` parameter, which should be a
        boolean. If you provide ``True``, the item will be forcibly overwritten
        within DynamoDB, even if another process changed the data in the
        meantime. (Default: ``False``)

        Returns ``True`` on success, ``False`` if no save was performed.

        Example::

            >>> user['last_name'] = 'Doh!'
            # All data on the Item is sent to DynamoDB.
            >>> user.save()

            # If it fails, you can overwrite.
            >>> user.save(overwrite=True)

        """
        if not self.needs_save() and not overwrite:
            return False

        final_data = self.prepare_full()
        expects = None

        if overwrite is False:
            # Build expectations about *all* of the data.
            expects = self.build_expects()

        returned = self.table._put_item(final_data, expects=expects)
        # Mark the object as clean.
        self.mark_clean()
        return returned

    def delete(self):
        """
        Deletes the item's data to DynamoDB.

        Returns ``True`` on success.

        Example::

            # Buh-bye now.
            >>> user.delete()

        """
        key_data = self.get_keys()
        return self.table.delete_item(**key_data)
