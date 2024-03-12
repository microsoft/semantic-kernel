#!/usr/bin/python3
#
# Copyright 2007 Google Inc. All Rights Reserved.
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
"""Pure python code for finding unused ports on a host.

This module provides a pick_unused_port() function.
It can also be called via the command line for use in shell scripts.
When called from the command line, it takes one optional argument, which,
if given, is sent to portserver instead of portpicker's PID.
To reserve a port for the lifetime of a bash script, use $BASHPID as this
argument.

There is a race condition between picking a port and your application code
binding to it.  The use of a port server to prevent that is recommended on
loaded test hosts running many tests at a time.

If your code can accept a bound socket as input rather than being handed a
port number consider using socket.bind(('localhost', 0)) to bind to an
available port without a race condition rather than using this library.

Typical usage:
  test_port = portpicker.pick_unused_port()
"""

# pylint: disable=consider-using-f-string
# Some people still use this on old Pythons despite our test matrix and
# supported versions.  Be kind for now, until it gets in our way.
from __future__ import print_function

import logging
import os
import random
import socket
import sys
import time

_winapi = None  # pylint: disable=invalid-name
if sys.platform == 'win32':
    try:
        import _winapi
    except ImportError:
        _winapi = None

# The legacy Bind, IsPortFree, etc. names are not exported.
__all__ = ('bind', 'is_port_free', 'pick_unused_port', 'return_port',
           'add_reserved_port', 'get_port_from_port_server')

_PROTOS = [(socket.SOCK_STREAM, socket.IPPROTO_TCP),
           (socket.SOCK_DGRAM, socket.IPPROTO_UDP)]


# Ports that are currently available to be given out.
_free_ports = set()

# Ports that are reserved or from the portserver that may be returned.
_owned_ports = set()

# Ports that we chose randomly that may be returned.
_random_ports = set()


class NoFreePortFoundError(Exception):
    """Exception indicating that no free port could be found."""


def add_reserved_port(port):
    """Add a port that was acquired by means other than the port server."""
    _free_ports.add(port)


def return_port(port):
    """Return a port that is no longer being used so it can be reused."""
    if port in _random_ports:
        _random_ports.remove(port)
    elif port in _owned_ports:
        _owned_ports.remove(port)
        _free_ports.add(port)
    elif port in _free_ports:
        logging.info("Returning a port that was already returned: %s", port)
    else:
        logging.info("Returning a port that wasn't given by portpicker: %s",
                     port)


def bind(port, socket_type, socket_proto):
    """Try to bind to a socket of the specified type, protocol, and port.

    This is primarily a helper function for PickUnusedPort, used to see
    if a particular port number is available.

    For the port to be considered available, the kernel must support at least
    one of (IPv6, IPv4), and the port must be available on each supported
    family.

    Args:
      port: The port number to bind to, or 0 to have the OS pick a free port.
      socket_type: The type of the socket (ex: socket.SOCK_STREAM).
      socket_proto: The protocol of the socket (ex: socket.IPPROTO_TCP).

    Returns:
      The port number on success or None on failure.
    """
    return _bind(port, socket_type, socket_proto)


def _bind(port, socket_type, socket_proto, return_socket=None,
          return_family=socket.AF_INET6):
    """Internal implementation of bind.

    Args:
      port, socket_type, socket_proto: see bind().
      return_socket: If supplied, a list that we will append an open bound
          reuseaddr socket on the port in question to.
      return_family: The socket family to return in return_socket.

    Returns:
      The port number on success or None on failure.
    """
    # Our return family must come last when returning a bound socket
    # as we cannot keep it bound while testing a bind on the other
    # family with many network stack configurations.
    if return_socket is None or return_family == socket.AF_INET:
        socket_families = (socket.AF_INET6, socket.AF_INET)
    elif return_family == socket.AF_INET6:
        socket_families = (socket.AF_INET, socket.AF_INET6)
    else:
        raise ValueError('unknown return_family %s' % return_family)
    got_socket = False
    for family in socket_families:
        try:
            sock = socket.socket(family, socket_type, socket_proto)
            got_socket = True
        except socket.error:
            continue
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', port))
            if socket_type == socket.SOCK_STREAM:
                sock.listen(1)
            port = sock.getsockname()[1]
        except socket.error:
            return None
        finally:
            if return_socket is None or family != return_family:
                try:
                    # Adding this resolved 1 in ~500 flakiness that we were
                    # seeing from an integration test framework managing a set
                    # of ports with is_port_free().  close() doesn't move the
                    # TCP state machine along quickly.
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
        if return_socket is not None and family == return_family:
            return_socket.append(sock)
            break  # Final iteration due to pre-loop logic; don't close.
    return port if got_socket else None


def is_port_free(port):
    """Check if specified port is free.

    Args:
      port: integer, port to check

    Returns:
      bool, whether port is free to use for both TCP and UDP.
    """
    return _is_port_free(port)


