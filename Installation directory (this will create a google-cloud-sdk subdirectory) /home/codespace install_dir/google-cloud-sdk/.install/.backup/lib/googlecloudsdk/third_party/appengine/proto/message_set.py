# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Copyright 2005 Google LLC.

"""This module contains the MessageSet class, which is a special kind of
protocol message which can contain other protocol messages without knowing
their types.  See the class's doc string for more information."""

# When a MessageSet is first parsed, it contains a set of strings.  It
# can't parse these to the final message types until it knows what type they
# are.  When the user first requests a particular message type, the actual
# class implementing the message type is captured for the MessageSet to
# use.  The string is then replaced with its fully-parsed equivalent.  Thus,
# each message is only parsed on-demand, the first time it is requested.

from googlecloudsdk.third_party.appengine.proto import ProtocolBuffer
from googlecloudsdk.core import log

# Degrade gracefully for users of the :pure_pyproto target who depend on
# some MessageSet functionality, but cannot include this C++ extension.
try:
  from googlecloudsdk.third_party.appengine.proto import _net_proto___parse__python
except ImportError:
  _net_proto___parse__python = None

# Tags byte values used in the wire format of MessageSet.
TAG_BEGIN_ITEM_GROUP = 11
TAG_END_ITEM_GROUP   = 12
TAG_TYPE_ID          = 16
TAG_MESSAGE          = 26

class Item:
  """This class is used internally by MessageSet.

  This class represents a particular message in the set.  The message may be
  either parsed or unparsed.  The point of this class is to provide a nice
  wrapper for all of the standard protocol buffer operations so that the
  caller does not have to check if the message is parsed or not."""

  def __init__(self, message, message_class=None):
    self.message = message
    self.message_class = message_class

  def SetToDefaultInstance(self, message_class):
    self.message = message_class()
    self.message_class = message_class

  def Parse(self, message_class):
    """Upgrades the Item to a parsed one, returning true if successful."""

    if self.message_class is not None:
      return 1

    try:
      message_obj = message_class()
      message_obj.MergePartialFromString(self.message)
      self.message = message_obj
      self.message_class = message_class
      return 1
    except ProtocolBuffer.ProtocolBufferDecodeError:
      logging.warn("Parse error in message inside MessageSet.  Tried "
                   "to parse as: " + message_class.__name__)
      return 0

  def MergeFrom(self, other):
    """Merges two items.

    If one item is parsed and one is not, an attempt will be made to parse
    the unparsed one."""

    if self.message_class is not None:
      if other.Parse(self.message_class):
        self.message.MergeFrom(other.message)
      # Pretend other was empty if it didn't parse, since callers to MergeFrom
      # don't expect to handle errors.

    elif other.message_class is not None:
      if not self.Parse(other.message_class):
        # Pretend self was empty if it didn't parse.
        self.message = other.message_class()
        self.message_class = other.message_class
      self.message.MergeFrom(other.message)

    else:
      self.message += other.message

  def Copy(self):
    """Make a deep copy of the Item."""

    if self.message_class is None:
      return Item(self.message)
    else:
      new_message = self.message_class()
      new_message.CopyFrom(self.message)
      return Item(new_message, self.message_class)

  def Equals(self, other):
    """Check if two items are equal.

    If one message is parsed and the other is not, an attempt will be made
    to parse the unparsed one."""

    if self.message_class is not None:
      if not other.Parse(self.message_class): return 0
      return self.message.Equals(other.message)

    elif other.message_class is not None:
      if not self.Parse(other.message_class): return 0
      return self.message.Equals(other.message)

    else:
      return self.message == other.message

  def IsInitialized(self, debug_strs=None):
    """Calls IsInitialized on the contained message if it is parsed, or just
    returns true otherwise."""

    if self.message_class is None:
      return 1
    else:
      return self.message.IsInitialized(debug_strs)

  def ByteSize(self, pb, type_id):
    """Returns the encoded size of this item."""

    message_length = 0
    if self.message_class is None:
      message_length = len(self.message)
    else:
      message_length = self.message.ByteSize()

    # Extra two bytes is tags for type_id and message.
    return pb.lengthString(message_length) + pb.lengthVarInt64(type_id) + 2

  def ByteSizePartial(self, pb, type_id):
    """Returns the encoded size of this item, not counting missing optional."""

    message_length = 0
    if self.message_class is None:
      message_length = len(self.message)
    else:
      message_length = self.message.ByteSizePartial()

    # Extra two bytes is tags for type_id and message.
    return pb.lengthString(message_length) + pb.lengthVarInt64(type_id) + 2

  def OutputUnchecked(self, out, type_id):
    """Writes the item to the decoder "out", given its type ID."""

    out.putVarInt32(TAG_TYPE_ID)
    # Type IDs are defined as being 32-bit as of this writing, but could
    # become 64-bit in the future.  Since putVarInt32() is just a wrapper
    # for putVarUint64() with added bounds checking, we might as well use
    # the 64-bit version now.
    out.putVarUint64(type_id)
    out.putVarInt32(TAG_MESSAGE)
    if self.message_class is None:
      out.putPrefixedString(self.message)
    else:
      out.putVarInt32(self.message.ByteSize())
      self.message.OutputUnchecked(out)

  def OutputPartial(self, out, type_id):
    """Writes the item to the decoder "out", given its type ID.
    Does not assume required fields are set."""

    out.putVarInt32(TAG_TYPE_ID)
    # Type IDs are defined as being 32-bit as of this writing, but could
    # become 64-bit in the future.  Since putVarInt32() is just a wrapper
    # for putVarUint64() with added bounds checking, we might as well use
    # the 64-bit version now.
    out.putVarUint64(type_id)
    out.putVarInt32(TAG_MESSAGE)
    if self.message_class is None:
      out.putPrefixedString(self.message)
    else:
      out.putVarInt32(self.message.ByteSizePartial())
      self.message.OutputPartial(out)

  def Decode(decoder):
    """Decodes a type_id and message buffer from the decoder.  (static)

    Returns a (type_id, message) tuple."""

    type_id = 0
    message = None
    while 1:
      tag = decoder.getVarInt32()
      if tag == TAG_END_ITEM_GROUP:
        break
      if tag == TAG_TYPE_ID:
        # Type IDs are defined as being 32-bit as of this writing, but could
        # become 64-bit in the future.  Since getVarInt32() is just a wrapper
        # for getVarUint64() with added bounds hcecking, we might as well use
        # the 64-bit version now.
        type_id = decoder.getVarUint64()
        continue
      if tag == TAG_MESSAGE:
        message = decoder.getPrefixedString()
        continue
      # tag 0 is special: it's used to indicate an error.
      # so if we see it we raise an exception.
      if tag == 0: raise ProtocolBuffer.ProtocolBufferDecodeError
      decoder.skipData(tag)

    if type_id == 0 or message is None:
      raise ProtocolBuffer.ProtocolBufferDecodeError
    return (type_id, message)
  Decode = staticmethod(Decode)


