# pack.py -- For dealing with packed git objects.
# Copyright (C) 2007 James Westby <jw+debian@jameswestby.net>
# Copyright (C) 2008-2013 Jelmer Vernooij <jelmer@jelmer.uk>
#
# Dulwich is dual-licensed under the Apache License, Version 2.0 and the GNU
# General Public License as public by the Free Software Foundation; version 2.0
# or (at your option) any later version. You can redistribute it and/or
# modify it under the terms of either of these two licenses.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You should have received a copy of the licenses; if not, see
# <http://www.gnu.org/licenses/> for a copy of the GNU General Public License
# and <http://www.apache.org/licenses/LICENSE-2.0> for a copy of the Apache
# License, Version 2.0.
#

"""Classes for dealing with packed git objects.

A pack is a compact representation of a bunch of objects, stored
using deltas where possible.

They have two parts, the pack file, which stores the data, and an index
that tells you where the data is.

To find an object you look in all of the index files 'til you find a
match for the object name. You then use the pointer got from this as
a pointer in to the corresponding packfile.
"""

from collections import defaultdict

import binascii
from io import BytesIO, UnsupportedOperation
from collections import (
    deque,
)
import difflib
import struct

from itertools import chain

import os
import sys

from hashlib import sha1
from os import (
    SEEK_CUR,
    SEEK_END,
)
from struct import unpack_from
import zlib

try:
    import mmap
except ImportError:
    has_mmap = False
else:
    has_mmap = True

# For some reason the above try, except fails to set has_mmap = False for plan9
if sys.platform == "Plan9":
    has_mmap = False

from dulwich.errors import (  # noqa: E402
    ApplyDeltaError,
    ChecksumMismatch,
)
from dulwich.file import GitFile  # noqa: E402
from dulwich.lru_cache import (  # noqa: E402
    LRUSizeCache,
)
from dulwich.objects import (  # noqa: E402
    ShaFile,
    hex_to_sha,
    sha_to_hex,
    object_header,
)


OFS_DELTA = 6
REF_DELTA = 7

DELTA_TYPES = (OFS_DELTA, REF_DELTA)


DEFAULT_PACK_DELTA_WINDOW_SIZE = 10


def take_msb_bytes(read, crc32=None):
    """Read bytes marked with most significant bit.

    Args:
      read: Read function
    """
    ret = []
    while len(ret) == 0 or ret[-1] & 0x80:
        b = read(1)
        if crc32 is not None:
            crc32 = binascii.crc32(b, crc32)
        ret.append(ord(b[:1]))
    return ret, crc32


class PackFileDisappeared(Exception):
    def __init__(self, obj):
        self.obj = obj


class UnpackedObject(object):
    """Class encapsulating an object unpacked from a pack file.

    These objects should only be created from within unpack_object. Most
    members start out as empty and are filled in at various points by
    read_zlib_chunks, unpack_object, DeltaChainIterator, etc.

    End users of this object should take care that the function they're getting
    this object from is guaranteed to set the members they need.
    """

    __slots__ = [
        "offset",  # Offset in its pack.
        "_sha",  # Cached binary SHA.
        "obj_type_num",  # Type of this object.
        "obj_chunks",  # Decompressed and delta-resolved chunks.
        "pack_type_num",  # Type of this object in the pack (may be a delta).
        "delta_base",  # Delta base offset or SHA.
        "comp_chunks",  # Compressed object chunks.
        "decomp_chunks",  # Decompressed object chunks.
        "decomp_len",  # Decompressed length of this object.
        "crc32",  # CRC32.
    ]

    # TODO(user): read_zlib_chunks and unpack_object could very well be
    # methods of this object.
    def __init__(self, pack_type_num, delta_base, decomp_len, crc32):
        self.offset = None
        self._sha = None
        self.pack_type_num = pack_type_num
        self.delta_base = delta_base
        self.comp_chunks = None
        self.decomp_chunks = []
        self.decomp_len = decomp_len
        self.crc32 = crc32

        if pack_type_num in DELTA_TYPES:
            self.obj_type_num = None
            self.obj_chunks = None
        else:
            self.obj_type_num = pack_type_num
            self.obj_chunks = self.decomp_chunks
            self.delta_base = delta_base

    def sha(self):
        """Return the binary SHA of this object."""
        if self._sha is None:
            self._sha = obj_sha(self.obj_type_num, self.obj_chunks)
        return self._sha

    def sha_file(self):
        """Return a ShaFile from this object."""
        return ShaFile.from_raw_chunks(self.obj_type_num, self.obj_chunks)

    # Only provided for backwards compatibility with code that expects either
    # chunks or a delta tuple.
    def _obj(self):
        """Return the decompressed chunks, or (delta base, delta chunks)."""
        if self.pack_type_num in DELTA_TYPES:
            return (self.delta_base, self.decomp_chunks)
        else:
            return self.decomp_chunks

    def __eq__(self, other):
        if not isinstance(other, UnpackedObject):
            return False
        for slot in self.__slots__:
            if getattr(self, slot) != getattr(other, slot):
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        data = ["%s=%r" % (s, getattr(self, s)) for s in self.__slots__]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(data))


_ZLIB_BUFSIZE = 4096


def read_zlib_chunks(
    read_some, unpacked, include_comp=False, buffer_size=_ZLIB_BUFSIZE
):
    """Read zlib data from a buffer.

    This function requires that the buffer have additional data following the
    compressed data, which is guaranteed to be the case for git pack files.

    Args:
      read_some: Read function that returns at least one byte, but may
        return less than the requested size.
      unpacked: An UnpackedObject to write result data to. If its crc32
        attr is not None, the CRC32 of the compressed bytes will be computed
        using this starting CRC32.
        After this function, will have the following attrs set:
        * comp_chunks    (if include_comp is True)
        * decomp_chunks
        * decomp_len
        * crc32
      include_comp: If True, include compressed data in the result.
      buffer_size: Size of the read buffer.
    Returns: Leftover unused data from the decompression.
    Raises:
      zlib.error: if a decompression error occurred.
    """
    if unpacked.decomp_len <= -1:
        raise ValueError("non-negative zlib data stream size expected")
    decomp_obj = zlib.decompressobj()

    comp_chunks = []
    decomp_chunks = unpacked.decomp_chunks
    decomp_len = 0
    crc32 = unpacked.crc32

    while True:
        add = read_some(buffer_size)
        if not add:
            raise zlib.error("EOF before end of zlib stream")
        comp_chunks.append(add)
        decomp = decomp_obj.decompress(add)
        decomp_len += len(decomp)
        decomp_chunks.append(decomp)
        unused = decomp_obj.unused_data
        if unused:
            left = len(unused)
            if crc32 is not None:
                crc32 = binascii.crc32(add[:-left], crc32)
            if include_comp:
                comp_chunks[-1] = add[:-left]
            break
        elif crc32 is not None:
            crc32 = binascii.crc32(add, crc32)
    if crc32 is not None:
        crc32 &= 0xFFFFFFFF

    if decomp_len != unpacked.decomp_len:
        raise zlib.error("decompressed data does not match expected size")

    unpacked.crc32 = crc32
    if include_comp:
        unpacked.comp_chunks = comp_chunks
    return unused


def iter_sha1(iter):
    """Return the hexdigest of the SHA1 over a set of names.

    Args:
      iter: Iterator over string objects
    Returns: 40-byte hex sha1 digest
    """
    sha = sha1()
    for name in iter:
        sha.update(name)
    return sha.hexdigest().encode("ascii")


def load_pack_index(path):
    """Load an index file by path.

    Args:
      filename: Path to the index file
    Returns: A PackIndex loaded from the given path
    """
    with GitFile(path, "rb") as f:
        return load_pack_index_file(path, f)


