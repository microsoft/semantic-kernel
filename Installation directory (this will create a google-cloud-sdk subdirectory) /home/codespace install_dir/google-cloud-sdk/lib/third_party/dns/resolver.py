# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2003-2017 Nominum, Inc.
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

"""DNS stub resolver."""

import socket
import sys
import time
import random

try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

import dns.exception
import dns.flags
import dns.ipv4
import dns.ipv6
import dns.message
import dns.name
import dns.query
import dns.rcode
import dns.rdataclass
import dns.rdatatype
import dns.reversename
import dns.tsig
from ._compat import xrange, string_types

if sys.platform == 'win32':
    try:
        import winreg as _winreg
    except ImportError:
        import _winreg  # pylint: disable=import-error

class NXDOMAIN(dns.exception.DNSException):
    """The DNS query name does not exist."""
    supp_kwargs = {'qnames', 'responses'}
    fmt = None  # we have our own __str__ implementation

    def _check_kwargs(self, qnames, responses=None):
        if not isinstance(qnames, (list, tuple, set)):
            raise AttributeError("qnames must be a list, tuple or set")
        if len(qnames) == 0:
            raise AttributeError("qnames must contain at least one element")
        if responses is None:
            responses = {}
        elif not isinstance(responses, dict):
            raise AttributeError("responses must be a dict(qname=response)")
        kwargs = dict(qnames=qnames, responses=responses)
        return kwargs

    def __str__(self):
        if 'qnames' not in self.kwargs:
            return super(NXDOMAIN, self).__str__()
        qnames = self.kwargs['qnames']
        if len(qnames) > 1:
            msg = 'None of DNS query names exist'
        else:
            msg = 'The DNS query name does not exist'
        qnames = ', '.join(map(str, qnames))
        return "{}: {}".format(msg, qnames)

    def canonical_name(self):
        if not 'qnames' in self.kwargs:
            raise TypeError("parametrized exception required")
        IN = dns.rdataclass.IN
        CNAME = dns.rdatatype.CNAME
        cname = None
        for qname in self.kwargs['qnames']:
            response = self.kwargs['responses'][qname]
            for answer in response.answer:
                if answer.rdtype != CNAME or answer.rdclass != IN:
                    continue
                cname = answer.items[0].target.to_text()
            if cname is not None:
                return dns.name.from_text(cname)
        return self.kwargs['qnames'][0]
    canonical_name = property(canonical_name, doc=(
        "Return the unresolved canonical name."))

    def __add__(self, e_nx):
        """Augment by results from another NXDOMAIN exception."""
        qnames0 = list(self.kwargs.get('qnames', []))
        responses0 = dict(self.kwargs.get('responses', {}))
        responses1 = e_nx.kwargs.get('responses', {})
        for qname1 in e_nx.kwargs.get('qnames', []):
            if qname1 not in qnames0:
                qnames0.append(qname1)
            if qname1 in responses1:
                responses0[qname1] = responses1[qname1]
        return NXDOMAIN(qnames=qnames0, responses=responses0)

    def qnames(self):
        """All of the names that were tried.

        Returns a list of ``dns.name.Name``.
        """
        return self.kwargs['qnames']

    def responses(self):
        """A map from queried names to their NXDOMAIN responses.

        Returns a dict mapping a ``dns.name.Name`` to a
        ``dns.message.Message``.
        """
        return self.kwargs['responses']

    def response(self, qname):
        """The response for query *qname*.

        Returns a ``dns.message.Message``.
        """
        return self.kwargs['responses'][qname]


class YXDOMAIN(dns.exception.DNSException):
    """The DNS query name is too long after DNAME substitution."""

# The definition of the Timeout exception has moved from here to the
# dns.exception module.  We keep dns.resolver.Timeout defined for
# backwards compatibility.

Timeout = dns.exception.Timeout


class NoAnswer(dns.exception.DNSException):
    """The DNS response does not contain an answer to the question."""
    fmt = 'The DNS response does not contain an answer ' + \
          'to the question: {query}'
    supp_kwargs = {'response'}

    def _fmt_kwargs(self, **kwargs):
        return super(NoAnswer, self)._fmt_kwargs(
            query=kwargs['response'].question)


class NoNameservers(dns.exception.DNSException):
    """All nameservers failed to answer the query.

    errors: list of servers and respective errors
    The type of errors is
    [(server IP address, any object convertible to string)].
    Non-empty errors list will add explanatory message ()
    """

    msg = "All nameservers failed to answer the query."
    fmt = "%s {query}: {errors}" % msg[:-1]
    supp_kwargs = {'request', 'errors'}

    def _fmt_kwargs(self, **kwargs):
        srv_msgs = []
        for err in kwargs['errors']:
            srv_msgs.append('Server {} {} port {} answered {}'.format(err[0],
                            'TCP' if err[1] else 'UDP', err[2], err[3]))
        return super(NoNameservers, self)._fmt_kwargs(
            query=kwargs['request'].question, errors='; '.join(srv_msgs))


class NotAbsolute(dns.exception.DNSException):
    """An absolute domain name is required but a relative name was provided."""


class NoRootSOA(dns.exception.DNSException):
    """There is no SOA RR at the DNS root name. This should never happen!"""


class NoMetaqueries(dns.exception.DNSException):
    """DNS metaqueries are not allowed."""


