# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Testing utilties for pyu2f.

Testing utilities such as a fake implementation of the pyhidapi device object
that implements parts of the U2FHID frame protocol.  This makes it easy to tests
of higher level abstractions without having to use mock to mock out low level
framing details.
"""
from pyu2f import hidtransport
from pyu2f.hid import base


class UnsupportedCommandError(Exception):
  pass


class FakeHidDevice(base.HidDevice):
  """Implements a fake hiddevice per the pyhidapi interface.

  This class implemetns a fake hiddevice that can be patched into
  code that uses pyhidapi to communicate with a hiddevice.  This device
  impelents part of U2FHID protocol and can be used to test interactions
  with a security key.  It supports arbitrary MSG replies as well as
  channel allocation, and ping.
  """

  def __init__(self, cid_to_allocate, msg_reply=None):
    self.cid_to_allocate = cid_to_allocate
    self.msg_reply = msg_reply
    self.transaction_active = False
    self.full_packet_received = False
    self.init_packet = None
    self.packet_body = None
    self.reply = None
    self.seq = 0
    self.received_packets = []
    self.busy_count = 0

  def GetInReportDataLength(self):
    return 64

  def GetOutReportDataLength(self):
    return 64

  def Write(self, data):
    """Write to the device.

    Writes to the fake hid device.  This function is stateful: if a transaction
    is currently open with the client, it will continue to accumulate data
    for the client->device messages until the expected size is reached.

    Args:
      data: A list of integers to accept as data payload.  It should be 64 bytes
          in length: just the report data--NO report ID.
    """

    if len(data) < 64:
      data = bytearray(data) + bytearray(0 for i in range(0, 64 - len(data)))

    if not self.transaction_active:
      self.transaction_active = True
      self.init_packet = hidtransport.UsbHidTransport.InitPacket.FromWireFormat(
          64, data)
      self.packet_body = self.init_packet.payload
      self.full_packet_received = False
      self.received_packets.append(self.init_packet)
    else:
      cont_packet = hidtransport.UsbHidTransport.ContPacket.FromWireFormat(
          64, data)
      self.packet_body += cont_packet.payload
      self.received_packets.append(cont_packet)

    if len(self.packet_body) >= self.init_packet.size:
      self.packet_body = self.packet_body[0:self.init_packet.size]
      self.full_packet_received = True

  def Read(self):
    """Read from the device.

    Reads from the fake hid device.  This function only works if a transaction
    is open and a complete write has taken place.  If so, it will return the
    next reply packet.  It should be called repeatedly until all expected
    data has been received.  It always reads one report.

    Returns:
      A list of ints containing the next packet.

    Raises:
      UnsupportedCommandError: if the requested amount is not 64.
    """
    if not self.transaction_active or not self.full_packet_received:
      return None

    ret = None
    if self.busy_count > 0:
      ret = hidtransport.UsbHidTransport.InitPacket(
          64, self.init_packet.cid, hidtransport.UsbHidTransport.U2FHID_ERROR,
          1, hidtransport.UsbHidTransport.ERR_CHANNEL_BUSY)
      self.busy_count -= 1
    elif self.reply:  # reply in progress
      next_frame = self.reply[0:59]
      self.reply = self.reply[59:]

      ret = hidtransport.UsbHidTransport.ContPacket(64, self.init_packet.cid,
                                                    self.seq, next_frame)
      self.seq += 1
    else:
      self.InternalGenerateReply()
      first_frame = self.reply[0:57]

      ret = hidtransport.UsbHidTransport.InitPacket(
          64, self.init_packet.cid, self.init_packet.cmd, len(self.reply),
          first_frame)
      self.reply = self.reply[57:]

    if not self.reply:  # done after this packet
      self.reply = None
      self.transaction_active = False
      self.seq = 0

    return ret.ToWireFormat()

  def SetChannelBusyCount(self, busy_count):  # pylint: disable=invalid-name
    """Mark the channel busy for next busy_count read calls."""
    self.busy_count = busy_count

  def InternalGenerateReply(self):  # pylint: disable=invalid-name
    if self.init_packet.cmd == hidtransport.UsbHidTransport.U2FHID_INIT:
      nonce = self.init_packet.payload[0:8]
      self.reply = nonce + self.cid_to_allocate + bytearray(
          b'\x01\x00\x00\x00\x00')
    elif self.init_packet.cmd == hidtransport.UsbHidTransport.U2FHID_PING:
      self.reply = self.init_packet.payload
    elif self.init_packet.cmd == hidtransport.UsbHidTransport.U2FHID_MSG:
      self.reply = self.msg_reply
    else:
      raise UnsupportedCommandError()