def _load_file_contents(f, size=None):
    try:
        fd = f.fileno()
    except (UnsupportedOperation, AttributeError):
        fd = None
    # Attempt to use mmap if possible
    if fd is not None:
        if size is None:
            size = os.fstat(fd).st_size
        if has_mmap:
            try:
                contents = mmap.mmap(fd, size, access=mmap.ACCESS_READ)
            except mmap.error:
                # Perhaps a socket?
                pass
            else:
                return contents, size
    contents = f.read()
    size = len(contents)
    return contents, size


def load_pack_index_file(path, f):
    """Load an index file from a file-like object.

    Args:
      path: Path for the index file
      f: File-like object
    Returns: A PackIndex loaded from the given file
    """
    contents, size = _load_file_contents(f)
    if contents[:4] == b"\377tOc":
        version = struct.unpack(b">L", contents[4:8])[0]
        if version == 2:
            return PackIndex2(path, file=f, contents=contents, size=size)
        else:
            raise KeyError("Unknown pack index format %d" % version)
    else:
        return PackIndex1(path, file=f, contents=contents, size=size)


def bisect_find_sha(start, end, sha, unpack_name):
    """Find a SHA in a data blob with sorted SHAs.

    Args:
      start: Start index of range to search
      end: End index of range to search
      sha: Sha to find
      unpack_name: Callback to retrieve SHA by index
    Returns: Index of the SHA, or None if it wasn't found
    """
    assert start <= end
    while start <= end:
        i = (start + end) // 2
        file_sha = unpack_name(i)
        if file_sha < sha:
            start = i + 1
        elif file_sha > sha:
            end = i - 1
        else:
            return i
    return None


class PackIndex(object):
    """An index in to a packfile.

    Given a sha id of an object a pack index can tell you the location in the
    packfile of that object if it has it.
    """

    def __eq__(self, other):
        if not isinstance(other, PackIndex):
            return False

        for (name1, _, _), (name2, _, _) in zip(
            self.iterentries(), other.iterentries()
        ):
            if name1 != name2:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        """Return the number of entries in this pack index."""
        raise NotImplementedError(self.__len__)

    def __iter__(self):
        """Iterate over the SHAs in this pack."""
        return map(sha_to_hex, self._itersha())

    def iterentries(self):
        """Iterate over the entries in this pack index.

        Returns: iterator over tuples with object name, offset in packfile and
            crc32 checksum.
        """
        raise NotImplementedError(self.iterentries)

    def get_pack_checksum(self):
        """Return the SHA1 checksum stored for the corresponding packfile.

        Returns: 20-byte binary digest
        """
        raise NotImplementedError(self.get_pack_checksum)

    def object_index(self, sha):
        """Return the index in to the corresponding packfile for the object.

        Given the name of an object it will return the offset that object
        lives at within the corresponding pack file. If the pack file doesn't
        have the object then None will be returned.
        """
        if len(sha) == 40:
            sha = hex_to_sha(sha)
        try:
            return self._object_index(sha)
        except ValueError:
            closed = getattr(self._contents, "closed", None)
            if closed in (None, True):
                raise PackFileDisappeared(self)
            raise

    def object_sha1(self, index):
        """Return the SHA1 corresponding to the index in the pack file."""
        # PERFORMANCE/TODO(user): Avoid scanning entire index
        for (name, offset, crc32) in self.iterentries():
            if offset == index:
                return name
        else:
            raise KeyError(index)

    def _object_index(self, sha):
        """See object_index.

        Args:
          sha: A *binary* SHA string. (20 characters long)_
        """
        raise NotImplementedError(self._object_index)

    def objects_sha1(self):
        """Return the hex SHA1 over all the shas of all objects in this pack.

        Note: This is used for the filename of the pack.
        """
        return iter_sha1(self._itersha())

    def _itersha(self):
        """Yield all the SHA1's of the objects in the index, sorted."""
        raise NotImplementedError(self._itersha)


class MemoryPackIndex(PackIndex):
    """Pack index that is stored entirely in memory."""

    def __init__(self, entries, pack_checksum=None):
        """Create a new MemoryPackIndex.

        Args:
          entries: Sequence of name, idx, crc32 (sorted)
          pack_checksum: Optional pack checksum
        """
        self._by_sha = {}
        self._by_index = {}
        for name, idx, crc32 in entries:
            self._by_sha[name] = idx
            self._by_index[idx] = name
        self._entries = entries
        self._pack_checksum = pack_checksum

    def get_pack_checksum(self):
        return self._pack_checksum

    def __len__(self):
        return len(self._entries)

    def _object_index(self, sha):
        return self._by_sha[sha][0]

    def object_sha1(self, index):
        return self._by_index[index]

    def _itersha(self):
        return iter(self._by_sha)

    def iterentries(self):
        return iter(self._entries)


class FilePackIndex(PackIndex):
    """Pack index that is based on a file.

    To do the loop it opens the file, and indexes first 256 4 byte groups
    with the first byte of the sha id. The value in the four byte group indexed
    is the end of the group that shares the same starting byte. Subtract one
    from the starting byte and index again to find the start of the group.
    The values are sorted by sha id within the group, so do the math to find
    the start and end offset and then bisect in to find if the value is
    present.
    """

    def __init__(self, filename, file=None, contents=None, size=None):
        """Create a pack index object.

        Provide it with the name of the index file to consider, and it will map
        it whenever required.
        """
        self._filename = filename
        # Take the size now, so it can be checked each time we map the file to
        # ensure that it hasn't changed.
        if file is None:
            self._file = GitFile(filename, "rb")
        else:
            self._file = file
        if contents is None:
            self._contents, self._size = _load_file_contents(self._file, size)
        else:
            self._contents, self._size = (contents, size)

    @property
    def path(self):
        return self._filename

    def __eq__(self, other):
        # Quick optimization:
        if (
            isinstance(other, FilePackIndex)
            and self._fan_out_table != other._fan_out_table
        ):
            return False

        return super(FilePackIndex, self).__eq__(other)

    def close(self):
        self._file.close()
        if getattr(self._contents, "close", None) is not None:
            self._contents.close()

    def __len__(self):
        """Return the number of entries in this pack index."""
        return self._fan_out_table[-1]

    def _unpack_entry(self, i):
        """Unpack the i-th entry in the index file.

        Returns: Tuple with object name (SHA), offset in pack file and CRC32
            checksum (if known).
        """
        raise NotImplementedError(self._unpack_entry)

    def _unpack_name(self, i):
        """Unpack the i-th name from the index file."""
        raise NotImplementedError(self._unpack_name)

    def _unpack_offset(self, i):
        """Unpack the i-th object offset from the index file."""
        raise NotImplementedError(self._unpack_offset)

    def _unpack_crc32_checksum(self, i):
        """Unpack the crc32 checksum for the ith object from the index file."""
        raise NotImplementedError(self._unpack_crc32_checksum)

    def _itersha(self):
        for i in range(len(self)):
            yield self._unpack_name(i)

    def iterentries(self):
        """Iterate over the entries in this pack index.

        Returns: iterator over tuples with object name, offset in packfile and
            crc32 checksum.
        """
        for i in range(len(self)):
            yield self._unpack_entry(i)

    def _read_fan_out_table(self, start_offset):
        ret = []
        for i in range(0x100):
            fanout_entry = self._contents[
                start_offset + i * 4 : start_offset + (i + 1) * 4
            ]
            ret.append(struct.unpack(">L", fanout_entry)[0])
        return ret

    def check(self):
        """Check that the stored checksum matches the actual checksum."""
        actual = self.calculate_checksum()
        stored = self.get_stored_checksum()
        if actual != stored:
            raise ChecksumMismatch(stored, actual)

    def calculate_checksum(self):
        """Calculate the SHA1 checksum over this pack index.

        Returns: This is a 20-byte binary digest
        """
        return sha1(self._contents[:-20]).digest()

    def get_pack_checksum(self):
        """Return the SHA1 checksum stored for the corresponding packfile.

        Returns: 20-byte binary digest
        """
        return bytes(self._contents[-40:-20])

    def get_stored_checksum(self):
        """Return the SHA1 checksum stored for this index.

        Returns: 20-byte binary digest
        """
        return bytes(self._contents[-20:])

    def _object_index(self, sha):
        """See object_index.

        Args:
          sha: A *binary* SHA string. (20 characters long)_
        """
        assert len(sha) == 20
        idx = ord(sha[:1])
        if idx == 0:
            start = 0
        else:
            start = self._fan_out_table[idx - 1]
        end = self._fan_out_table[idx]
        i = bisect_find_sha(start, end, sha, self._unpack_name)
        if i is None:
            raise KeyError(sha)
        return self._unpack_offset(i)