class Answer(object):
    """DNS stub resolver answer.

    Instances of this class bundle up the result of a successful DNS
    resolution.

    For convenience, the answer object implements much of the sequence
    protocol, forwarding to its ``rrset`` attribute.  E.g.
    ``for a in answer`` is equivalent to ``for a in answer.rrset``.
    ``answer[i]`` is equivalent to ``answer.rrset[i]``, and
    ``answer[i:j]`` is equivalent to ``answer.rrset[i:j]``.

    Note that CNAMEs or DNAMEs in the response may mean that answer
    RRset's name might not be the query name.
    """

    def __init__(self, qname, rdtype, rdclass, response,
                 raise_on_no_answer=True):
        self.qname = qname
        self.rdtype = rdtype
        self.rdclass = rdclass
        self.response = response
        min_ttl = -1
        rrset = None
        for count in xrange(0, 15):
            try:
                rrset = response.find_rrset(response.answer, qname,
                                            rdclass, rdtype)
                if min_ttl == -1 or rrset.ttl < min_ttl:
                    min_ttl = rrset.ttl
                break
            except KeyError:
                if rdtype != dns.rdatatype.CNAME:
                    try:
                        crrset = response.find_rrset(response.answer,
                                                     qname,
                                                     rdclass,
                                                     dns.rdatatype.CNAME)
                        if min_ttl == -1 or crrset.ttl < min_ttl:
                            min_ttl = crrset.ttl
                        for rd in crrset:
                            qname = rd.target
                            break
                        continue
                    except KeyError:
                        if raise_on_no_answer:
                            raise NoAnswer(response=response)
                if raise_on_no_answer:
                    raise NoAnswer(response=response)
        if rrset is None and raise_on_no_answer:
            raise NoAnswer(response=response)
        self.canonical_name = qname
        self.rrset = rrset
        if rrset is None:
            while 1:
                # Look for a SOA RR whose owner name is a superdomain
                # of qname.
                try:
                    srrset = response.find_rrset(response.authority, qname,
                                                 rdclass, dns.rdatatype.SOA)
                    if min_ttl == -1 or srrset.ttl < min_ttl:
                        min_ttl = srrset.ttl
                    if srrset[0].minimum < min_ttl:
                        min_ttl = srrset[0].minimum
                    break
                except KeyError:
                    try:
                        qname = qname.parent()
                    except dns.name.NoParent:
                        break
        self.expiration = time.time() + min_ttl

    def __getattr__(self, attr):
        if attr == 'name':
            return self.rrset.name
        elif attr == 'ttl':
            return self.rrset.ttl
        elif attr == 'covers':
            return self.rrset.covers
        elif attr == 'rdclass':
            return self.rrset.rdclass
        elif attr == 'rdtype':
            return self.rrset.rdtype
        else:
            raise AttributeError(attr)

    def __len__(self):
        return self.rrset and len(self.rrset) or 0

    def __iter__(self):
        return self.rrset and iter(self.rrset) or iter(tuple())

    def __getitem__(self, i):
        if self.rrset is None:
            raise IndexError
        return self.rrset[i]

    def __delitem__(self, i):
        if self.rrset is None:
            raise IndexError
        del self.rrset[i]


class Cache(object):
    """Simple thread-safe DNS answer cache."""

    def __init__(self, cleaning_interval=300.0):
        """*cleaning_interval*, a ``float`` is the number of seconds between
        periodic cleanings.
        """

        self.data = {}
        self.cleaning_interval = cleaning_interval
        self.next_cleaning = time.time() + self.cleaning_interval
        self.lock = _threading.Lock()

    def _maybe_clean(self):
        """Clean the cache if it's time to do so."""

        now = time.time()
        if self.next_cleaning <= now:
            keys_to_delete = []
            for (k, v) in self.data.items():
                if v.expiration <= now:
                    keys_to_delete.append(k)
            for k in keys_to_delete:
                del self.data[k]
            now = time.time()
            self.next_cleaning = now + self.cleaning_interval

    def get(self, key):
        """Get the answer associated with *key*.

        Returns None if no answer is cached for the key.

        *key*, a ``(dns.name.Name, int, int)`` tuple whose values are the
        query name, rdtype, and rdclass respectively.

        Returns a ``dns.resolver.Answer`` or ``None``.
        """

        try:
            self.lock.acquire()
            self._maybe_clean()
            v = self.data.get(key)
            if v is None or v.expiration <= time.time():
                return None
            return v
        finally:
            self.lock.release()

    def put(self, key, value):
        """Associate key and value in the cache.

        *key*, a ``(dns.name.Name, int, int)`` tuple whose values are the
        query name, rdtype, and rdclass respectively.

        *value*, a ``dns.resolver.Answer``, the answer.
        """

        try:
            self.lock.acquire()
            self._maybe_clean()
            self.data[key] = value
        finally:
            self.lock.release()

    def flush(self, key=None):
        """Flush the cache.

        If *key* is not ``None``, only that item is flushed.  Otherwise
        the entire cache is flushed.

        *key*, a ``(dns.name.Name, int, int)`` tuple whose values are the
        query name, rdtype, and rdclass respectively.
        """

        try:
            self.lock.acquire()
            if key is not None:
                if key in self.data:
                    del self.data[key]
            else:
                self.data = {}
                self.next_cleaning = time.time() + self.cleaning_interval
        finally:
            self.lock.release()