class MessageSet(ProtocolBuffer.ProtocolMessage):
  """A protocol message which contains other protocol messages.

  This class is a specially-crafted ProtocolMessage which represents a
  container storing other protocol messages.  The contained messages can be
  of any protocol message type which has been assigned a unique type
  identifier.  No two messages in the MessageSet may have the same type,
  but otherwise there are no restrictions on what you can put in it.  Accessing
  the stored messages involves passing the class objects representing the
  types you are looking for:
    assert myMessageSet.has(MyMessageType)
    message = myMessageSet.get(MyMessageType)
    message = myMessageSet.mutable(MyMessageType)
    myMessageSet.remove(MyMessageType)

  Message types designed to be stored in MessageSets must have unique
  32-bit type identifiers.  Give your message type an identifier like so:
    parsed message MyMessageType {
      enum TypeId {MESSAGE_TYPE_ID = 12345678};
  To insure that your type ID is unique, use one of your perforce change
  numbers.  Just make sure you only use your own numbers and that you don't
  use the same one twice.

  The wire format of a MessageSet looks like this:
     parsed message MessageSet {
       repeated group Item = 1 {
         required fixed32 type_id = 2;
         required message<RawMessage> message = 3;
       };
     };
  The MessageSet class provides a special interface around this format for
  the sake of ease-of-use and type safety.

  See message_set_unittest.proto and message_set_py_unittest.py for examples.
  """

  def __init__(self, contents=None):
    """Construct a new MessageSet, with optional starting contents
    in binary protocol buffer format."""
    self.items = dict()
    if contents is not None: self.MergeFromString(contents)

  # -------------------------------------------------------------------
  # MessageSet standard interface.

  def get(self, message_class):
    """Gets a message of the given type from the set.

    If the MessageSet contains no message of that type, a default instance
    of the class is returned.  This is done to match the behavior of the
    accessors normally generated for an optional field of a protocol message.
    This makes it easier to transition from a long list of optional fields
    to a MessageSet.

    The returned message should not be modified.
    """

    if message_class.MESSAGE_TYPE_ID not in self.items:
      return message_class()
    item = self.items[message_class.MESSAGE_TYPE_ID]
    if item.Parse(message_class):
      return item.message
    else:
      return message_class()

  def mutable(self, message_class):
    """Gets a mutable reference to a message of the given type in the set.

    If the MessageSet contains no message of that type, one is created and
    added to the set.
    """

    if message_class.MESSAGE_TYPE_ID not in self.items:
      message = message_class()
      self.items[message_class.MESSAGE_TYPE_ID] = Item(message, message_class)
      return message
    item = self.items[message_class.MESSAGE_TYPE_ID]
    if not item.Parse(message_class):
      item.SetToDefaultInstance(message_class)
    return item.message

  def has(self, message_class):
    """Checks if the set contains a message of the given type."""

    if message_class.MESSAGE_TYPE_ID not in self.items:
      return 0
    item = self.items[message_class.MESSAGE_TYPE_ID]
    return item.Parse(message_class)

  def has_unparsed(self, message_class):
    """Checks if the set contains an unparsed message of the given type.

    This differs from has() when the set contains a message of the given type
    with a parse error.  has() will return false when this is the case, but
    has_unparsed() will return true.  This is only useful for error checking.
    """
    return message_class.MESSAGE_TYPE_ID in self.items

  def GetTypeIds(self):
    """Return a list of all type ids in the set.

    Returns:
      [ cls1.MESSAGE_TYPE_ID, ... ] for each cls in the set.  The returned
      list does not contain duplicates.
    """
    return self.items.keys()

  def NumMessages(self):
    """Return the number of messages in the set.  For any set the following
    invariant holds:
      set.NumMessages() == len(set.GetTypeIds())

    Returns:
      number of messages in the set
    """
    return len(self.items)

  def remove(self, message_class):
    """Removes any message of the given type from the set."""
    if message_class.MESSAGE_TYPE_ID in self.items:
      del self.items[message_class.MESSAGE_TYPE_ID]

  # -------------------------------------------------------------------
  # Python container methods.

  def __getitem__(self, message_class):
    if message_class.MESSAGE_TYPE_ID not in self.items:
      raise KeyError(message_class)
    item = self.items[message_class.MESSAGE_TYPE_ID]
    if item.Parse(message_class):
      return item.message
    else:
      raise KeyError(message_class)

  def __setitem__(self, message_class, message):
    self.items[message_class.MESSAGE_TYPE_ID] = Item(message, message_class)

  def __contains__(self, message_class):
    return self.has(message_class)

  def __delitem__(self, message_class):
    self.remove(message_class)

  def __len__(self):
    return len(self.items)

  # -------------------------------------------------------------------
  # Standard ProtocolMessage interface.

  def MergeFrom(self, other):
    """Merges the messages from MessageSet 'other' into this set.

    If both sets contain messages of matching types, those messages will be
    individually merged by type.
    """

    assert other is not self

    for (type_id, item) in other.items.items():
      if type_id in self.items:
        self.items[type_id].MergeFrom(item)
      else:
        self.items[type_id] = item.Copy()

  def Equals(self, other):
    """Checks if two MessageSets are equal."""
    if other is self: return 1
    if len(self.items) != len(other.items): return 0

    for (type_id, item) in other.items.items():
      if type_id not in self.items: return 0
      if not self.items[type_id].Equals(item): return 0

    return 1

  def __eq__(self, other):
    return ((other is not None)
        and (other.__class__ == self.__class__)
        and self.Equals(other))

  def __ne__(self, other):
    return not (self == other)

  def IsInitialized(self, debug_strs=None):
    """Checks if all messages in this set have had all of their required fields
    set."""

    initialized = 1
    for item in self.items.values():
      if not item.IsInitialized(debug_strs):
        initialized = 0
    return initialized

  def ByteSize(self):
    """Gets the byte size of a protocol buffer representing this MessageSet."""
    n = 2 * len(self.items)  # 2 bytes for group start and end tags
    for (type_id, item) in self.items.items():
      n += item.ByteSize(self, type_id)
    return n

  def ByteSizePartial(self):
    """Gets the byte size of a protocol buffer representing this MessageSet.
    Does not count missing required fields."""
    n = 2 * len(self.items)  # 2 bytes for group start and end tags
    for (type_id, item) in self.items.items():
      n += item.ByteSizePartial(self, type_id)
    return n

  def Clear(self):
    """Removes all messages from the set."""
    self.items = dict()

  def OutputUnchecked(self, out):
    """Writes the MessageSet to the encoder 'out'."""
    for (type_id, item) in self.items.items():
      out.putVarInt32(TAG_BEGIN_ITEM_GROUP)
      item.OutputUnchecked(out, type_id)
      out.putVarInt32(TAG_END_ITEM_GROUP)

  def OutputPartial(self, out):
    """Writes the MessageSet to the encoder 'out'.
    Does not assume required fields are set."""
    for (type_id, item) in self.items.items():
      out.putVarInt32(TAG_BEGIN_ITEM_GROUP)
      item.OutputPartial(out, type_id)
      out.putVarInt32(TAG_END_ITEM_GROUP)

  def TryMerge(self, decoder):
    """Attempts to decode a MessageSet from the decoder 'd' and merge it
    with this one."""
    while decoder.avail() > 0:
      tag = decoder.getVarInt32()
      if tag == TAG_BEGIN_ITEM_GROUP:
        (type_id, message) = Item.Decode(decoder)
        if type_id in self.items:
          self.items[type_id].MergeFrom(Item(message))
        else:
          self.items[type_id] = Item(message)
        continue
      # tag 0 is special: it's used to indicate an error.
      # so if we see it we raise an exception.
      if (tag == 0): raise ProtocolBuffer.ProtocolBufferDecodeError
      decoder.skipData(tag)

  # ASCII serialization.  Only available through C++ extension.
  def _CToASCII(self, output_format):
    if _net_proto___parse__python is None:
      return ProtocolBuffer.ProtocolMessage._CToASCII(self, output_format)
    else:
      return _net_proto___parse__python.ToASCII(
          self, "MessageSetInternal", output_format)

  def ParseASCII(self, s):
    if _net_proto___parse__python is None:
      ProtocolBuffer.ProtocolMessage.ParseASCII(self, s)
    else:
      _net_proto___parse__python.ParseASCII(self, "MessageSetInternal", s)

  def ParseASCIIIgnoreUnknown(self, s):
    if _net_proto___parse__python is None:
      ProtocolBuffer.ProtocolMessage.ParseASCIIIgnoreUnknown(self, s)
    else:
      _net_proto___parse__python.ParseASCIIIgnoreUnknown(
          self, "MessageSetInternal", s)

  # NOTE(user): Use ToASCII() rather than __str__() for ASCII serialization.
  # This legacy implementation has several quirks:
  # - Does not qualify message names by package, so it will print "Message"
  #   from package foo.bar as [Message] rather than [foo.bar.Message].
  # - Only knows about messages previously seen by its class instance, and
  #   may print byte counts in place of message data.
  def __str__(self, prefix="", printElemNumber=0):
    text = ""
    for (type_id, item) in self.items.items():
      if item.message_class is None:
        text += "%s[%d] <\n" % (prefix, type_id)
        text += "%s  (%d bytes)\n" % (prefix, len(item.message))
        text += "%s>\n" % prefix
      else:
        text += "%s[%s] <\n" % (prefix, item.message_class.__name__)
        text += item.message.__str__(prefix + "  ", printElemNumber)
        text += "%s>\n" % prefix
    return text

  # To allow MessageSet to be used as an extension type. (b/6401336)
  _PROTO_DESCRIPTOR_NAME = 'MessageSet'

__all__ = ['MessageSet']