class PackIndex1(FilePackIndex):
    """Version 1 Pack Index file."""

    def __init__(self, filename, file=None, contents=None, size=None):
        super(PackIndex1, self).__init__(filename, file, contents, size)
        self.version = 1
        self._fan_out_table = self._read_fan_out_table(0)

    def _unpack_entry(self, i):
        (offset, name) = unpack_from(">L20s", self._contents, (0x100 * 4) + (i * 24))
        return (name, offset, None)

    def _unpack_name(self, i):
        offset = (0x100 * 4) + (i * 24) + 4
        return self._contents[offset : offset + 20]

    def _unpack_offset(self, i):
        offset = (0x100 * 4) + (i * 24)
        return unpack_from(">L", self._contents, offset)[0]

    def _unpack_crc32_checksum(self, i):
        # Not stored in v1 index files
        return None


class PackIndex2(FilePackIndex):
    """Version 2 Pack Index file."""

    def __init__(self, filename, file=None, contents=None, size=None):
        super(PackIndex2, self).__init__(filename, file, contents, size)
        if self._contents[:4] != b"\377tOc":
            raise AssertionError("Not a v2 pack index file")
        (self.version,) = unpack_from(b">L", self._contents, 4)
        if self.version != 2:
            raise AssertionError("Version was %d" % self.version)
        self._fan_out_table = self._read_fan_out_table(8)
        self._name_table_offset = 8 + 0x100 * 4
        self._crc32_table_offset = self._name_table_offset + 20 * len(self)
        self._pack_offset_table_offset = self._crc32_table_offset + 4 * len(self)
        self._pack_offset_largetable_offset = self._pack_offset_table_offset + 4 * len(
            self
        )

    def _unpack_entry(self, i):
        return (
            self._unpack_name(i),
            self._unpack_offset(i),
            self._unpack_crc32_checksum(i),
        )

    def _unpack_name(self, i):
        offset = self._name_table_offset + i * 20
        return self._contents[offset : offset + 20]

    def _unpack_offset(self, i):
        offset = self._pack_offset_table_offset + i * 4
        offset = unpack_from(">L", self._contents, offset)[0]
        if offset & (2 ** 31):
            offset = self._pack_offset_largetable_offset + (offset & (2 ** 31 - 1)) * 8
            offset = unpack_from(">Q", self._contents, offset)[0]
        return offset

    def _unpack_crc32_checksum(self, i):
        return unpack_from(">L", self._contents, self._crc32_table_offset + i * 4)[0]


def read_pack_header(read):
    """Read the header of a pack file.

    Args:
      read: Read function
    Returns: Tuple of (pack version, number of objects). If no data is
        available to read, returns (None, None).
    """
    header = read(12)
    if not header:
        return None, None
    if header[:4] != b"PACK":
        raise AssertionError("Invalid pack header %r" % header)
    (version,) = unpack_from(b">L", header, 4)
    if version not in (2, 3):
        raise AssertionError("Version was %d" % version)
    (num_objects,) = unpack_from(b">L", header, 8)
    return (version, num_objects)


def chunks_length(chunks):
    if isinstance(chunks, bytes):
        return len(chunks)
    else:
        return sum(map(len, chunks))


def unpack_object(
    read_all,
    read_some=None,
    compute_crc32=False,
    include_comp=False,
    zlib_bufsize=_ZLIB_BUFSIZE,
):
    """Unpack a Git object.

    Args:
      read_all: Read function that blocks until the number of requested
        bytes are read.
      read_some: Read function that returns at least one byte, but may not
        return the number of bytes requested.
      compute_crc32: If True, compute the CRC32 of the compressed data. If
        False, the returned CRC32 will be None.
      include_comp: If True, include compressed data in the result.
      zlib_bufsize: An optional buffer size for zlib operations.
    Returns: A tuple of (unpacked, unused), where unused is the unused data
        leftover from decompression, and unpacked in an UnpackedObject with
        the following attrs set:

        * obj_chunks     (for non-delta types)
        * pack_type_num
        * delta_base     (for delta types)
        * comp_chunks    (if include_comp is True)
        * decomp_chunks
        * decomp_len
        * crc32          (if compute_crc32 is True)
    """
    if read_some is None:
        read_some = read_all
    if compute_crc32:
        crc32 = 0
    else:
        crc32 = None

    bytes, crc32 = take_msb_bytes(read_all, crc32=crc32)
    type_num = (bytes[0] >> 4) & 0x07
    size = bytes[0] & 0x0F
    for i, byte in enumerate(bytes[1:]):
        size += (byte & 0x7F) << ((i * 7) + 4)

    raw_base = len(bytes)
    if type_num == OFS_DELTA:
        bytes, crc32 = take_msb_bytes(read_all, crc32=crc32)
        raw_base += len(bytes)
        if bytes[-1] & 0x80:
            raise AssertionError
        delta_base_offset = bytes[0] & 0x7F
        for byte in bytes[1:]:
            delta_base_offset += 1
            delta_base_offset <<= 7
            delta_base_offset += byte & 0x7F
        delta_base = delta_base_offset
    elif type_num == REF_DELTA:
        delta_base = read_all(20)
        if compute_crc32:
            crc32 = binascii.crc32(delta_base, crc32)
        raw_base += 20
    else:
        delta_base = None

    unpacked = UnpackedObject(type_num, delta_base, size, crc32)
    unused = read_zlib_chunks(
        read_some,
        unpacked,
        buffer_size=zlib_bufsize,
        include_comp=include_comp,
    )
    return unpacked, unused


def _compute_object_size(value):
    """Compute the size of a unresolved object for use with LRUSizeCache."""
    (num, obj) = value
    if num in DELTA_TYPES:
        return chunks_length(obj[1])
    return chunks_length(obj)