class LRUCacheNode(object):
    """LRUCache node."""

    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = self
        self.next = self

    def link_before(self, node):
        self.prev = node.prev
        self.next = node
        node.prev.next = self
        node.prev = self

    def link_after(self, node):
        self.prev = node
        self.next = node.next
        node.next.prev = self
        node.next = self

    def unlink(self):
        self.next.prev = self.prev
        self.prev.next = self.next


class LRUCache(object):
    """Thread-safe, bounded, least-recently-used DNS answer cache.

    This cache is better than the simple cache (above) if you're
    running a web crawler or other process that does a lot of
    resolutions.  The LRUCache has a maximum number of nodes, and when
    it is full, the least-recently used node is removed to make space
    for a new one.
    """

    def __init__(self, max_size=100000):
        """*max_size*, an ``int``, is the maximum number of nodes to cache;
        it must be greater than 0.
        """

        self.data = {}
        self.set_max_size(max_size)
        self.sentinel = LRUCacheNode(None, None)
        self.lock = _threading.Lock()

    def set_max_size(self, max_size):
        if max_size < 1:
            max_size = 1
        self.max_size = max_size

    def get(self, key):
        """Get the answer associated with *key*.

        Returns None if no answer is cached for the key.

        *key*, a ``(dns.name.Name, int, int)`` tuple whose values are the
        query name, rdtype, and rdclass respectively.

        Returns a ``dns.resolver.Answer`` or ``None``.
        """

        try:
            self.lock.acquire()
            node = self.data.get(key)
            if node is None:
                return None
            # Unlink because we're either going to move the node to the front
            # of the LRU list or we're going to free it.
            node.unlink()
            if node.value.expiration <= time.time():
                del self.data[node.key]
                return None
            node.link_after(self.sentinel)
            return node.value
        finally:
            self.lock.release()

    def put(self, key, value):
        """Associate key and value in the cache.

        *key*, a ``(dns.name.Name, int, int)`` tuple whose values are the
        query name, rdtype, and rdclass respectively.

        *value*, a ``dns.resolver.Answer``, the answer.
        """

        try:
            self.lock.acquire()
            node = self.data.get(key)
            if node is not None:
                node.unlink()
                del self.data[node.key]
            while len(self.data) >= self.max_size:
                node = self.sentinel.prev
                node.unlink()
                del self.data[node.key]
            node = LRUCacheNode(key, value)
            node.link_after(self.sentinel)
            self.data[key] = node
        finally:
            self.lock.release()

    def flush(self, key=None):
        """Flush the cache.

        If *key* is not ``None``, only that item is flushed.  Otherwise
        the entire cache is flushed.

        *key*, a ``(dns.name.Name, int, int)`` tuple whose values are the
        query name, rdtype, and rdclass respectively.
        """

        try:
            self.lock.acquire()
            if key is not None:
                node = self.data.get(key)
                if node is not None:
                    node.unlink()
                    del self.data[node.key]
            else:
                node = self.sentinel.next
                while node != self.sentinel:
                    next = node.next
                    node.prev = None
                    node.next = None
                    node = next
                self.data = {}
        finally:
            self.lock.release()


