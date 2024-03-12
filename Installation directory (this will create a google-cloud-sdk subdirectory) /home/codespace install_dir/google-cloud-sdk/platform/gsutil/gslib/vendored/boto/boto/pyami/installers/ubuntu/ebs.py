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
#
"""
Automated installer to attach, format and mount an EBS volume.
This installer assumes that you want the volume formatted as
an XFS file system.  To drive this installer, you need the
following section in the boto config passed to the new instance.
You also need to install dateutil by listing python-dateutil
in the list of packages to be installed in the Pyami seciont
of your boto config file.

If there is already a device mounted at the specified mount point,
the installer assumes that it is the ephemeral drive and unmounts
it, remounts it as /tmp and chmods it to 777.

Config file section::

    [EBS]
    volume_id = <the id of the EBS volume, should look like vol-xxxxxxxx>
    logical_volume_name = <the name of the logical volume that contaings
        a reference to the physical volume to be mounted. If this parameter
        is supplied, it overrides the volume_id setting.>
    device = <the linux device the EBS volume should be mounted on>
    mount_point = <directory to mount device, defaults to /ebs>

"""
import boto
from boto.manage.volume import Volume
from boto.exception import EC2ResponseError
import os, time
from boto.pyami.installers.ubuntu.installer import Installer
from string import Template

BackupScriptTemplate = """#!/usr/bin/env python
# Backup EBS volume
import boto
from boto.pyami.scriptbase import ScriptBase
import traceback

class Backup(ScriptBase):

    def main(self):
        try:
            ec2 = boto.connect_ec2()
            self.run("/usr/sbin/xfs_freeze -f ${mount_point}", exit_on_error = True)
            snapshot = ec2.create_snapshot('${volume_id}')
            boto.log.info("Snapshot created: %s " %  snapshot)
        except Exception as e:
            self.notify(subject="${instance_id} Backup Failed", body=traceback.format_exc())
            boto.log.info("Snapshot created: ${volume_id}")
        except Exception as e:
            self.notify(subject="${instance_id} Backup Failed", body=traceback.format_exc())
        finally:
            self.run("/usr/sbin/xfs_freeze -u ${mount_point}")

if __name__ == "__main__":
    b = Backup()
    b.main()
"""

BackupCleanupScript= """#!/usr/bin/env python
import boto
from boto.manage.volume import Volume

# Cleans Backups of EBS volumes

for v in Volume.all():
    v.trim_snapshots(True)
"""

TagBasedBackupCleanupScript= """#!/usr/bin/env python
import boto

# Cleans Backups of EBS volumes

ec2 = boto.connect_ec2()
ec2.trim_snapshots()
"""