class PackStreamReader(object):
    """Class to read a pack stream.

    The pack is read from a ReceivableProtocol using read() or recv() as
    appropriate.
    """

    def __init__(self, read_all, read_some=None, zlib_bufsize=_ZLIB_BUFSIZE):
        self.read_all = read_all
        if read_some is None:
            self.read_some = read_all
        else:
            self.read_some = read_some
        self.sha = sha1()
        self._offset = 0
        self._rbuf = BytesIO()
        # trailer is a deque to avoid memory allocation on small reads
        self._trailer = deque()
        self._zlib_bufsize = zlib_bufsize

    def _read(self, read, size):
        """Read up to size bytes using the given callback.

        As a side effect, update the verifier's hash (excluding the last 20
        bytes read).

        Args:
          read: The read callback to read from.
          size: The maximum number of bytes to read; the particular
            behavior is callback-specific.
        """
        data = read(size)

        # maintain a trailer of the last 20 bytes we've read
        n = len(data)
        self._offset += n
        tn = len(self._trailer)
        if n >= 20:
            to_pop = tn
            to_add = 20
        else:
            to_pop = max(n + tn - 20, 0)
            to_add = n
        self.sha.update(
            bytes(bytearray([self._trailer.popleft() for _ in range(to_pop)]))
        )
        self._trailer.extend(data[-to_add:])

        # hash everything but the trailer
        self.sha.update(data[:-to_add])
        return data

    def _buf_len(self):
        buf = self._rbuf
        start = buf.tell()
        buf.seek(0, SEEK_END)
        end = buf.tell()
        buf.seek(start)
        return end - start

    @property
    def offset(self):
        return self._offset - self._buf_len()

    def read(self, size):
        """Read, blocking until size bytes are read."""
        buf_len = self._buf_len()
        if buf_len >= size:
            return self._rbuf.read(size)
        buf_data = self._rbuf.read()
        self._rbuf = BytesIO()
        return buf_data + self._read(self.read_all, size - buf_len)

    def recv(self, size):
        """Read up to size bytes, blocking until one byte is read."""
        buf_len = self._buf_len()
        if buf_len:
            data = self._rbuf.read(size)
            if size >= buf_len:
                self._rbuf = BytesIO()
            return data
        return self._read(self.read_some, size)

    def __len__(self):
        return self._num_objects

    def read_objects(self, compute_crc32=False):
        """Read the objects in this pack file.

        Args:
          compute_crc32: If True, compute the CRC32 of the compressed
            data. If False, the returned CRC32 will be None.
        Returns: Iterator over UnpackedObjects with the following members set:
            offset
            obj_type_num
            obj_chunks (for non-delta types)
            delta_base (for delta types)
            decomp_chunks
            decomp_len
            crc32 (if compute_crc32 is True)
        Raises:
          ChecksumMismatch: if the checksum of the pack contents does not
            match the checksum in the pack trailer.
          zlib.error: if an error occurred during zlib decompression.
          IOError: if an error occurred writing to the output file.
        """
        pack_version, self._num_objects = read_pack_header(self.read)
        if pack_version is None:
            return

        for i in range(self._num_objects):
            offset = self.offset
            unpacked, unused = unpack_object(
                self.read,
                read_some=self.recv,
                compute_crc32=compute_crc32,
                zlib_bufsize=self._zlib_bufsize,
            )
            unpacked.offset = offset

            # prepend any unused data to current read buffer
            buf = BytesIO()
            buf.write(unused)
            buf.write(self._rbuf.read())
            buf.seek(0)
            self._rbuf = buf

            yield unpacked

        if self._buf_len() < 20:
            # If the read buffer is full, then the last read() got the whole
            # trailer off the wire. If not, it means there is still some of the
            # trailer to read. We need to read() all 20 bytes; N come from the
            # read buffer and (20 - N) come from the wire.
            self.read(20)

        pack_sha = bytearray(self._trailer)
        if pack_sha != self.sha.digest():
            raise ChecksumMismatch(sha_to_hex(pack_sha), self.sha.hexdigest())


class PackStreamCopier(PackStreamReader):
    """Class to verify a pack stream as it is being read.

    The pack is read from a ReceivableProtocol using read() or recv() as
    appropriate and written out to the given file-like object.
    """

    def __init__(self, read_all, read_some, outfile, delta_iter=None):
        """Initialize the copier.

        Args:
          read_all: Read function that blocks until the number of
            requested bytes are read.
          read_some: Read function that returns at least one byte, but may
            not return the number of bytes requested.
          outfile: File-like object to write output through.
          delta_iter: Optional DeltaChainIterator to record deltas as we
            read them.
        """
        super(PackStreamCopier, self).__init__(read_all, read_some=read_some)
        self.outfile = outfile
        self._delta_iter = delta_iter

    def _read(self, read, size):
        """Read data from the read callback and write it to the file."""
        data = super(PackStreamCopier, self)._read(read, size)
        self.outfile.write(data)
        return data

    def verify(self):
        """Verify a pack stream and write it to the output file.

        See PackStreamReader.iterobjects for a list of exceptions this may
        throw.
        """
        if self._delta_iter:
            for unpacked in self.read_objects():
                self._delta_iter.record(unpacked)
        else:
            for _ in self.read_objects():
                pass


def obj_sha(type, chunks):
    """Compute the SHA for a numeric type and object chunks."""
    sha = sha1()
    sha.update(object_header(type, chunks_length(chunks)))
    if isinstance(chunks, bytes):
        sha.update(chunks)
    else:
        for chunk in chunks:
            sha.update(chunk)
    return sha.digest()


def compute_file_sha(f, start_ofs=0, end_ofs=0, buffer_size=1 << 16):
    """Hash a portion of a file into a new SHA.

    Args:
      f: A file-like object to read from that supports seek().
      start_ofs: The offset in the file to start reading at.
      end_ofs: The offset in the file to end reading at, relative to the
        end of the file.
      buffer_size: A buffer size for reading.
    Returns: A new SHA object updated with data read from the file.
    """
    sha = sha1()
    f.seek(0, SEEK_END)
    length = f.tell()
    if (end_ofs < 0 and length + end_ofs < start_ofs) or end_ofs > length:
        raise AssertionError(
            "Attempt to read beyond file length. "
            "start_ofs: %d, end_ofs: %d, file length: %d" % (start_ofs, end_ofs, length)
        )
    todo = length + end_ofs - start_ofs
    f.seek(start_ofs)
    while todo:
        data = f.read(min(todo, buffer_size))
        sha.update(data)
        todo -= len(data)
    return sha