class Resolver(object):
    """DNS stub resolver."""

    def __init__(self, filename='/etc/resolv.conf', configure=True):
        """*filename*, a ``text`` or file object, specifying a file
        in standard /etc/resolv.conf format.  This parameter is meaningful
        only when *configure* is true and the platform is POSIX.

        *configure*, a ``bool``.  If True (the default), the resolver
        instance is configured in the normal fashion for the operating
        system the resolver is running on.  (I.e. by reading a
        /etc/resolv.conf file on POSIX systems and from the registry
        on Windows systems.)
        """

        self.domain = None
        self.nameservers = None
        self.nameserver_ports = None
        self.port = None
        self.search = None
        self.timeout = None
        self.lifetime = None
        self.keyring = None
        self.keyname = None
        self.keyalgorithm = None
        self.edns = None
        self.ednsflags = None
        self.payload = None
        self.cache = None
        self.flags = None
        self.retry_servfail = False
        self.rotate = False

        self.reset()
        if configure:
            if sys.platform == 'win32':
                self.read_registry()
            elif filename:
                self.read_resolv_conf(filename)

    def reset(self):
        """Reset all resolver configuration to the defaults."""

        self.domain = \
            dns.name.Name(dns.name.from_text(socket.gethostname())[1:])
        if len(self.domain) == 0:
            self.domain = dns.name.root
        self.nameservers = []
        self.nameserver_ports = {}
        self.port = 53
        self.search = []
        self.timeout = 2.0
        self.lifetime = 30.0
        self.keyring = None
        self.keyname = None
        self.keyalgorithm = dns.tsig.default_algorithm
        self.edns = -1
        self.ednsflags = 0
        self.payload = 0
        self.cache = None
        self.flags = None
        self.retry_servfail = False
        self.rotate = False

    def read_resolv_conf(self, f):
        """Process *f* as a file in the /etc/resolv.conf format.  If f is
        a ``text``, it is used as the name of the file to open; otherwise it
        is treated as the file itself."""

        if isinstance(f, string_types):
            try:
                f = open(f, 'r')
            except IOError:
                # /etc/resolv.conf doesn't exist, can't be read, etc.
                # We'll just use the default resolver configuration.
                self.nameservers = ['127.0.0.1']
                return
            want_close = True
        else:
            want_close = False
        try:
            for l in f:
                if len(l) == 0 or l[0] == '#' or l[0] == ';':
                    continue
                tokens = l.split()

                # Any line containing less than 2 tokens is malformed
                if len(tokens) < 2:
                    continue

                if tokens[0] == 'nameserver':
                    self.nameservers.append(tokens[1])
                elif tokens[0] == 'domain':
                    self.domain = dns.name.from_text(tokens[1])
                elif tokens[0] == 'search':
                    for suffix in tokens[1:]:
                        self.search.append(dns.name.from_text(suffix))
                elif tokens[0] == 'options':
                    if 'rotate' in tokens[1:]:
                        self.rotate = True
        finally:
            if want_close:
                f.close()
        if len(self.nameservers) == 0:
            self.nameservers.append('127.0.0.1')

    def _determine_split_char(self, entry):
        #
        # The windows registry irritatingly changes the list element
        # delimiter in between ' ' and ',' (and vice-versa) in various
        # versions of windows.
        #
        if entry.find(' ') >= 0:
            split_char = ' '
        elif entry.find(',') >= 0:
            split_char = ','
        else:
            # probably a singleton; treat as a space-separated list.
            split_char = ' '
        return split_char

    def _config_win32_nameservers(self, nameservers):
        # we call str() on nameservers to convert it from unicode to ascii
        nameservers = str(nameservers)
        split_char = self._determine_split_char(nameservers)
        ns_list = nameservers.split(split_char)
        for ns in ns_list:
            if ns not in self.nameservers:
                self.nameservers.append(ns)

    def _config_win32_domain(self, domain):
        # we call str() on domain to convert it from unicode to ascii
        self.domain = dns.name.from_text(str(domain))

    def _config_win32_search(self, search):
        # we call str() on search to convert it from unicode to ascii
        search = str(search)
        split_char = self._determine_split_char(search)
        search_list = search.split(split_char)
        for s in search_list:
            if s not in self.search:
                self.search.append(dns.name.from_text(s))

    def _config_win32_fromkey(self, key, always_try_domain):
        try:
            servers, rtype = _winreg.QueryValueEx(key, 'NameServer')
        except WindowsError:  # pylint: disable=undefined-variable
            servers = None
        if servers:
            self._config_win32_nameservers(servers)
        if servers or always_try_domain:
            try:
                dom, rtype = _winreg.QueryValueEx(key, 'Domain')
                if dom:
                    self._config_win32_domain(dom)
            except WindowsError:  # pylint: disable=undefined-variable
                pass
        else:
            try:
                servers, rtype = _winreg.QueryValueEx(key, 'DhcpNameServer')
            except WindowsError:  # pylint: disable=undefined-variable
                servers = None
            if servers:
                self._config_win32_nameservers(servers)
                try:
                    dom, rtype = _winreg.QueryValueEx(key, 'DhcpDomain')
                    if dom:
                        self._config_win32_domain(dom)
                except WindowsError:  # pylint: disable=undefined-variable
                    pass
        try:
            search, rtype = _winreg.QueryValueEx(key, 'SearchList')
        except WindowsError:  # pylint: disable=undefined-variable
            search = None
        if search:
            self._config_win32_search(search)

    def read_registry(self):
        """Extract resolver configuration from the Windows registry."""

        lm = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        want_scan = False
        try:
            try:
                # XP, 2000
                tcp_params = _winreg.OpenKey(lm,
                                             r'SYSTEM\CurrentControlSet'
                                             r'\Services\Tcpip\Parameters')
                want_scan = True
            except EnvironmentError:
                # ME
                tcp_params = _winreg.OpenKey(lm,
                                             r'SYSTEM\CurrentControlSet'
                                             r'\Services\VxD\MSTCP')
            try:
                self._config_win32_fromkey(tcp_params, True)
            finally:
                tcp_params.Close()
            if want_scan:
                interfaces = _winreg.OpenKey(lm,
                                             r'SYSTEM\CurrentControlSet'
                                             r'\Services\Tcpip\Parameters'
                                             r'\Interfaces')
                try:
                    i = 0
                    while True:
                        try:
                            guid = _winreg.EnumKey(interfaces, i)
                            i += 1
                            key = _winreg.OpenKey(interfaces, guid)
                            if not self._win32_is_nic_enabled(lm, guid, key):
                                continue
                            try:
                                self._config_win32_fromkey(key, False)
                            finally:
                                key.Close()
                        except EnvironmentError:
                            break
                finally:
                    interfaces.Close()
        finally:
            lm.Close()

    def _win32_is_nic_enabled(self, lm, guid, interface_key):
        # Look in the Windows Registry to determine whether the network
        # interface corresponding to the given guid is enabled.
        #
        # (Code contributed by Paul Marks, thanks!)
        #
        try:
            # This hard-coded location seems to be consistent, at least
            # from Windows 2000 through Vista.
            connection_key = _winreg.OpenKey(
                lm,
                r'SYSTEM\CurrentControlSet\Control\Network'
                r'\{4D36E972-E325-11CE-BFC1-08002BE10318}'
                r'\%s\Connection' % guid)

            try:
                # The PnpInstanceID points to a key inside Enum
                (pnp_id, ttype) = _winreg.QueryValueEx(
                    connection_key, 'PnpInstanceID')

                if ttype != _winreg.REG_SZ:
                    raise ValueError

                device_key = _winreg.OpenKey(
                    lm, r'SYSTEM\CurrentControlSet\Enum\%s' % pnp_id)

                try:
                    # Get ConfigFlags for this device
                    (flags, ttype) = _winreg.QueryValueEx(
                        device_key, 'ConfigFlags')

                    if ttype != _winreg.REG_DWORD:
                        raise ValueError

                    # Based on experimentation, bit 0x1 indicates that the
                    # device is disabled.
                    return not flags & 0x1

                finally:
                    device_key.Close()
            finally:
                connection_key.Close()
        except (EnvironmentError, ValueError):
            # Pre-vista, enabled interfaces seem to have a non-empty
            # NTEContextList; this was how dnspython detected enabled
            # nics before the code above was contributed.  We've retained
            # the old method since we don't know if the code above works
            # on Windows 95/98/ME.
            try:
                (nte, ttype) = _winreg.QueryValueEx(interface_key,
                                                    'NTEContextList')
                return nte is not None
            except WindowsError:  # pylint: disable=undefined-variable
                return False

    def _compute_timeout(self, start, lifetime=None):
        lifetime = self.lifetime if lifetime is None else lifetime
        now = time.time()
        duration = now - start
        if duration < 0:
            if duration < -1:
                # Time going backwards is bad.  Just give up.
                raise Timeout(timeout=duration)
            else:
                # Time went backwards, but only a little.  This can
                # happen, e.g. under vmware with older linux kernels.
                # Pretend it didn't happen.
                now = start
        if duration >= lifetime:
            raise Timeout(timeout=duration)
        return min(lifetime - duration, self.timeout)

    def query(self, qname, rdtype=dns.rdatatype.A, rdclass=dns.rdataclass.IN,
              tcp=False, source=None, raise_on_no_answer=True, source_port=0,
              lifetime=None):
        """Query nameservers to find the answer to the question.

        The *qname*, *rdtype*, and *rdclass* parameters may be objects
        of the appropriate type, or strings that can be converted into objects
        of the appropriate type.

        *qname*, a ``dns.name.Name`` or ``text``, the query name.

        *rdtype*, an ``int`` or ``text``,  the query type.

        *rdclass*, an ``int`` or ``text``,  the query class.

        *tcp*, a ``bool``.  If ``True``, use TCP to make the query.

        *source*, a ``text`` or ``None``.  If not ``None``, bind to this IP
        address when making queries.

        *raise_on_no_answer*, a ``bool``.  If ``True``, raise
        ``dns.resolver.NoAnswer`` if there's no answer to the question.

        *source_port*, an ``int``, the port from which to send the message.

        *lifetime*, a ``float``, how long query should run before timing out.

        Raises ``dns.exception.Timeout`` if no answers could be found
        in the specified lifetime.

        Raises ``dns.resolver.NXDOMAIN`` if the query name does not exist.

        Raises ``dns.resolver.YXDOMAIN`` if the query name is too long after
        DNAME substitution.

        Raises ``dns.resolver.NoAnswer`` if *raise_on_no_answer* is
        ``True`` and the query name exists but has no RRset of the
        desired type and class.

        Raises ``dns.resolver.NoNameservers`` if no non-broken
        nameservers are available to answer the question.

        Returns a ``dns.resolver.Answer`` instance.
        """

        if isinstance(qname, string_types):
            qname = dns.name.from_text(qname, None)
        if isinstance(rdtype, string_types):
            rdtype = dns.rdatatype.from_text(rdtype)
        if dns.rdatatype.is_metatype(rdtype):
            raise NoMetaqueries
        if isinstance(rdclass, string_types):
            rdclass = dns.rdataclass.from_text(rdclass)
        if dns.rdataclass.is_metaclass(rdclass):
            raise NoMetaqueries
        qnames_to_try = []
        if qname.is_absolute():
            qnames_to_try.append(qname)
        else:
            if len(qname) > 1:
                qnames_to_try.append(qname.concatenate(dns.name.root))
            if self.search:
                for suffix in self.search:
                    qnames_to_try.append(qname.concatenate(suffix))
            else:
                qnames_to_try.append(qname.concatenate(self.domain))
        all_nxdomain = True
        nxdomain_responses = {}
        start = time.time()
        _qname = None # make pylint happy
        for _qname in qnames_to_try:
            if self.cache:
                answer = self.cache.get((_qname, rdtype, rdclass))
                if answer is not None:
                    if answer.rrset is None and raise_on_no_answer:
                        raise NoAnswer(response=answer.response)
                    else:
                        return answer
            request = dns.message.make_query(_qname, rdtype, rdclass)
            if self.keyname is not None:
                request.use_tsig(self.keyring, self.keyname,
                                 algorithm=self.keyalgorithm)
            request.use_edns(self.edns, self.ednsflags, self.payload)
            if self.flags is not None:
                request.flags = self.flags
            response = None
            #
            # make a copy of the servers list so we can alter it later.
            #
            nameservers = self.nameservers[:]
            errors = []
            if self.rotate:
                random.shuffle(nameservers)
            backoff = 0.10
            while response is None:
                if len(nameservers) == 0:
                    raise NoNameservers(request=request, errors=errors)
                for nameserver in nameservers[:]:
                    timeout = self._compute_timeout(start, lifetime)
                    port = self.nameserver_ports.get(nameserver, self.port)
                    try:
                        tcp_attempt = tcp
                        if tcp:
                            response = dns.query.tcp(request, nameserver,
                                                     timeout, port,
                                                     source=source,
                                                     source_port=source_port)
                        else:
                            response = dns.query.udp(request, nameserver,
                                                     timeout, port,
                                                     source=source,
                                                     source_port=source_port)
                            if response.flags & dns.flags.TC:
                                # Response truncated; retry with TCP.
                                tcp_attempt = True
                                timeout = self._compute_timeout(start, lifetime)
                                response = \
                                    dns.query.tcp(request, nameserver,
                                                  timeout, port,
                                                  source=source,
                                                  source_port=source_port)
                    except (socket.error, dns.exception.Timeout) as ex:
                        #
                        # Communication failure or timeout.  Go to the
                        # next server
                        #
                        errors.append((nameserver, tcp_attempt, port, ex,
                                       response))
                        response = None
                        continue
                    except dns.query.UnexpectedSource as ex:
                        #
                        # Who knows?  Keep going.
                        #
                        errors.append((nameserver, tcp_attempt, port, ex,
                                       response))
                        response = None
                        continue
                    except dns.exception.FormError as ex:
                        #
                        # We don't understand what this server is
                        # saying.  Take it out of the mix and
                        # continue.
                        #
                        nameservers.remove(nameserver)
                        errors.append((nameserver, tcp_attempt, port, ex,
                                       response))
                        response = None
                        continue
                    except EOFError as ex:
                        #
                        # We're using TCP and they hung up on us.
                        # Probably they don't support TCP (though
                        # they're supposed to!).  Take it out of the
                        # mix and continue.
                        #
                        nameservers.remove(nameserver)
                        errors.append((nameserver, tcp_attempt, port, ex,
                                       response))
                        response = None
                        continue
                    rcode = response.rcode()
                    if rcode == dns.rcode.YXDOMAIN:
                        ex = YXDOMAIN()
                        errors.append((nameserver, tcp_attempt, port, ex,
                                       response))
                        raise ex
                    if rcode == dns.rcode.NOERROR or \
                            rcode == dns.rcode.NXDOMAIN:
                        break
                    #
                    # We got a response, but we're not happy with the
                    # rcode in it.  Remove the server from the mix if
                    # the rcode isn't SERVFAIL.
                    #
                    if rcode != dns.rcode.SERVFAIL or not self.retry_servfail:
                        nameservers.remove(nameserver)
                    errors.append((nameserver, tcp_attempt, port,
                                   dns.rcode.to_text(rcode), response))
                    response = None
                if response is not None:
                    break
                #
                # All nameservers failed!
                #
                if len(nameservers) > 0:
                    #
                    # But we still have servers to try.  Sleep a bit
                    # so we don't pound them!
                    #
                    timeout = self._compute_timeout(start, lifetime)
                    sleep_time = min(timeout, backoff)
                    backoff *= 2
                    time.sleep(sleep_time)
            if response.rcode() == dns.rcode.NXDOMAIN:
                nxdomain_responses[_qname] = response
                continue
            all_nxdomain = False
            break
        if all_nxdomain:
            raise NXDOMAIN(qnames=qnames_to_try, responses=nxdomain_responses)
        answer = Answer(_qname, rdtype, rdclass, response,
                        raise_on_no_answer)
        if self.cache:
            self.cache.put((_qname, rdtype, rdclass), answer)
        return answer

    def use_tsig(self, keyring, keyname=None,
                 algorithm=dns.tsig.default_algorithm):
        """Add a TSIG signature to the query.

        See the documentation of the Message class for a complete
        description of the keyring dictionary.

        *keyring*, a ``dict``, the TSIG keyring to use.  If a
        *keyring* is specified but a *keyname* is not, then the key
        used will be the first key in the *keyring*.  Note that the
        order of keys in a dictionary is not defined, so applications
        should supply a keyname when a keyring is used, unless they
        know the keyring contains only one key.

        *keyname*, a ``dns.name.Name`` or ``None``, the name of the TSIG key
        to use; defaults to ``None``. The key must be defined in the keyring.

        *algorithm*, a ``dns.name.Name``, the TSIG algorithm to use.
        """

        self.keyring = keyring
        if keyname is None:
            self.keyname = list(self.keyring.keys())[0]
        else:
            self.keyname = keyname
        self.keyalgorithm = algorithm

    def use_edns(self, edns, ednsflags, payload):
        """Configure EDNS behavior.

        *edns*, an ``int``, is the EDNS level to use.  Specifying
        ``None``, ``False``, or ``-1`` means "do not use EDNS", and in this case
        the other parameters are ignored.  Specifying ``True`` is
        equivalent to specifying 0, i.e. "use EDNS0".

        *ednsflags*, an ``int``, the EDNS flag values.

        *payload*, an ``int``, is the EDNS sender's payload field, which is the
        maximum size of UDP datagram the sender can handle.  I.e. how big
        a response to this message can be.
        """

        if edns is None:
            edns = -1
        self.edns = edns
        self.ednsflags = ednsflags
        self.payload = payload

    def set_flags(self, flags):
        """Overrides the default flags with your own.

        *flags*, an ``int``, the message flags to use.
        """

        self.flags = flags


