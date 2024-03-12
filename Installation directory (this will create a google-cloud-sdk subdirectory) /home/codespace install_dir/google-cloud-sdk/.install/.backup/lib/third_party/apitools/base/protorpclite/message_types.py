#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
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
#

"""Simple protocol message types.

Includes new message and field types that are outside what is defined by the
protocol buffers standard.
"""
import datetime

from apitools.base.protorpclite import messages
from apitools.base.protorpclite import util

__all__ = [
    'DateTimeField',
    'DateTimeMessage',
    'VoidMessage',
]


class VoidMessage(messages.Message):
    """Empty message."""


class DateTimeMessage(messages.Message):
    """Message to store/transmit a DateTime.

    Fields:
      milliseconds: Milliseconds since Jan 1st 1970 local time.
      time_zone_offset: Optional time zone offset, in minutes from UTC.
    """
    milliseconds = messages.IntegerField(1, required=True)
    time_zone_offset = messages.IntegerField(2)


class DateTimeField(messages.MessageField):
    """Field definition for datetime values.

    Stores a python datetime object as a field.  If time zone information is
    included in the datetime object, it will be included in
    the encoded data when this is encoded/decoded.
    """

    type = datetime.datetime

    message_type = DateTimeMessage

    @util.positional(3)
    def __init__(self,
                 number,
                 **kwargs):
        super(DateTimeField, self).__init__(self.message_type,
                                            number,
                                            **kwargs)

    def value_from_message(self, message):
        """Convert DateTimeMessage to a datetime.

        Args:
          A DateTimeMessage instance.

        Returns:
          A datetime instance.
        """
        message = super(DateTimeField, self).value_from_message(message)
        if message.time_zone_offset is None:
            return datetime.datetime.utcfromtimestamp(
                message.milliseconds / 1000.0)

        # Need to subtract the time zone offset, because when we call
        # datetime.fromtimestamp, it will add the time zone offset to the
        # value we pass.
        milliseconds = (message.milliseconds -
                        60000 * message.time_zone_offset)

        timezone = util.TimeZoneOffset(message.time_zone_offset)
        return datetime.datetime.fromtimestamp(milliseconds / 1000.0,
                                               tz=timezone)

    def value_to_message(self, value):
        value = super(DateTimeField, self).value_to_message(value)
        # First, determine the delta from the epoch, so we can fill in
        # DateTimeMessage's milliseconds field.
        if value.tzinfo is None:
            time_zone_offset = 0
            local_epoch = datetime.datetime.utcfromtimestamp(0)
        else:
            time_zone_offset = util.total_seconds(
                value.tzinfo.utcoffset(value))
            # Determine Jan 1, 1970 local time.
            local_epoch = datetime.datetime.fromtimestamp(-time_zone_offset,
                                                          tz=value.tzinfo)
        delta = value - local_epoch

        # Create and fill in the DateTimeMessage, including time zone if
        # one was specified.
        message = DateTimeMessage()
        message.milliseconds = int(util.total_seconds(delta) * 1000)
        if value.tzinfo is not None:
            utc_offset = value.tzinfo.utcoffset(value)
            if utc_offset is not None:
                message.time_zone_offset = int(
                    util.total_seconds(value.tzinfo.utcoffset(value)) / 60)

        return message