class PackData(object):
    """The data contained in a packfile.

    Pack files can be accessed both sequentially for exploding a pack, and
    directly with the help of an index to retrieve a specific object.

    The objects within are either complete or a delta against another.

    The header is variable length. If the MSB of each byte is set then it
    indicates that the subsequent byte is still part of the header.
    For the first byte the next MS bits are the type, which tells you the type
    of object, and whether it is a delta. The LS byte is the lowest bits of the
    size. For each subsequent byte the LS 7 bits are the next MS bits of the
    size, i.e. the last byte of the header contains the MS bits of the size.

    For the complete objects the data is stored as zlib deflated data.
    The size in the header is the uncompressed object size, so to uncompress
    you need to just keep feeding data to zlib until you get an object back,
    or it errors on bad data. This is done here by just giving the complete
    buffer from the start of the deflated object on. This is bad, but until I
    get mmap sorted out it will have to do.

    Currently there are no integrity checks done. Also no attempt is made to
    try and detect the delta case, or a request for an object at the wrong
    position.  It will all just throw a zlib or KeyError.
    """

    def __init__(self, filename, file=None, size=None):
        """Create a PackData object representing the pack in the given filename.

        The file must exist and stay readable until the object is disposed of.
        It must also stay the same size. It will be mapped whenever needed.

        Currently there is a restriction on the size of the pack as the python
        mmap implementation is flawed.
        """
        self._filename = filename
        self._size = size
        self._header_size = 12
        if file is None:
            self._file = GitFile(self._filename, "rb")
        else:
            self._file = file
        (version, self._num_objects) = read_pack_header(self._file.read)
        self._offset_cache = LRUSizeCache(
            1024 * 1024 * 20, compute_size=_compute_object_size
        )
        self.pack = None

    @property
    def filename(self):
        return os.path.basename(self._filename)

    @property
    def path(self):
        return self._filename

    @classmethod
    def from_file(cls, file, size=None):
        return cls(str(file), file=file, size=size)

    @classmethod
    def from_path(cls, path):
        return cls(filename=path)

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __eq__(self, other):
        if isinstance(other, PackData):
            return self.get_stored_checksum() == other.get_stored_checksum()
        if isinstance(other, list):
            if len(self) != len(other):
                return False
            for o1, o2 in zip(self.iterobjects(), other):
                if o1 != o2:
                    return False
            return True
        return False

    def _get_size(self):
        if self._size is not None:
            return self._size
        self._size = os.path.getsize(self._filename)
        if self._size < self._header_size:
            errmsg = "%s is too small for a packfile (%d < %d)" % (
                self._filename,
                self._size,
                self._header_size,
            )
            raise AssertionError(errmsg)
        return self._size

    def __len__(self):
        """Returns the number of objects in this pack."""
        return self._num_objects

    def calculate_checksum(self):
        """Calculate the checksum for this pack.

        Returns: 20-byte binary SHA1 digest
        """
        return compute_file_sha(self._file, end_ofs=-20).digest()

    def get_ref(self, sha):
        """Get the object for a ref SHA, only looking in this pack."""
        # TODO: cache these results
        if self.pack is None:
            raise KeyError(sha)
        try:
            offset = self.pack.index.object_index(sha)
        except KeyError:
            offset = None
        if offset:
            type, obj = self.get_object_at(offset)
        elif self.pack is not None and self.pack.resolve_ext_ref:
            type, obj = self.pack.resolve_ext_ref(sha)
        else:
            raise KeyError(sha)
        return offset, type, obj

    def resolve_object(self, offset, type, obj, get_ref=None):
        """Resolve an object, possibly resolving deltas when necessary.

        Returns: Tuple with object type and contents.
        """
        # Walk down the delta chain, building a stack of deltas to reach
        # the requested object.
        base_offset = offset
        base_type = type
        base_obj = obj
        delta_stack = []
        while base_type in DELTA_TYPES:
            prev_offset = base_offset
            if get_ref is None:
                get_ref = self.get_ref
            if base_type == OFS_DELTA:
                (delta_offset, delta) = base_obj
                # TODO: clean up asserts and replace with nicer error messages
                base_offset = base_offset - delta_offset
                base_type, base_obj = self.get_object_at(base_offset)
                assert isinstance(base_type, int)
            elif base_type == REF_DELTA:
                (basename, delta) = base_obj
                assert isinstance(basename, bytes) and len(basename) == 20
                base_offset, base_type, base_obj = get_ref(basename)
                assert isinstance(base_type, int)
            delta_stack.append((prev_offset, base_type, delta))

        # Now grab the base object (mustn't be a delta) and apply the
        # deltas all the way up the stack.
        chunks = base_obj
        for prev_offset, delta_type, delta in reversed(delta_stack):
            chunks = apply_delta(chunks, delta)
            # TODO(user): This can result in poor performance if
            # large base objects are separated from deltas in the pack.
            # We should reorganize so that we apply deltas to all
            # objects in a chain one after the other to optimize cache
            # performance.
            if prev_offset is not None:
                self._offset_cache[prev_offset] = base_type, chunks
        return base_type, chunks

    def iterobjects(self, progress=None, compute_crc32=True):
        self._file.seek(self._header_size)
        for i in range(1, self._num_objects + 1):
            offset = self._file.tell()
            unpacked, unused = unpack_object(
                self._file.read, compute_crc32=compute_crc32
            )
            if progress is not None:
                progress(i, self._num_objects)
            yield (
                offset,
                unpacked.pack_type_num,
                unpacked._obj(),
                unpacked.crc32,
            )
            # Back up over unused data.
            self._file.seek(-len(unused), SEEK_CUR)

    def _iter_unpacked(self):
        # TODO(user): Merge this with iterobjects, if we can change its
        # return type.
        self._file.seek(self._header_size)

        if self._num_objects is None:
            return

        for _ in range(self._num_objects):
            offset = self._file.tell()
            unpacked, unused = unpack_object(self._file.read, compute_crc32=False)
            unpacked.offset = offset
            yield unpacked
            # Back up over unused data.
            self._file.seek(-len(unused), SEEK_CUR)

    def iterentries(self, progress=None):
        """Yield entries summarizing the contents of this pack.

        Args:
          progress: Progress function, called with current and total
            object count.
        Returns: iterator of tuples with (sha, offset, crc32)
        """
        num_objects = self._num_objects
        resolve_ext_ref = self.pack.resolve_ext_ref if self.pack is not None else None
        indexer = PackIndexer.for_pack_data(self, resolve_ext_ref=resolve_ext_ref)
        for i, result in enumerate(indexer):
            if progress is not None:
                progress(i, num_objects)
            yield result

    def sorted_entries(self, progress=None):
        """Return entries in this pack, sorted by SHA.

        Args:
          progress: Progress function, called with current and total
            object count
        Returns: List of tuples with (sha, offset, crc32)
        """
        ret = sorted(self.iterentries(progress=progress))
        return ret

    def create_index_v1(self, filename, progress=None):
        """Create a version 1 file for this data file.

        Args:
          filename: Index filename.
          progress: Progress report function
        Returns: Checksum of index file
        """
        entries = self.sorted_entries(progress=progress)
        with GitFile(filename, "wb") as f:
            return write_pack_index_v1(f, entries, self.calculate_checksum())

    def create_index_v2(self, filename, progress=None):
        """Create a version 2 index file for this data file.

        Args:
          filename: Index filename.
          progress: Progress report function
        Returns: Checksum of index file
        """
        entries = self.sorted_entries(progress=progress)
        with GitFile(filename, "wb") as f:
            return write_pack_index_v2(f, entries, self.calculate_checksum())

    def create_index(self, filename, progress=None, version=2):
        """Create an  index file for this data file.

        Args:
          filename: Index filename.
          progress: Progress report function
        Returns: Checksum of index file
        """
        if version == 1:
            return self.create_index_v1(filename, progress)
        elif version == 2:
            return self.create_index_v2(filename, progress)
        else:
            raise ValueError("unknown index format %d" % version)

    def get_stored_checksum(self):
        """Return the expected checksum stored in this pack."""
        self._file.seek(-20, SEEK_END)
        return self._file.read(20)

    def check(self):
        """Check the consistency of this pack."""
        actual = self.calculate_checksum()
        stored = self.get_stored_checksum()
        if actual != stored:
            raise ChecksumMismatch(stored, actual)

    def get_compressed_data_at(self, offset):
        """Given offset in the packfile return compressed data that is there.

        Using the associated index the location of an object can be looked up,
        and then the packfile can be asked directly for that object using this
        function.
        """
        assert offset >= self._header_size
        self._file.seek(offset)
        unpacked, _ = unpack_object(self._file.read, include_comp=True)
        return (
            unpacked.pack_type_num,
            unpacked.delta_base,
            unpacked.comp_chunks,
        )

    def get_object_at(self, offset):
        """Given an offset in to the packfile return the object that is there.

        Using the associated index the location of an object can be looked up,
        and then the packfile can be asked directly for that object using this
        function.
        """
        try:
            return self._offset_cache[offset]
        except KeyError:
            pass
        assert offset >= self._header_size
        self._file.seek(offset)
        unpacked, _ = unpack_object(self._file.read)
        return (unpacked.pack_type_num, unpacked._obj())