#: The default resolver.
default_resolver = None


def get_default_resolver():
    """Get the default resolver, initializing it if necessary."""
    if default_resolver is None:
        reset_default_resolver()
    return default_resolver


def reset_default_resolver():
    """Re-initialize default resolver.

    Note that the resolver configuration (i.e. /etc/resolv.conf on UNIX
    systems) will be re-read immediately.
    """

    global default_resolver
    default_resolver = Resolver()


def query(qname, rdtype=dns.rdatatype.A, rdclass=dns.rdataclass.IN,
          tcp=False, source=None, raise_on_no_answer=True,
          source_port=0, lifetime=None):
    """Query nameservers to find the answer to the question.

    This is a convenience function that uses the default resolver
    object to make the query.

    See ``dns.resolver.Resolver.query`` for more information on the
    parameters.
    """

    return get_default_resolver().query(qname, rdtype, rdclass, tcp, source,
                                        raise_on_no_answer, source_port,
                                        lifetime)


def zone_for_name(name, rdclass=dns.rdataclass.IN, tcp=False, resolver=None):
    """Find the name of the zone which contains the specified name.

    *name*, an absolute ``dns.name.Name`` or ``text``, the query name.

    *rdclass*, an ``int``, the query class.

    *tcp*, a ``bool``.  If ``True``, use TCP to make the query.

    *resolver*, a ``dns.resolver.Resolver`` or ``None``, the resolver to use.
    If ``None``, the default resolver is used.

    Raises ``dns.resolver.NoRootSOA`` if there is no SOA RR at the DNS
    root.  (This is only likely to happen if you're using non-default
    root servers in your network and they are misconfigured.)

    Returns a ``dns.name.Name``.
    """

    if isinstance(name, string_types):
        name = dns.name.from_text(name, dns.name.root)
    if resolver is None:
        resolver = get_default_resolver()
    if not name.is_absolute():
        raise NotAbsolute(name)
    while 1:
        try:
            answer = resolver.query(name, dns.rdatatype.SOA, rdclass, tcp)
            if answer.rrset.name == name:
                return name
            # otherwise we were CNAMEd or DNAMEd and need to look higher
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        try:
            name = name.parent()
        except dns.name.NoParent:
            raise NoRootSOA

