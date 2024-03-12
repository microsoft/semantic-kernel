# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2009-2017 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import os
import random
import time
from ._compat import long, binary_type
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading


class EntropyPool(object):

    # This is an entropy pool for Python implementations that do not
    # have a working SystemRandom.  I'm not sure there are any, but
    # leaving this code doesn't hurt anything as the library code
    # is used if present.

    def __init__(self, seed=None):
        self.pool_index = 0
        self.digest = None
        self.next_byte = 0
        self.lock = _threading.Lock()
        try:
            import hashlib
            self.hash = hashlib.sha1()
            self.hash_len = 20
        except ImportError:
            try:
                import sha
                self.hash = sha.new()
                self.hash_len = 20
            except ImportError:
                import md5  # pylint: disable=import-error
                self.hash = md5.new()
                self.hash_len = 16
        self.pool = bytearray(b'\0' * self.hash_len)
        if seed is not None:
            self.stir(bytearray(seed))
            self.seeded = True
            self.seed_pid = os.getpid()
        else:
            self.seeded = False
            self.seed_pid = 0

    def stir(self, entropy, already_locked=False):
        if not already_locked:
            self.lock.acquire()
        try:
            for c in entropy:
                if self.pool_index == self.hash_len:
                    self.pool_index = 0
                b = c & 0xff
                self.pool[self.pool_index] ^= b
                self.pool_index += 1
        finally:
            if not already_locked:
                self.lock.release()

    def _maybe_seed(self):
        if not self.seeded or self.seed_pid != os.getpid():
            try:
                seed = os.urandom(16)
            except Exception:
                try:
                    r = open('/dev/urandom', 'rb', 0)
                    try:
                        seed = r.read(16)
                    finally:
                        r.close()
                except Exception:
                    seed = str(time.time())
            self.seeded = True
            self.seed_pid = os.getpid()
            self.digest = None
            seed = bytearray(seed)
            self.stir(seed, True)

    def random_8(self):
        self.lock.acquire()
        try:
            self._maybe_seed()
            if self.digest is None or self.next_byte == self.hash_len:
                self.hash.update(binary_type(self.pool))
                self.digest = bytearray(self.hash.digest())
                self.stir(self.digest, True)
                self.next_byte = 0
            value = self.digest[self.next_byte]
            self.next_byte += 1
        finally:
            self.lock.release()
        return value

    def random_16(self):
        return self.random_8() * 256 + self.random_8()

    def random_32(self):
        return self.random_16() * 65536 + self.random_16()

    def random_between(self, first, last):
        size = last - first + 1
        if size > long(4294967296):
            raise ValueError('too big')
        if size > 65536:
            rand = self.random_32
            max = long(4294967295)
        elif size > 256:
            rand = self.random_16
            max = 65535
        else:
            rand = self.random_8
            max = 255
        return first + size * rand() // (max + 1)

pool = EntropyPool()

try:
    system_random = random.SystemRandom()
except Exception:
    system_random = None

def random_16():
    if system_random is not None:
        return system_random.randrange(0, 65536)
    else:
        return pool.random_16()

def between(first, last):
    if system_random is not None:
        return system_random.randrange(first, last + 1)
    else:
        return pool.random_between(first, last)