class DeltaChainIterator(object):
    """Abstract iterator over pack data based on delta chains.

    Each object in the pack is guaranteed to be inflated exactly once,
    regardless of how many objects reference it as a delta base. As a result,
    memory usage is proportional to the length of the longest delta chain.

    Subclasses can override _result to define the result type of the iterator.
    By default, results are UnpackedObjects with the following members set:

    * offset
    * obj_type_num
    * obj_chunks
    * pack_type_num
    * delta_base     (for delta types)
    * comp_chunks    (if _include_comp is True)
    * decomp_chunks
    * decomp_len
    * crc32          (if _compute_crc32 is True)
    """

    _compute_crc32 = False
    _include_comp = False

    def __init__(self, file_obj, resolve_ext_ref=None):
        self._file = file_obj
        self._resolve_ext_ref = resolve_ext_ref
        self._pending_ofs = defaultdict(list)
        self._pending_ref = defaultdict(list)
        self._full_ofs = []
        self._shas = {}
        self._ext_refs = []

    @classmethod
    def for_pack_data(cls, pack_data, resolve_ext_ref=None):
        walker = cls(None, resolve_ext_ref=resolve_ext_ref)
        walker.set_pack_data(pack_data)
        for unpacked in pack_data._iter_unpacked():
            walker.record(unpacked)
        return walker

    def record(self, unpacked):
        type_num = unpacked.pack_type_num
        offset = unpacked.offset
        if type_num == OFS_DELTA:
            base_offset = offset - unpacked.delta_base
            self._pending_ofs[base_offset].append(offset)
        elif type_num == REF_DELTA:
            self._pending_ref[unpacked.delta_base].append(offset)
        else:
            self._full_ofs.append((offset, type_num))

    def set_pack_data(self, pack_data):
        self._file = pack_data._file

    def _walk_all_chains(self):
        for offset, type_num in self._full_ofs:
            for result in self._follow_chain(offset, type_num, None):
                yield result
        for result in self._walk_ref_chains():
            yield result
        assert not self._pending_ofs

    def _ensure_no_pending(self):
        if self._pending_ref:
            raise KeyError([sha_to_hex(s) for s in self._pending_ref])

    def _walk_ref_chains(self):
        if not self._resolve_ext_ref:
            self._ensure_no_pending()
            return

        for base_sha, pending in sorted(self._pending_ref.items()):
            if base_sha not in self._pending_ref:
                continue
            try:
                type_num, chunks = self._resolve_ext_ref(base_sha)
            except KeyError:
                # Not an external ref, but may depend on one. Either it will
                # get popped via a _follow_chain call, or we will raise an
                # error below.
                continue
            self._ext_refs.append(base_sha)
            self._pending_ref.pop(base_sha)
            for new_offset in pending:
                for result in self._follow_chain(new_offset, type_num, chunks):
                    yield result

        self._ensure_no_pending()

    def _result(self, unpacked):
        return unpacked

    def _resolve_object(self, offset, obj_type_num, base_chunks):
        self._file.seek(offset)
        unpacked, _ = unpack_object(
            self._file.read,
            include_comp=self._include_comp,
            compute_crc32=self._compute_crc32,
        )
        unpacked.offset = offset
        if base_chunks is None:
            assert unpacked.pack_type_num == obj_type_num
        else:
            assert unpacked.pack_type_num in DELTA_TYPES
            unpacked.obj_type_num = obj_type_num
            unpacked.obj_chunks = apply_delta(base_chunks, unpacked.decomp_chunks)
        return unpacked

    def _follow_chain(self, offset, obj_type_num, base_chunks):
        # Unlike PackData.get_object_at, there is no need to cache offsets as
        # this approach by design inflates each object exactly once.
        todo = [(offset, obj_type_num, base_chunks)]
        for offset, obj_type_num, base_chunks in todo:
            unpacked = self._resolve_object(offset, obj_type_num, base_chunks)
            yield self._result(unpacked)

            unblocked = chain(
                self._pending_ofs.pop(unpacked.offset, []),
                self._pending_ref.pop(unpacked.sha(), []),
            )
            todo.extend(
                (new_offset, unpacked.obj_type_num, unpacked.obj_chunks)
                for new_offset in unblocked
            )

    def __iter__(self):
        return self._walk_all_chains()

    def ext_refs(self):
        return self._ext_refs


class PackIndexer(DeltaChainIterator):
    """Delta chain iterator that yields index entries."""

    _compute_crc32 = True

    def _result(self, unpacked):
        return unpacked.sha(), unpacked.offset, unpacked.crc32


class PackInflater(DeltaChainIterator):
    """Delta chain iterator that yields ShaFile objects."""

    def _result(self, unpacked):
        return unpacked.sha_file()


class SHA1Reader(object):
    """Wrapper for file-like object that remembers the SHA1 of its data."""

    def __init__(self, f):
        self.f = f
        self.sha1 = sha1(b"")

    def read(self, num=None):
        data = self.f.read(num)
        self.sha1.update(data)
        return data

    def check_sha(self):
        stored = self.f.read(20)
        if stored != self.sha1.digest():
            raise ChecksumMismatch(self.sha1.hexdigest(), sha_to_hex(stored))

    def close(self):
        return self.f.close()

    def tell(self):
        return self.f.tell()


class SHA1Writer(object):
    """Wrapper for file-like object that remembers the SHA1 of its data."""

    def __init__(self, f):
        self.f = f
        self.length = 0
        self.sha1 = sha1(b"")

    def write(self, data):
        self.sha1.update(data)
        self.f.write(data)
        self.length += len(data)

    def write_sha(self):
        sha = self.sha1.digest()
        assert len(sha) == 20
        self.f.write(sha)
        self.length += len(sha)
        return sha

    def close(self):
        sha = self.write_sha()
        self.f.close()
        return sha

    def offset(self):
        return self.length

    def tell(self):
        return self.f.tell()


def pack_object_header(type_num, delta_base, size):
    """Create a pack object header for the given object info.

    Args:
      type_num: Numeric type of the object.
      delta_base: Delta base offset or ref, or None for whole objects.
      size: Uncompressed object size.
    Returns: A header for a packed object.
    """
    header = []
    c = (type_num << 4) | (size & 15)
    size >>= 4
    while size:
        header.append(c | 0x80)
        c = size & 0x7F
        size >>= 7
    header.append(c)
    if type_num == OFS_DELTA:
        ret = [delta_base & 0x7F]
        delta_base >>= 7
        while delta_base:
            delta_base -= 1
            ret.insert(0, 0x80 | (delta_base & 0x7F))
            delta_base >>= 7
        header.extend(ret)
    elif type_num == REF_DELTA:
        assert len(delta_base) == 20
        header += delta_base
    return bytearray(header)


def write_pack_object(f, type, object, sha=None, compression_level=-1):
    """Write pack object to a file.

    Args:
      f: File to write to
      type: Numeric type of the object
      object: Object to write
      compression_level: the zlib compression level
    Returns: Tuple with offset at which the object was written, and crc32
    """
    if type in DELTA_TYPES:
        delta_base, object = object
    else:
        delta_base = None
    header = bytes(pack_object_header(type, delta_base, len(object)))
    comp_data = zlib.compress(object, compression_level)
    crc32 = 0
    for data in (header, comp_data):
        f.write(data)
        if sha is not None:
            sha.update(data)
        crc32 = binascii.crc32(data, crc32)
    return crc32 & 0xFFFFFFFF


def write_pack(
    filename,
    objects,
    deltify=None,
    delta_window_size=None,
    compression_level=-1,
):
    """Write a new pack data file.

    Args:
      filename: Path to the new pack file (without .pack extension)
      objects: Iterable of (object, path) tuples to write.
        Should provide __len__
      window_size: Delta window size
      deltify: Whether to deltify pack objects
      compression_level: the zlib compression level
    Returns: Tuple with checksum of pack file and index file
    """
    with GitFile(filename + ".pack", "wb") as f:
        entries, data_sum = write_pack_objects(
            f,
            objects,
            delta_window_size=delta_window_size,
            deltify=deltify,
            compression_level=compression_level,
        )
    entries = sorted([(k, v[0], v[1]) for (k, v) in entries.items()])
    with GitFile(filename + ".idx", "wb") as f:
        return data_sum, write_pack_index_v2(f, entries, data_sum)


def write_pack_header(f, num_objects):
    """Write a pack header for the given number of objects."""
    f.write(b"PACK")  # Pack header
    f.write(struct.pack(b">L", 2))  # Pack version
    f.write(struct.pack(b">L", num_objects))  # Number of objects in pack