class EBSInstaller(Installer):
    """
    Set up the EBS stuff
    """

    def __init__(self, config_file=None):
        super(EBSInstaller, self).__init__(config_file)
        self.instance_id = boto.config.get('Instance', 'instance-id')
        self.device = boto.config.get('EBS', 'device', '/dev/sdp')
        self.volume_id = boto.config.get('EBS', 'volume_id')
        self.logical_volume_name = boto.config.get('EBS', 'logical_volume_name')
        self.mount_point = boto.config.get('EBS', 'mount_point', '/ebs')

    def attach(self):
        ec2 = boto.connect_ec2()
        if self.logical_volume_name:
            # if a logical volume was specified, override the specified volume_id
            # (if there was one) with the current AWS volume for the logical volume:
            logical_volume = next(Volume.find(name=self.logical_volume_name))
            self.volume_id = logical_volume._volume_id
        volume = ec2.get_all_volumes([self.volume_id])[0]
        # wait for the volume to be available. The volume may still be being created
        # from a snapshot.
        while volume.update() != 'available':
            boto.log.info('Volume %s not yet available. Current status = %s.' % (volume.id, volume.status))
            time.sleep(5)
        instance = ec2.get_only_instances([self.instance_id])[0]
        attempt_attach = True
        while attempt_attach:
            try:
                ec2.attach_volume(self.volume_id, self.instance_id, self.device)
                attempt_attach = False
            except EC2ResponseError as e:
                if e.error_code != 'IncorrectState':
                    # if there's an EC2ResonseError with the code set to IncorrectState, delay a bit for ec2
                    # to realize the instance is running, then try again. Otherwise, raise the error:
                    boto.log.info('Attempt to attach the EBS volume %s to this instance (%s) returned %s. Trying again in a bit.' % (self.volume_id, self.instance_id, e.errors))
                    time.sleep(2)
                else:
                    raise e
        boto.log.info('Attached volume %s to instance %s as device %s' % (self.volume_id, self.instance_id, self.device))
        # now wait for the volume device to appear
        while not os.path.exists(self.device):
            boto.log.info('%s still does not exist, waiting 2 seconds' % self.device)
            time.sleep(2)

    def make_fs(self):
        boto.log.info('make_fs...')
        has_fs = self.run('fsck %s' % self.device)
        if has_fs != 0:
            self.run('mkfs -t xfs %s' % self.device)

    def create_backup_script(self):
        t = Template(BackupScriptTemplate)
        s = t.substitute(volume_id=self.volume_id, instance_id=self.instance_id,
                         mount_point=self.mount_point)
        fp = open('/usr/local/bin/ebs_backup', 'w')
        fp.write(s)
        fp.close()
        self.run('chmod +x /usr/local/bin/ebs_backup')

    def create_backup_cleanup_script(self, use_tag_based_cleanup=False):
        fp = open('/usr/local/bin/ebs_backup_cleanup', 'w')
        if use_tag_based_cleanup:
            fp.write(TagBasedBackupCleanupScript)
        else:
            fp.write(BackupCleanupScript)
        fp.close()
        self.run('chmod +x /usr/local/bin/ebs_backup_cleanup')

    def handle_mount_point(self):
        boto.log.info('handle_mount_point')
        if not os.path.isdir(self.mount_point):
            boto.log.info('making directory')
            # mount directory doesn't exist so create it
            self.run("mkdir %s" % self.mount_point)
        else:
            boto.log.info('directory exists already')
            self.run('mount -l')
            lines = self.last_command.output.split('\n')
            for line in lines:
                t = line.split()
                if t and t[2] == self.mount_point:
                    # something is already mounted at the mount point
                    # unmount that and mount it as /tmp
                    if t[0] != self.device:
                        self.run('umount %s' % self.mount_point)
                        self.run('mount %s /tmp' % t[0])
                        break
        self.run('chmod 777 /tmp')
        # Mount up our new EBS volume onto mount_point
        self.run("mount %s %s" % (self.device, self.mount_point))
        self.run('xfs_growfs %s' % self.mount_point)

    def update_fstab(self):
        f = open("/etc/fstab", "a")
        f.write('%s\t%s\txfs\tdefaults 0 0\n' % (self.device, self.mount_point))
        f.close()

    def install(self):
        # First, find and attach the volume
        self.attach()

        # Install the xfs tools
        self.run('apt-get -y install xfsprogs xfsdump')

        # Check to see if the filesystem was created or not
        self.make_fs()

        # create the /ebs directory for mounting
        self.handle_mount_point()

        # create the backup script
        self.create_backup_script()

        # Set up the backup script
        minute = boto.config.get('EBS', 'backup_cron_minute', '0')
        hour = boto.config.get('EBS', 'backup_cron_hour', '4,16')
        self.add_cron("ebs_backup", "/usr/local/bin/ebs_backup", minute=minute, hour=hour)

        # Set up the backup cleanup script
        minute = boto.config.get('EBS', 'backup_cleanup_cron_minute')
        hour = boto.config.get('EBS', 'backup_cleanup_cron_hour')
        if (minute is not None) and (hour is not None):
            # Snapshot clean up can either be done via the manage module, or via the new tag based
            # snapshot code, if the snapshots have been tagged with the name of the associated
            # volume. Check for the presence of the new configuration flag, and use the appropriate
            # cleanup method / script:
            use_tag_based_cleanup = boto.config.has_option('EBS', 'use_tag_based_snapshot_cleanup')
            self.create_backup_cleanup_script(use_tag_based_cleanup)
            self.add_cron("ebs_backup_cleanup", "/usr/local/bin/ebs_backup_cleanup", minute=minute, hour=hour)

        # Set up the fstab
        self.update_fstab()

    def main(self):
        if not os.path.exists(self.device):
            self.install()
        else:
            boto.log.info("Device %s is already attached, skipping EBS Installer" % self.device)
