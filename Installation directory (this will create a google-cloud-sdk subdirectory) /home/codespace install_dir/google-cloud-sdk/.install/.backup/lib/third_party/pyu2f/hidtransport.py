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

"""HID Transport for U2F.

This module imports the U2F HID Transport protocol as well as methods
for discovering devices implementing this protocol.
"""
import logging
import os
import struct
import time

from pyu2f import errors
from pyu2f import hid


def HidUsageSelector(device):
  if device['usage_page'] == 0xf1d0 and device['usage'] == 0x01:
    return True
  return False


def DiscoverLocalHIDU2FDevices(selector=HidUsageSelector):
  for d in hid.Enumerate():
    if selector(d):
      try:
        dev = hid.Open(d['path'])
        yield UsbHidTransport(dev)
      except OSError:
        # Insufficient permissions to access device
        pass


class UsbHidTransport(object):
  """Implements the U2FHID transport protocol.

  This class implements the U2FHID transport protocol from the
  FIDO U2F specs.  This protocol manages fragmenting longer messages
  over a short hid frame (usually 64 bytes).  It exposes an APDU
  channel through the MSG command as well as a series of other commands
  for configuring and interacting with the device.
  """

  U2FHID_PING = 0x81
  U2FHID_MSG = 0x83
  U2FHID_WINK = 0x88
  U2FHID_PROMPT = 0x87
  U2FHID_INIT = 0x86
  U2FHID_LOCK = 0x84
  U2FHID_ERROR = 0xbf
  U2FHID_SYNC = 0xbc

  U2FHID_BROADCAST_CID = bytearray([0xff, 0xff, 0xff, 0xff])

  ERR_CHANNEL_BUSY = bytearray([0x06])

  class InitPacket(object):
    """Represent an initial U2FHID packet.

    Represent an initial U2FHID packet.  This packet contains
    metadata necessary to interpret the entire packet stream associated
    with a particular exchange (read or write).

    Attributes:
      packet_size: The size of the hid report (packet) used.  Usually 64.
      cid: The channel id for the connection to the device.
      size: The size of the entire message to be sent (including
          all continuation packets)
      payload: The portion of the message to put into the init packet.
          This must be smaller than packet_size - 7 (the overhead for
          an init packet).
    """

    def __init__(self, packet_size, cid, cmd, size, payload):
      self.packet_size = packet_size
      if len(cid) != 4 or cmd > 255 or size >= 2**16:
        raise errors.InvalidPacketError()
      if len(payload) > self.packet_size - 7:
        raise errors.InvalidPacketError()

      self.cid = cid  # byte array
      self.cmd = cmd  # number
      self.size = size  # number (full size of message)
      self.payload = payload  # byte array (for first packet)

    def ToWireFormat(self):
      """Serializes the packet."""
      ret = bytearray(64)
      ret[0:4] = self.cid
      ret[4] = self.cmd
      struct.pack_into('>H', ret, 5, self.size)
      ret[7:7 + len(self.payload)] = self.payload
      return list(map(int, ret))

    @staticmethod
    def FromWireFormat(packet_size, data):
      """Derializes the packet.

      Deserializes the packet from wire format.

      Args:
        packet_size: The size of all packets (usually 64)
        data: List of ints or bytearray containing the data from the wire.

      Returns:
        InitPacket object for specified data

      Raises:
        InvalidPacketError: if the data isn't a valid InitPacket
      """
      ba = bytearray(data)
      if len(ba) != packet_size:
        raise errors.InvalidPacketError()
      cid = ba[0:4]
      cmd = ba[4]
      size = struct.unpack('>H', bytes(ba[5:7]))[0]
      payload = ba[7:7 + size]  # might truncate at packet_size
      return UsbHidTransport.InitPacket(packet_size, cid, cmd, size, payload)

  class ContPacket(object):
    """Represents a continutation U2FHID packet.

    Represents a continutation U2FHID packet.  These packets follow
    the intial packet and contains the remaining data in a particular
    message.

    Attributes:
      packet_size: The size of the hid report (packet) used.  Usually 64.
      cid: The channel id for the connection to the device.
      seq: The sequence number for this continuation packet.  The first
          continuation packet is 0 and it increases from there.
      payload:  The payload to put into this continuation packet.  This
          must be less than packet_size - 5 (the overhead of the
          continuation packet is 5).
    """

    def __init__(self, packet_size, cid, seq, payload):
      self.packet_size = packet_size
      self.cid = cid
      self.seq = seq
      self.payload = payload
      if len(payload) > self.packet_size - 5:
        raise errors.InvalidPacketError()
      if seq > 127:
        raise errors.InvalidPacketError()

    def ToWireFormat(self):
      """Serializes the packet."""
      ret = bytearray(self.packet_size)
      ret[0:4] = self.cid
      ret[4] = self.seq
      ret[5:5 + len(self.payload)] = self.payload
      return list(map(int, ret))

    @staticmethod
    def FromWireFormat(packet_size, data):
      """Derializes the packet.

      Deserializes the packet from wire format.

      Args:
        packet_size: The size of all packets (usually 64)
        data: List of ints or bytearray containing the data from the wire.

      Returns:
        InitPacket object for specified data

      Raises:
        InvalidPacketError: if the data isn't a valid ContPacket
      """
      ba = bytearray(data)
      if len(ba) != packet_size:
        raise errors.InvalidPacketError()
      cid = ba[0:4]
      seq = ba[4]
      # We don't know the size limit a priori here without seeing the init
      # packet, so truncation needs to be done in the higher level protocol
      # handling code, unlike the degenerate case of a 1 packet message in an
      # init packet, where the size is known.
      payload = ba[5:]
      return UsbHidTransport.ContPacket(packet_size, cid, seq, payload)

  def __init__(self, hid_device, read_timeout_secs=3.0):
    self.hid_device = hid_device

    in_size = hid_device.GetInReportDataLength()
    out_size = hid_device.GetOutReportDataLength()
    if in_size != out_size:
      raise errors.HardwareError(
          'unsupported device with different in/out packet sizes.')
    if in_size == 0:
      raise errors.HardwareError('unable to determine packet size')

    self.packet_size = in_size
    self.read_timeout_secs = read_timeout_secs
    self.logger = logging.getLogger('pyu2f.hidtransport')

    self.InternalInit()

  def SendMsgBytes(self, msg):
    r = self.InternalExchange(UsbHidTransport.U2FHID_MSG, msg)
    return r

  def SendBlink(self, length):
    return self.InternalExchange(UsbHidTransport.U2FHID_PROMPT,
                                 bytearray([length]))

  def SendWink(self):
    return self.InternalExchange(UsbHidTransport.U2FHID_WINK, bytearray([]))

  def SendPing(self, data):
    return self.InternalExchange(UsbHidTransport.U2FHID_PING, data)

  def InternalInit(self):
    """Initializes the device and obtains channel id."""
    self.cid = UsbHidTransport.U2FHID_BROADCAST_CID
    nonce = bytearray(os.urandom(8))
    r = self.InternalExchange(UsbHidTransport.U2FHID_INIT, nonce)
    if len(r) < 17:
      raise errors.HidError('unexpected init reply len')
    if r[0:8] != nonce:
      raise errors.HidError('nonce mismatch')
    self.cid = bytearray(r[8:12])

    self.u2fhid_version = r[12]

  def InternalExchange(self, cmd, payload_in):
    """Sends and receives a message from the device."""
    # make a copy because we destroy it below
    self.logger.debug('payload: ' + str(list(payload_in)))
    payload = bytearray()
    payload[:] = payload_in
    for _ in range(2):
      self.InternalSend(cmd, payload)
      ret_cmd, ret_payload = self.InternalRecv()

      if ret_cmd == UsbHidTransport.U2FHID_ERROR:
        if ret_payload == UsbHidTransport.ERR_CHANNEL_BUSY:
          time.sleep(0.5)
          continue
        raise errors.HidError('Device error: %d' % int(ret_payload[0]))
      elif ret_cmd != cmd:
        raise errors.HidError('Command mismatch!')

      return ret_payload
    raise errors.HidError('Device Busy.  Please retry')

  def InternalSend(self, cmd, payload):
    """Sends a message to the device, including fragmenting it."""
    length_to_send = len(payload)

    max_payload = self.packet_size - 7
    first_frame = payload[0:max_payload]
    first_packet = UsbHidTransport.InitPacket(self.packet_size, self.cid, cmd,
                                              len(payload), first_frame)
    del payload[0:max_payload]
    length_to_send -= len(first_frame)
    self.InternalSendPacket(first_packet)

    seq = 0
    while length_to_send > 0:
      max_payload = self.packet_size - 5
      next_frame = payload[0:max_payload]
      del payload[0:max_payload]
      length_to_send -= len(next_frame)
      next_packet = UsbHidTransport.ContPacket(self.packet_size, self.cid, seq,
                                               next_frame)
      self.InternalSendPacket(next_packet)
      seq += 1

  def InternalSendPacket(self, packet):
    wire = packet.ToWireFormat()
    self.logger.debug('sending packet: ' + str(wire))
    self.hid_device.Write(wire)

  def InternalReadFrame(self):
        # TODO(user): Figure out timeouts.  Today, this implementation
        # blocks forever at the HID level waiting for a response to a report.
        # This may not be reasonable behavior (though in practice in seems to be
        # OK on the set of devices and machines tested so far).
    frame = self.hid_device.Read()
    self.logger.debug('recv: ' + str(frame))
    return frame

  def InternalRecv(self):
    """Receives a message from the device, including defragmenting it."""
    first_read = self.InternalReadFrame()
    first_packet = UsbHidTransport.InitPacket.FromWireFormat(self.packet_size,
                                                             first_read)

    data = first_packet.payload
    to_read = first_packet.size - len(first_packet.payload)

    seq = 0
    while to_read > 0:
      next_read = self.InternalReadFrame()
      next_packet = UsbHidTransport.ContPacket.FromWireFormat(self.packet_size,
                                                              next_read)
      if self.cid != next_packet.cid:
        # Skip over packets that are for communication with other clients.
        # HID is broadcast, so we see potentially all communication from the
        # device.  For well-behaved devices, these should be BUSY messages
        # sent to other clients of the device because at this point we're
        # in mid-message transit.
        continue

      if seq != next_packet.seq:
        raise errors.HardwareError('Packets received out of order')

      # This packet for us at this point, so debit it against our
      # balance of bytes to read.
      to_read -= len(next_packet.payload)

      data.extend(next_packet.payload)
      seq += 1

    # truncate incomplete frames
    data = data[0:first_packet.size]
    return (first_packet.cmd, data)