def deltify_pack_objects(objects, window_size=None):
    """Generate deltas for pack objects.

    Args:
      objects: An iterable of (object, path) tuples to deltify.
      window_size: Window size; None for default
    Returns: Iterator over type_num, object id, delta_base, content
        delta_base is None for full text entries
    """
    # TODO(user): Use threads
    if window_size is None:
        window_size = DEFAULT_PACK_DELTA_WINDOW_SIZE
    # Build a list of objects ordered by the magic Linus heuristic
    # This helps us find good objects to diff against us
    magic = []
    for obj, path in objects:
        magic.append((obj.type_num, path, -obj.raw_length(), obj))
    magic.sort()

    possible_bases = deque()

    for type_num, path, neg_length, o in magic:
        raw = o.as_raw_string()
        winner = raw
        winner_base = None
        for base in possible_bases:
            if base.type_num != type_num:
                continue
            delta = create_delta(base.as_raw_string(), raw)
            if len(delta) < len(winner):
                winner_base = base.sha().digest()
                winner = delta
        yield type_num, o.sha().digest(), winner_base, winner
        possible_bases.appendleft(o)
        while len(possible_bases) > window_size:
            possible_bases.pop()


def pack_objects_to_data(objects):
    """Create pack data from objects

    Args:
      objects: Pack objects
    Returns: Tuples with (type_num, hexdigest, delta base, object chunks)
    """
    count = len(objects)
    return (
        count,
        (
            (o.type_num, o.sha().digest(), None, o.as_raw_string())
            for (o, path) in objects
        ),
    )


def write_pack_objects(
    f, objects, delta_window_size=None, deltify=None, compression_level=-1
):
    """Write a new pack data file.

    Args:
      f: File to write to
      objects: Iterable of (object, path) tuples to write.
        Should provide __len__
      window_size: Sliding window size for searching for deltas;
                        Set to None for default window size.
      deltify: Whether to deltify objects
      compression_level: the zlib compression level to use
    Returns: Dict mapping id -> (offset, crc32 checksum), pack checksum
    """
    if deltify is None:
        # PERFORMANCE/TODO(user): This should be enabled but is *much* too
        # slow at the moment.
        deltify = False
    if deltify:
        pack_contents = deltify_pack_objects(objects, delta_window_size)
        pack_contents_count = len(objects)
    else:
        pack_contents_count, pack_contents = pack_objects_to_data(objects)

    return write_pack_data(
        f,
        pack_contents_count,
        pack_contents,
        compression_level=compression_level,
    )


def write_pack_data(f, num_records, records, progress=None, compression_level=-1):
    """Write a new pack data file.

    Args:
      f: File to write to
      num_records: Number of records
      records: Iterator over type_num, object_id, delta_base, raw
      progress: Function to report progress to
      compression_level: the zlib compression level
    Returns: Dict mapping id -> (offset, crc32 checksum), pack checksum
    """
    # Write the pack
    entries = {}
    f = SHA1Writer(f)
    write_pack_header(f, num_records)
    for i, (type_num, object_id, delta_base, raw) in enumerate(records):
        if progress is not None:
            progress(("writing pack data: %d/%d\r" % (i, num_records)).encode("ascii"))
        offset = f.offset()
        if delta_base is not None:
            try:
                base_offset, base_crc32 = entries[delta_base]
            except KeyError:
                type_num = REF_DELTA
                raw = (delta_base, raw)
            else:
                type_num = OFS_DELTA
                raw = (offset - base_offset, raw)
        crc32 = write_pack_object(f, type_num, raw, compression_level=compression_level)
        entries[object_id] = (offset, crc32)
    return entries, f.write_sha()


def write_pack_index_v1(f, entries, pack_checksum):
    """Write a new pack index file.

    Args:
      f: A file-like object to write to
      entries: List of tuples with object name (sha), offset_in_pack,
        and crc32_checksum.
      pack_checksum: Checksum of the pack file.
    Returns: The SHA of the written index file
    """
    f = SHA1Writer(f)
    fan_out_table = defaultdict(lambda: 0)
    for (name, offset, entry_checksum) in entries:
        fan_out_table[ord(name[:1])] += 1
    # Fan-out table
    for i in range(0x100):
        f.write(struct.pack(">L", fan_out_table[i]))
        fan_out_table[i + 1] += fan_out_table[i]
    for (name, offset, entry_checksum) in entries:
        if not (offset <= 0xFFFFFFFF):
            raise TypeError("pack format 1 only supports offsets < 2Gb")
        f.write(struct.pack(">L20s", offset, name))
    assert len(pack_checksum) == 20
    f.write(pack_checksum)
    return f.write_sha()


def _delta_encode_size(size):
    ret = bytearray()
    c = size & 0x7F
    size >>= 7
    while size:
        ret.append(c | 0x80)
        c = size & 0x7F
        size >>= 7
    ret.append(c)
    return ret


# The length of delta compression copy operations in version 2 packs is limited
# to 64K.  To copy more, we use several copy operations.  Version 3 packs allow
# 24-bit lengths in copy operations, but we always make version 2 packs.
_MAX_COPY_LEN = 0xFFFF


def _encode_copy_operation(start, length):
    scratch = []
    op = 0x80
    for i in range(4):
        if start & 0xFF << i * 8:
            scratch.append((start >> i * 8) & 0xFF)
            op |= 1 << i
    for i in range(2):
        if length & 0xFF << i * 8:
            scratch.append((length >> i * 8) & 0xFF)
            op |= 1 << (4 + i)
    return bytearray([op] + scratch)


def create_delta(base_buf, target_buf):
    """Use python difflib to work out how to transform base_buf to target_buf.

    Args:
      base_buf: Base buffer
      target_buf: Target buffer
    """
    assert isinstance(base_buf, bytes)
    assert isinstance(target_buf, bytes)
    out_buf = bytearray()
    # write delta header
    out_buf += _delta_encode_size(len(base_buf))
    out_buf += _delta_encode_size(len(target_buf))
    # write out delta opcodes
    seq = difflib.SequenceMatcher(a=base_buf, b=target_buf)
    for opcode, i1, i2, j1, j2 in seq.get_opcodes():
        # Git patch opcodes don't care about deletes!
        # if opcode == 'replace' or opcode == 'delete':
        #    pass
        if opcode == "equal":
            # If they are equal, unpacker will use data from base_buf
            # Write out an opcode that says what range to use
            copy_start = i1
            copy_len = i2 - i1
            while copy_len > 0:
                to_copy = min(copy_len, _MAX_COPY_LEN)
                out_buf += _encode_copy_operation(copy_start, to_copy)
                copy_start += to_copy
                copy_len -= to_copy
        if opcode == "replace" or opcode == "insert":
            # If we are replacing a range or adding one, then we just
            # output it to the stream (prefixed by its size)
            s = j2 - j1
            o = j1
            while s > 127:
                out_buf.append(127)
                out_buf += bytearray(target_buf[o : o + 127])
                s -= 127
                o += 127
            out_buf.append(s)
            out_buf += bytearray(target_buf[o : o + s])
    return bytes(out_buf)