#
# Support for overriding the system resolver for all python code in the
# running process.
#

_protocols_for_socktype = {
    socket.SOCK_DGRAM: [socket.SOL_UDP],
    socket.SOCK_STREAM: [socket.SOL_TCP],
}

_resolver = None
_original_getaddrinfo = socket.getaddrinfo
_original_getnameinfo = socket.getnameinfo
_original_getfqdn = socket.getfqdn
_original_gethostbyname = socket.gethostbyname
_original_gethostbyname_ex = socket.gethostbyname_ex
_original_gethostbyaddr = socket.gethostbyaddr


def _getaddrinfo(host=None, service=None, family=socket.AF_UNSPEC, socktype=0,
                 proto=0, flags=0):
    if flags & (socket.AI_ADDRCONFIG | socket.AI_V4MAPPED) != 0:
        raise NotImplementedError
    if host is None and service is None:
        raise socket.gaierror(socket.EAI_NONAME)
    v6addrs = []
    v4addrs = []
    canonical_name = None
    try:
        # Is host None or a V6 address literal?
        if host is None:
            canonical_name = 'localhost'
            if flags & socket.AI_PASSIVE != 0:
                v6addrs.append('::')
                v4addrs.append('0.0.0.0')
            else:
                v6addrs.append('::1')
                v4addrs.append('127.0.0.1')
        else:
            parts = host.split('%')
            if len(parts) == 2:
                ahost = parts[0]
            else:
                ahost = host
            addr = dns.ipv6.inet_aton(ahost)
            v6addrs.append(host)
            canonical_name = host
    except Exception:
        try:
            # Is it a V4 address literal?
            addr = dns.ipv4.inet_aton(host)
            v4addrs.append(host)
            canonical_name = host
        except Exception:
            if flags & socket.AI_NUMERICHOST == 0:
                try:
                    if family == socket.AF_INET6 or family == socket.AF_UNSPEC:
                        v6 = _resolver.query(host, dns.rdatatype.AAAA,
                                             raise_on_no_answer=False)
                        # Note that setting host ensures we query the same name
                        # for A as we did for AAAA.
                        host = v6.qname
                        canonical_name = v6.canonical_name.to_text(True)
                        if v6.rrset is not None:
                            for rdata in v6.rrset:
                                v6addrs.append(rdata.address)
                    if family == socket.AF_INET or family == socket.AF_UNSPEC:
                        v4 = _resolver.query(host, dns.rdatatype.A,
                                             raise_on_no_answer=False)
                        host = v4.qname
                        canonical_name = v4.canonical_name.to_text(True)
                        if v4.rrset is not None:
                            for rdata in v4.rrset:
                                v4addrs.append(rdata.address)
                except dns.resolver.NXDOMAIN:
                    raise socket.gaierror(socket.EAI_NONAME)
                except Exception:
                    raise socket.gaierror(socket.EAI_SYSTEM)
    port = None
    try:
        # Is it a port literal?
        if service is None:
            port = 0
        else:
            port = int(service)
    except Exception:
        if flags & socket.AI_NUMERICSERV == 0:
            try:
                port = socket.getservbyname(service)
            except Exception:
                pass
    if port is None:
        raise socket.gaierror(socket.EAI_NONAME)
    tuples = []
    if socktype == 0:
        socktypes = [socket.SOCK_DGRAM, socket.SOCK_STREAM]
    else:
        socktypes = [socktype]
    if flags & socket.AI_CANONNAME != 0:
        cname = canonical_name
    else:
        cname = ''
    if family == socket.AF_INET6 or family == socket.AF_UNSPEC:
        for addr in v6addrs:
            for socktype in socktypes:
                for proto in _protocols_for_socktype[socktype]:
                    tuples.append((socket.AF_INET6, socktype, proto,
                                   cname, (addr, port, 0, 0)))
    if family == socket.AF_INET or family == socket.AF_UNSPEC:
        for addr in v4addrs:
            for socktype in socktypes:
                for proto in _protocols_for_socktype[socktype]:
                    tuples.append((socket.AF_INET, socktype, proto,
                                   cname, (addr, port)))
    if len(tuples) == 0:
        raise socket.gaierror(socket.EAI_NONAME)
    return tuples