def _is_port_free(port, return_sockets=None):
    """Internal implementation of is_port_free.

    Args:
      port: integer, port to check
      return_sockets: If supplied, a list that we will append open bound
        sockets on the port in question to rather than closing them.

    Returns:
      bool, whether port is free to use for both TCP and UDP.
    """
    return (_bind(port, *_PROTOS[0], return_socket=return_sockets) and
            _bind(port, *_PROTOS[1], return_socket=return_sockets))


def pick_unused_port(pid=None, portserver_address=None):
    """Picks an unused port and reserves it for use by a given process id.

    Args:
      pid: PID to tell the portserver to associate the reservation with. If
        None, the current process's PID is used.
      portserver_address: The address (path) of a unix domain socket
        with which to connect to a portserver, a leading '@'
        character indicates an address in the "abstract namespace".  OR
        On systems without socket.AF_UNIX, this is an AF_INET address.
        If None, or no port is returned by the portserver at the provided
        address, the environment will be checked for a PORTSERVER_ADDRESS
        variable.  If that is not set, no port server will be used.

    If no portserver is used, no pid based reservation is managed by any
    central authority. Race conditions and duplicate assignments may occur.

    Returns:
      A port number that is unused on both TCP and UDP.

    Raises:
      NoFreePortFoundError: No free port could be found.
    """
    return _pick_unused_port(pid, portserver_address)


def _pick_unused_port(pid=None, portserver_address=None,
                     noserver_bind_timeout=0):
    """Internal implementation of pick_unused_port.

    Args:
      pid, portserver_address: See pick_unused_port().
      noserver_bind_timeout: If no portserver was used, this is the number of
        seconds we will attempt to keep a child process around with the ports
        returned open and bound SO_REUSEADDR style to help avoid race condition
        port reuse. A non-zero value attempts os.fork(). Do not use it in a
        multithreaded process.
    """
    try:  # Instead of `if _free_ports:` to handle the race condition.
        port = _free_ports.pop()
    except KeyError:
        pass
    else:
        _owned_ports.add(port)
        return port
    # Provide access to the portserver on an opt-in basis.
    if portserver_address:
        port = get_port_from_port_server(portserver_address, pid=pid)
        if port:
            return port
    if 'PORTSERVER_ADDRESS' in os.environ:
        port = get_port_from_port_server(os.environ['PORTSERVER_ADDRESS'],
                                         pid=pid)
        if port:
            return port
    return _pick_unused_port_without_server(bind_timeout=noserver_bind_timeout)


def _spawn_bound_port_holding_daemon(port, bound_sockets, timeout):
    """If possible, fork()s a daemon process to hold bound_sockets open.

    Emits a warning to stderr if it cannot.

    Args:
      port: The port number the sockets are bound to (informational).
      bound_sockets: The list of bound sockets our child process will hold
          open. If the list is empty, no action is taken.
      timeout: A positive number of seconds the child should sleep for before
          closing the sockets and exiting.
    """
    if bound_sockets and timeout > 0:
        try:
            fork_pid = os.fork()  # This concept only works on POSIX.
        except Exception as err:  # pylint: disable=broad-except
            print('WARNING: Cannot timeout unbinding close of port', port,
                  ' closing on exit. -', err, file=sys.stderr)
        else:
            if fork_pid == 0:
                # This child process inherits and holds bound_sockets open
                # for bind_timeout seconds.
                try:
                    # Close the stdio fds as may be connected to
                    # a pipe that will cause a grandparent process
                    # to wait on before returning. (cl/427587550)
                    os.close(sys.stdin.fileno())
                    os.close(sys.stdout.fileno())
                    os.close(sys.stderr.fileno())
                    time.sleep(timeout)
                    for held_socket in bound_sockets:
                        held_socket.close()
                finally:
                    os._exit(0)


def _pick_unused_port_without_server(bind_timeout=0):
    """Pick an available network port without the help of a port server.

    This code ensures that the port is available on both TCP and UDP.

    This function is an implementation detail of PickUnusedPort(), and
    should not be called by code outside of this module.

    Args:
      bind_timeout: number of seconds to attempt to keep a child process
          process around bound SO_REUSEADDR style to the port. If we cannot
          do that we emit a warning to stderr.

    Returns:
      A port number that is unused on both TCP and UDP.

    Raises:
      NoFreePortFoundError: No free port could be found.
    """
    # Next, try a few times to get an OS-assigned port.
    # Ambrose discovered that on the 2.6 kernel, calling Bind() on UDP socket
    # returns the same port over and over. So always try TCP first.
    port = None
    bound_sockets = [] if bind_timeout > 0 else None
    for _ in range(10):
        # Ask the OS for an unused port.
        port = _bind(0, socket.SOCK_STREAM, socket.IPPROTO_TCP, bound_sockets)
        # Check if this port is unused on the other protocol.
        if (port and port not in _random_ports and
            _bind(port, socket.SOCK_DGRAM, socket.IPPROTO_UDP, bound_sockets)):
            _random_ports.add(port)
            _spawn_bound_port_holding_daemon(port, bound_sockets, bind_timeout)
            return port
        if bound_sockets:
            for held_socket in bound_sockets:
                held_socket.close()
            del bound_sockets[:]

    # Try random ports as a last resort.
    rng = random.Random()
    for _ in range(10):
        port = int(rng.randrange(15000, 25000))
        if port not in _random_ports:
            if _is_port_free(port, bound_sockets):
                _random_ports.add(port)
                _spawn_bound_port_holding_daemon(
                        port, bound_sockets, bind_timeout)
                return port
            if bound_sockets:
                for held_socket in bound_sockets:
                    held_socket.close()
                del bound_sockets[:]

    # Give up.
    raise NoFreePortFoundError()