def apply_delta(src_buf, delta):
    """Based on the similar function in git's patch-delta.c.

    Args:
      src_buf: Source buffer
      delta: Delta instructions
    """
    if not isinstance(src_buf, bytes):
        src_buf = b"".join(src_buf)
    if not isinstance(delta, bytes):
        delta = b"".join(delta)
    out = []
    index = 0
    delta_length = len(delta)

    def get_delta_header_size(delta, index):
        size = 0
        i = 0
        while delta:
            cmd = ord(delta[index : index + 1])
            index += 1
            size |= (cmd & ~0x80) << i
            i += 7
            if not cmd & 0x80:
                break
        return size, index

    src_size, index = get_delta_header_size(delta, index)
    dest_size, index = get_delta_header_size(delta, index)
    assert src_size == len(src_buf), "%d vs %d" % (src_size, len(src_buf))
    while index < delta_length:
        cmd = ord(delta[index : index + 1])
        index += 1
        if cmd & 0x80:
            cp_off = 0
            for i in range(4):
                if cmd & (1 << i):
                    x = ord(delta[index : index + 1])
                    index += 1
                    cp_off |= x << (i * 8)
            cp_size = 0
            # Version 3 packs can contain copy sizes larger than 64K.
            for i in range(3):
                if cmd & (1 << (4 + i)):
                    x = ord(delta[index : index + 1])
                    index += 1
                    cp_size |= x << (i * 8)
            if cp_size == 0:
                cp_size = 0x10000
            if (
                cp_off + cp_size < cp_size
                or cp_off + cp_size > src_size
                or cp_size > dest_size
            ):
                break
            out.append(src_buf[cp_off : cp_off + cp_size])
        elif cmd != 0:
            out.append(delta[index : index + cmd])
            index += cmd
        else:
            raise ApplyDeltaError("Invalid opcode 0")

    if index != delta_length:
        raise ApplyDeltaError("delta not empty: %r" % delta[index:])

    if dest_size != chunks_length(out):
        raise ApplyDeltaError("dest size incorrect")

    return out


def write_pack_index_v2(f, entries, pack_checksum):
    """Write a new pack index file.

    Args:
      f: File-like object to write to
      entries: List of tuples with object name (sha), offset_in_pack, and
        crc32_checksum.
      pack_checksum: Checksum of the pack file.
    Returns: The SHA of the index file written
    """
    f = SHA1Writer(f)
    f.write(b"\377tOc")  # Magic!
    f.write(struct.pack(">L", 2))
    fan_out_table = defaultdict(lambda: 0)
    for (name, offset, entry_checksum) in entries:
        fan_out_table[ord(name[:1])] += 1
    # Fan-out table
    largetable = []
    for i in range(0x100):
        f.write(struct.pack(b">L", fan_out_table[i]))
        fan_out_table[i + 1] += fan_out_table[i]
    for (name, offset, entry_checksum) in entries:
        f.write(name)
    for (name, offset, entry_checksum) in entries:
        f.write(struct.pack(b">L", entry_checksum))
    for (name, offset, entry_checksum) in entries:
        if offset < 2 ** 31:
            f.write(struct.pack(b">L", offset))
        else:
            f.write(struct.pack(b">L", 2 ** 31 + len(largetable)))
            largetable.append(offset)
    for offset in largetable:
        f.write(struct.pack(b">Q", offset))
    assert len(pack_checksum) == 20
    f.write(pack_checksum)
    return f.write_sha()


write_pack_index = write_pack_index_v2


class Pack(object):
    """A Git pack object."""

    def __init__(self, basename, resolve_ext_ref=None):
        self._basename = basename
        self._data = None
        self._idx = None
        self._idx_path = self._basename + ".idx"
        self._data_path = self._basename + ".pack"
        self._data_load = lambda: PackData(self._data_path)
        self._idx_load = lambda: load_pack_index(self._idx_path)
        self.resolve_ext_ref = resolve_ext_ref

    @classmethod
    def from_lazy_objects(cls, data_fn, idx_fn):
        """Create a new pack object from callables to load pack data and
        index objects."""
        ret = cls("")
        ret._data_load = data_fn
        ret._idx_load = idx_fn
        return ret

    @classmethod
    def from_objects(cls, data, idx):
        """Create a new pack object from pack data and index objects."""
        ret = cls("")
        ret._data = data
        ret._data.pack = ret
        ret._data_load = None
        ret._idx = idx
        ret._idx_load = None
        ret.check_length_and_checksum()
        return ret

    def name(self):
        """The SHA over the SHAs of the objects in this pack."""
        return self.index.objects_sha1()

    @property
    def data(self):
        """The pack data object being used."""
        if self._data is None:
            self._data = self._data_load()
            self._data.pack = self
            self.check_length_and_checksum()
        return self._data

    @property
    def index(self):
        """The index being used.

        Note: This may be an in-memory index
        """
        if self._idx is None:
            self._idx = self._idx_load()
        return self._idx

    def close(self):
        if self._data is not None:
            self._data.close()
        if self._idx is not None:
            self._idx.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.index == other.index

    def __len__(self):
        """Number of entries in this pack."""
        return len(self.index)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._basename)

    def __iter__(self):
        """Iterate over all the sha1s of the objects in this pack."""
        return iter(self.index)

    def check_length_and_checksum(self):
        """Sanity check the length and checksum of the pack index and data."""
        assert len(self.index) == len(self.data)
        idx_stored_checksum = self.index.get_pack_checksum()
        data_stored_checksum = self.data.get_stored_checksum()
        if idx_stored_checksum != data_stored_checksum:
            raise ChecksumMismatch(
                sha_to_hex(idx_stored_checksum),
                sha_to_hex(data_stored_checksum),
            )

    def check(self):
        """Check the integrity of this pack.

        Raises:
          ChecksumMismatch: if a checksum for the index or data is wrong
        """
        self.index.check()
        self.data.check()
        for obj in self.iterobjects():
            obj.check()
        # TODO: object connectivity checks

    def get_stored_checksum(self):
        return self.data.get_stored_checksum()

    def __contains__(self, sha1):
        """Check whether this pack contains a particular SHA1."""
        try:
            self.index.object_index(sha1)
            return True
        except KeyError:
            return False

    def get_raw_unresolved(self, sha1):
        """Get raw unresolved data for a SHA.

        Args:
          sha1: SHA to return data for
        Returns: Tuple with pack object type, delta base (if applicable),
            list of data chunks
        """
        offset = self.index.object_index(sha1)
        (obj_type, delta_base, chunks) = self.data.get_compressed_data_at(offset)
        if obj_type == OFS_DELTA:
            delta_base = sha_to_hex(self.index.object_sha1(offset - delta_base))
            obj_type = REF_DELTA
        return (obj_type, delta_base, chunks)

    def get_raw(self, sha1):
        offset = self.index.object_index(sha1)
        obj_type, obj = self.data.get_object_at(offset)
        type_num, chunks = self.data.resolve_object(offset, obj_type, obj)
        return type_num, b"".join(chunks)

    def __getitem__(self, sha1):
        """Retrieve the specified SHA1."""
        type, uncomp = self.get_raw(sha1)
        return ShaFile.from_raw_string(type, uncomp, sha=sha1)

    def iterobjects(self):
        """Iterate over the objects in this pack."""
        return iter(
            PackInflater.for_pack_data(self.data, resolve_ext_ref=self.resolve_ext_ref)
        )

    def pack_tuples(self):
        """Provide an iterable for use with write_pack_objects.

        Returns: Object that can iterate over (object, path) tuples
            and provides __len__
        """

        class PackTupleIterable(object):
            def __init__(self, pack):
                self.pack = pack

            def __len__(self):
                return len(self.pack)

            def __iter__(self):
                return ((o, None) for o in self.pack.iterobjects())

        return PackTupleIterable(self)

    def keep(self, msg=None):
        """Add a .keep file for the pack, preventing git from garbage collecting it.

        Args:
          msg: A message written inside the .keep file; can be used later
            to determine whether or not a .keep file is obsolete.
        Returns: The path of the .keep file, as a string.
        """
        keepfile_name = "%s.keep" % self._basename
        with GitFile(keepfile_name, "wb") as keepfile:
            if msg:
                keepfile.write(msg)
                keepfile.write(b"\n")
        return keepfile_name


try:
    from dulwich._pack import (  # type: ignore # noqa: F811
        apply_delta,
        bisect_find_sha,
    )
except ImportError:
    pass