def _getnameinfo(sockaddr, flags=0):
    host = sockaddr[0]
    port = sockaddr[1]
    if len(sockaddr) == 4:
        scope = sockaddr[3]
        family = socket.AF_INET6
    else:
        scope = None
        family = socket.AF_INET
    tuples = _getaddrinfo(host, port, family, socket.SOCK_STREAM,
                          socket.SOL_TCP, 0)
    if len(tuples) > 1:
        raise socket.error('sockaddr resolved to multiple addresses')
    addr = tuples[0][4][0]
    if flags & socket.NI_DGRAM:
        pname = 'udp'
    else:
        pname = 'tcp'
    qname = dns.reversename.from_address(addr)
    if flags & socket.NI_NUMERICHOST == 0:
        try:
            answer = _resolver.query(qname, 'PTR')
            hostname = answer.rrset[0].target.to_text(True)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            if flags & socket.NI_NAMEREQD:
                raise socket.gaierror(socket.EAI_NONAME)
            hostname = addr
            if scope is not None:
                hostname += '%' + str(scope)
    else:
        hostname = addr
        if scope is not None:
            hostname += '%' + str(scope)
    if flags & socket.NI_NUMERICSERV:
        service = str(port)
    else:
        service = socket.getservbyport(port, pname)
    return (hostname, service)


