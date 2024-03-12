# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""
The cmdshell module uses the paramiko package to create SSH connections
to the servers that are represented by instance objects. The module has
functions for running commands, managing files, and opening interactive
shell sessions over those connections.
"""
from boto.mashups.interactive import interactive_shell
import boto
import os
import time
import shutil
import paramiko
import socket
import subprocess

from boto.compat import StringIO

class SSHClient(object):
    """
    This class creates a paramiko.SSHClient() object that represents
    a session with an SSH server. You can use the SSHClient object to send
    commands to the remote host and manipulate files on the remote host. 
    
    :ivar server: A Server object or FakeServer object.
    :ivar host_key_file: The path to the user's .ssh key files.
    :ivar uname: The username for the SSH connection. Default = 'root'.
    :ivar timeout: The optional timeout variable for the TCP connection.
    :ivar ssh_pwd: An optional password to use for authentication or for
                    unlocking the private key.
    """
    def __init__(self, server,
                 host_key_file='~/.ssh/known_hosts',
                 uname='root', timeout=None, ssh_pwd=None):
        self.server = server
        self.host_key_file = host_key_file
        self.uname = uname
        self._timeout = timeout
        self._pkey = paramiko.RSAKey.from_private_key_file(server.ssh_key_file,
                                                           password=ssh_pwd)
        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.load_system_host_keys()
        self._ssh_client.load_host_keys(os.path.expanduser(host_key_file))
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    def connect(self, num_retries=5):
        """
        Connect to an SSH server and authenticate with it.
        
        :type num_retries: int
        :param num_retries: The maximum number of connection attempts.
        """
        retry = 0
        while retry < num_retries:
            try:
                self._ssh_client.connect(self.server.hostname,
                                         username=self.uname,
                                         pkey=self._pkey,
                                         timeout=self._timeout)
                return
            except socket.error as xxx_todo_changeme:
                (value, message) = xxx_todo_changeme.args
                if value in (51, 61, 111):
                    print('SSH Connection refused, will retry in 5 seconds')
                    time.sleep(5)
                    retry += 1
                else:
                    raise
            except paramiko.BadHostKeyException:
                print("%s has an entry in ~/.ssh/known_hosts and it doesn't match" % self.server.hostname)
                print('Edit that file to remove the entry and then hit return to try again')
                raw_input('Hit Enter when ready')
                retry += 1
            except EOFError:
                print('Unexpected Error from SSH Connection, retry in 5 seconds')
                time.sleep(5)
                retry += 1
        print('Could not establish SSH connection')

    def open_sftp(self):
        """
        Open an SFTP session on the SSH server.
        
        :rtype: :class:`paramiko.sftp_client.SFTPClient`
        :return: An SFTP client object.
        """
        return self._ssh_client.open_sftp()

    def get_file(self, src, dst):
        """
        Open an SFTP session on the remote host, and copy a file from
        the remote host to the specified path on the local host.
        
        :type src: string
        :param src: The path to the target file on the remote host.
        
        :type dst: string
        :param dst: The path on your local host where you want to
                    store the file.
        """
        sftp_client = self.open_sftp()
        sftp_client.get(src, dst)

    def put_file(self, src, dst):
        """
        Open an SFTP session on the remote host, and copy a file from
        the local host to the specified path on the remote host.
        
        :type src: string
        :param src: The path to the target file on your local host.
        
        :type dst: string
        :param dst: The path on the remote host where you want to store
                    the file.
        """
        sftp_client = self.open_sftp()
        sftp_client.put(src, dst)

    def open(self, filename, mode='r', bufsize=-1):
        """
        Open an SFTP session to the remote host, and open a file on
        that host.
        
        :type filename: string
        :param filename: The path to the file on the remote host.
        
        :type mode: string
        :param mode: The file interaction mode.
        
        :type bufsize: integer
        :param bufsize: The file buffer size.
        
        :rtype: :class:`paramiko.sftp_file.SFTPFile`
        :return: A paramiko proxy object for a file on the remote server.
        """
        sftp_client = self.open_sftp()
        return sftp_client.open(filename, mode, bufsize)

    def listdir(self, path):
        """
        List all of the files and subdirectories at the specified path
        on the remote host.
        
        :type path: string
        :param path: The base path from which to obtain the list.
          
        :rtype: list
        :return: A list of files and subdirectories at the specified path.
        """
        sftp_client = self.open_sftp()
        return sftp_client.listdir(path)

    def isdir(self, path):
        """
        Check the specified path on the remote host to determine if
        it is a directory.
        
        :type path: string
        :param path: The path to the directory that you want to check.
        
        :rtype: integer
        :return: If the path is a directory, the function returns 1.
                If the path is a file or an invalid path, the function
                returns 0.
        """
        status = self.run('[ -d %s ] || echo "FALSE"' % path)
        if status[1].startswith('FALSE'):
            return 0
        return 1

    def exists(self, path):
        """
        Check the remote host for the specified path, or a file
        at the specified path. This function returns 1 if the
        path or the file exist on the remote host, and returns 0 if
        the path or the file does not exist on the remote host.
        
        :type path: string
        :param path: The path to the directory or file that you want to check.
        
        :rtype: integer
        :return: If the path or the file exist, the function returns 1.
                If the path or the file do not exist on the remote host,
                the function returns 0.
        """
        
        status = self.run('[ -a %s ] || echo "FALSE"' % path)
        if status[1].startswith('FALSE'):
            return 0
        return 1

    def shell(self):
        """
        Start an interactive shell session with the remote host.
        """
        channel = self._ssh_client.invoke_shell()
        interactive_shell(channel)

    def run(self, command):
        """
        Run a command on the remote host.
        
        :type command: string
        :param command: The command that you want to send to the remote host.

        :rtype: tuple
        :return: This function returns a tuple that contains an integer status,
                the stdout from the command, and the stderr from the command.

        """
        boto.log.debug('running:%s on %s' % (command, self.server.instance_id))
        status = 0
        try:
            t = self._ssh_client.exec_command(command)
        except paramiko.SSHException:
            status = 1
        std_out = t[1].read()
        std_err = t[2].read()
        t[0].close()
        t[1].close()
        t[2].close()
        boto.log.debug('stdout: %s' % std_out)
        boto.log.debug('stderr: %s' % std_err)
        return (status, std_out, std_err)

    def run_pty(self, command):
        """
        Request a pseudo-terminal from a server, and execute a command on that
        server.

        :type command: string
        :param command: The command that you want to run on the remote host.
        
        :rtype: :class:`paramiko.channel.Channel`
        :return: An open channel object.
        """
        boto.log.debug('running:%s on %s' % (command, self.server.instance_id))
        channel = self._ssh_client.get_transport().open_session()
        channel.get_pty()
        channel.exec_command(command)
        return channel

    def close(self):
        """
        Close an SSH session and any open channels that are tied to it.
        """
        transport = self._ssh_client.get_transport()
        transport.close()
        self.server.reset_cmdshell()

class LocalClient(object):
    """
    :ivar server: A Server object or FakeServer object.
    :ivar host_key_file: The path to the user's .ssh key files.
    :ivar uname: The username for the SSH connection. Default = 'root'.
    """
    def __init__(self, server, host_key_file=None, uname='root'):
        self.server = server
        self.host_key_file = host_key_file
        self.uname = uname

    def get_file(self, src, dst):
        """
        Copy a file from one directory to another.
        """
        shutil.copyfile(src, dst)

    def put_file(self, src, dst):
        """
        Copy a file from one directory to another.
        """
        shutil.copyfile(src, dst)

    def listdir(self, path):
        """
        List all of the files and subdirectories at the specified path.
        
        :rtype: list
        :return: Return a list containing the names of the entries
                in the directory given by path.
        """
        return os.listdir(path)

    def isdir(self, path):
        """
        Check the specified path to determine if it is a directory.
        
        :rtype: boolean
        :return: Returns True if the path is an existing directory.
        """
        return os.path.isdir(path)

    def exists(self, path):
        """
        Check for the specified path, or check a file at the specified path.
        
        :rtype: boolean
        :return: If the path or the file exist, the function returns True.
        """
        return os.path.exists(path)

    def shell(self):
        raise NotImplementedError('shell not supported with LocalClient')

    def run(self):
        """
        Open a subprocess and run a command on the local host.
        
        :rtype: tuple
        :return: This function returns a tuple that contains an integer status
                and a string with the combined stdout and stderr output.
        """
        boto.log.info('running:%s' % self.command)
        log_fp = StringIO()
        process = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(1)
            t = process.communicate()
            log_fp.write(t[0])
            log_fp.write(t[1])
        boto.log.info(log_fp.getvalue())
        boto.log.info('output: %s' % log_fp.getvalue())
        return (process.returncode, log_fp.getvalue())

    def close(self):
        pass

class FakeServer(object):
    """
    This object has a subset of the variables that are normally in a
    :class:`boto.manage.server.Server` object. You can use this FakeServer
    object to create a :class:`boto.manage.SSHClient` object if you
    don't have a real Server object.
    
    :ivar instance: A boto Instance object.
    :ivar ssh_key_file: The path to the SSH key file.
    """
    def __init__(self, instance, ssh_key_file):
        self.instance = instance
        self.ssh_key_file = ssh_key_file
        self.hostname = instance.dns_name
        self.instance_id = self.instance.id

def start(server):
    """
    Connect to the specified server.

    :return: If the server is local, the function returns a 
            :class:`boto.manage.cmdshell.LocalClient` object.
            If the server is remote, the function returns a
            :class:`boto.manage.cmdshell.SSHClient` object.
    """
    instance_id = boto.config.get('Instance', 'instance-id', None)
    if instance_id == server.instance_id:
        return LocalClient(server)
    else:
        return SSHClient(server)

def sshclient_from_instance(instance, ssh_key_file,
                            host_key_file='~/.ssh/known_hosts',
                            user_name='root', ssh_pwd=None):
    """
    Create and return an SSHClient object given an
    instance object.

    :type instance: :class`boto.ec2.instance.Instance` object
    :param instance: The instance object.

    :type ssh_key_file: string
    :param ssh_key_file: A path to the private key file that is 
                        used to log into the instance.

    :type host_key_file: string
    :param host_key_file: A path to the known_hosts file used
                          by the SSH client.
                          Defaults to ~/.ssh/known_hosts
    :type user_name: string
    :param user_name: The username to use when logging into
                      the instance.  Defaults to root.

    :type ssh_pwd: string
    :param ssh_pwd: The passphrase, if any, associated with
                    private key.
    """
    s = FakeServer(instance, ssh_key_file)
    return SSHClient(s, host_key_file, user_name, ssh_pwd)