def _posix_get_port_from_port_server(portserver_address, pid):
    # An AF_UNIX address may start with a zero byte, in which case it is in the
    # "abstract namespace", and doesn't have any filesystem representation.
    # See 'man 7 unix' for details.
    # The convention is to write '@' in the address to represent this zero byte.
    if portserver_address[0] == '@':
        portserver_address = '\0' + portserver_address[1:]

    try:
        # Create socket.
        if hasattr(socket, 'AF_UNIX'):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            # fallback to AF_INET if this is not unix
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Connect to portserver.
            sock.connect(portserver_address)

            # Write request.
            sock.sendall(('%d\n' % pid).encode('ascii'))

            # Read response.
            # 1K should be ample buffer space.
            return sock.recv(1024)
        finally:
            sock.close()
    except socket.error as error:
        print('Socket error when connecting to portserver:', error,
              file=sys.stderr)
        return None


def _windows_get_port_from_port_server(portserver_address, pid):
    if portserver_address[0] == '@':
        portserver_address = '\\\\.\\pipe\\' + portserver_address[1:]

    try:
        handle = _winapi.CreateFile(
            portserver_address,
            _winapi.GENERIC_READ | _winapi.GENERIC_WRITE,
            0,
            0,
            _winapi.OPEN_EXISTING,
            0,
            0)

        _winapi.WriteFile(handle, ('%d\n' % pid).encode('ascii'))
        data, _ = _winapi.ReadFile(handle, 6, 0)
        return data
    except FileNotFoundError as error:
        print('File error when connecting to portserver:', error,
              file=sys.stderr)
        return None


def get_port_from_port_server(portserver_address, pid=None):
    """Request a free a port from a system-wide portserver.

    This follows a very simple portserver protocol:
    The request consists of our pid (in ASCII) followed by a newline.
    The response is a port number and a newline, 0 on failure.

    This function is an implementation detail of pick_unused_port().
    It should not normally be called by code outside of this module.

    Args:
      portserver_address: The address (path) of a unix domain socket
        with which to connect to the portserver.  A leading '@'
        character indicates an address in the "abstract namespace."
        On systems without socket.AF_UNIX, this is an AF_INET address.
      pid: The PID to tell the portserver to associate the reservation with.
        If None, the current process's PID is used.

    Returns:
      The port number on success or None on failure.
    """
    if not portserver_address:
        return None

    if pid is None:
        pid = os.getpid()

    if _winapi:
        buf = _windows_get_port_from_port_server(portserver_address, pid)
    else:
        buf = _posix_get_port_from_port_server(portserver_address, pid)

    if buf is None:
        return None

    try:
        port = int(buf.split(b'\n')[0])
    except ValueError:
        print('Portserver failed to find a port.', file=sys.stderr)
        return None
    _owned_ports.add(port)
    return port


# Legacy APIs.
# pylint: disable=invalid-name
Bind = bind
GetPortFromPortServer = get_port_from_port_server
IsPortFree = is_port_free
PickUnusedPort = pick_unused_port
# pylint: enable=invalid-name


def main(argv):
    """If passed an arg, treat it as a PID, otherwise we use getppid().

    A second optional argument can be a bind timeout in seconds that will be
    used ONLY if no portserver is found. We attempt to leave a process around
    holding the port open and bound with SO_REUSEADDR set for timeout seconds.
    If the timeout bind was not possible, a warning is emitted to stderr.

      #!/bin/bash
      port="$(python -m portpicker $$ 1.23)"
      test_my_server "$port"

    This will pick a port for your script's PID and assign it to $port, if no
    portserver was used, it attempts to keep a socket bound to $port for 1.23
    seconds after the portpicker process has exited. This is a convenient hack
    to attempt to prevent port reallocation during scripts outside of
    portserver managed environments.

    Older versions of the portpicker CLI ignore everything beyond the first arg.
    Older versions also used getpid() instead of getppid(), so script users are
    strongly encouraged to be explicit and pass $$ or your languages equivalent
    to associate the port with the PID of the controlling process.
    """
    # Our command line is trivial so I avoid an argparse import. If we ever
    # grow more than 1-2 args, switch to a using argparse.
    if '-h' in argv or '--help' in argv:
        print(argv[0], 'usage:\n')
        import inspect
        print(inspect.getdoc(main))
        sys.exit(1)
    pid=int(argv[1]) if len(argv) > 1 else os.getppid()
    bind_timeout=float(argv[2]) if len(argv) > 2 else 0
    port = _pick_unused_port(pid=pid, noserver_bind_timeout=bind_timeout)
    if not port:
        sys.exit(1)
    print(port)


if __name__ == '__main__':
    main(sys.argv)