def _getfqdn(name=None):
    if name is None:
        name = socket.gethostname()
    try:
        return _getnameinfo(_getaddrinfo(name, 80)[0][4])[0]
    except Exception:
        return name


def _gethostbyname(name):
    return _gethostbyname_ex(name)[2][0]


def _gethostbyname_ex(name):
    aliases = []
    addresses = []
    tuples = _getaddrinfo(name, 0, socket.AF_INET, socket.SOCK_STREAM,
                          socket.SOL_TCP, socket.AI_CANONNAME)
    canonical = tuples[0][3]
    for item in tuples:
        addresses.append(item[4][0])
    # XXX we just ignore aliases
    return (canonical, aliases, addresses)


def _gethostbyaddr(ip):
    try:
        dns.ipv6.inet_aton(ip)
        sockaddr = (ip, 80, 0, 0)
        family = socket.AF_INET6
    except Exception:
        sockaddr = (ip, 80)
        family = socket.AF_INET
    (name, port) = _getnameinfo(sockaddr, socket.NI_NAMEREQD)
    aliases = []
    addresses = []
    tuples = _getaddrinfo(name, 0, family, socket.SOCK_STREAM, socket.SOL_TCP,
                          socket.AI_CANONNAME)
    canonical = tuples[0][3]
    for item in tuples:
        addresses.append(item[4][0])
    # XXX we just ignore aliases
    return (canonical, aliases, addresses)


def override_system_resolver(resolver=None):
    """Override the system resolver routines in the socket module with
    versions which use dnspython's resolver.

    This can be useful in testing situations where you want to control
    the resolution behavior of python code without having to change
    the system's resolver settings (e.g. /etc/resolv.conf).

    The resolver to use may be specified; if it's not, the default
    resolver will be used.

    resolver, a ``dns.resolver.Resolver`` or ``None``, the resolver to use.
    """

    if resolver is None:
        resolver = get_default_resolver()
    global _resolver
    _resolver = resolver
    socket.getaddrinfo = _getaddrinfo
    socket.getnameinfo = _getnameinfo
    socket.getfqdn = _getfqdn
    socket.gethostbyname = _gethostbyname
    socket.gethostbyname_ex = _gethostbyname_ex
    socket.gethostbyaddr = _gethostbyaddr


def restore_system_resolver():
    """Undo the effects of prior override_system_resolver()."""

    global _resolver
    _resolver = None
    socket.getaddrinfo = _original_getaddrinfo
    socket.getnameinfo = _original_getnameinfo
    socket.getfqdn = _original_getfqdn
    socket.gethostbyname = _original_gethostbyname
    socket.gethostbyname_ex = _original_gethostbyname_ex
    socket.gethostbyaddr = _original_gethostbyaddr
