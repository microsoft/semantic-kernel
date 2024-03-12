# Copyright (c) 2009-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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


class BlockDeviceType(object):
    """
    Represents parameters for a block device.
    """

    def __init__(self,
                 connection=None,
                 ephemeral_name=None,
                 no_device=False,
                 volume_id=None,
                 snapshot_id=None,
                 status=None,
                 attach_time=None,
                 delete_on_termination=False,
                 size=None,
                 volume_type=None,
                 iops=None,
                 encrypted=None):
        self.connection = connection
        self.ephemeral_name = ephemeral_name
        self.no_device = no_device
        self.volume_id = volume_id
        self.snapshot_id = snapshot_id
        self.status = status
        self.attach_time = attach_time
        self.delete_on_termination = delete_on_termination
        self.size = size
        self.volume_type = volume_type
        self.iops = iops
        self.encrypted = encrypted

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        lname = name.lower()
        if name == 'volumeId':
            self.volume_id = value
        elif lname == 'virtualname':
            self.ephemeral_name = value
        elif lname == 'nodevice':
            self.no_device = (value == 'true')
        elif lname == 'snapshotid':
            self.snapshot_id = value
        elif lname == 'volumesize':
            self.size = int(value)
        elif lname == 'status':
            self.status = value
        elif lname == 'attachtime':
            self.attach_time = value
        elif lname == 'deleteontermination':
            self.delete_on_termination = (value == 'true')
        elif lname == 'volumetype':
            self.volume_type = value
        elif lname == 'iops':
            self.iops = int(value)
        elif lname == 'encrypted':
            self.encrypted = (value == 'true')
        else:
            setattr(self, name, value)

# for backwards compatibility
EBSBlockDeviceType = BlockDeviceType


class BlockDeviceMapping(dict):
    """
    Represents a collection of BlockDeviceTypes when creating ec2 instances.

    Example:
    dev_sda1 = BlockDeviceType()
    dev_sda1.size = 100   # change root volume to 100GB instead of default
    bdm = BlockDeviceMapping()
    bdm['/dev/sda1'] = dev_sda1
    reservation = image.run(..., block_device_map=bdm, ...)
    """

    def __init__(self, connection=None):
        """
        :type connection: :class:`boto.ec2.EC2Connection`
        :param connection: Optional connection.
        """
        dict.__init__(self)
        self.connection = connection
        self.current_name = None
        self.current_value = None

    def startElement(self, name, attrs, connection):
        lname = name.lower()
        if lname in ['ebs', 'virtualname']:
            self.current_value = BlockDeviceType(self)
            return self.current_value

    def endElement(self, name, value, connection):
        lname = name.lower()
        if lname in ['device', 'devicename']:
            self.current_name = value
        elif lname in ['item', 'member']:
            self[self.current_name] = self.current_value

    def ec2_build_list_params(self, params, prefix=''):
        pre = '%sBlockDeviceMapping' % prefix
        return self._build_list_params(params, prefix=pre)

    def autoscale_build_list_params(self, params, prefix=''):
        pre = '%sBlockDeviceMappings.member' % prefix
        return self._build_list_params(params, prefix=pre)

    def _build_list_params(self, params, prefix=''):
        i = 1
        for dev_name in self:
            pre = '%s.%d' % (prefix, i)
            params['%s.DeviceName' % pre] = dev_name
            block_dev = self[dev_name]
            if block_dev.ephemeral_name:
                params['%s.VirtualName' % pre] = block_dev.ephemeral_name
            else:
                if block_dev.no_device:
                    params['%s.NoDevice' % pre] = ''
                else:
                    if block_dev.snapshot_id:
                        params['%s.Ebs.SnapshotId' % pre] = block_dev.snapshot_id
                    if block_dev.size:
                        params['%s.Ebs.VolumeSize' % pre] = block_dev.size
                    if block_dev.delete_on_termination:
                        params['%s.Ebs.DeleteOnTermination' % pre] = 'true'
                    else:
                        params['%s.Ebs.DeleteOnTermination' % pre] = 'false'
                    if block_dev.volume_type:
                        params['%s.Ebs.VolumeType' % pre] = block_dev.volume_type
                    if block_dev.iops is not None:
                        params['%s.Ebs.Iops' % pre] = block_dev.iops
                    # The encrypted flag (even if False) cannot be specified for the root EBS
                    # volume.
                    if block_dev.encrypted is not None:
                        if block_dev.encrypted:
                            params['%s.Ebs.Encrypted' % pre] = 'true'
                        else:
                            params['%s.Ebs.Encrypted' % pre] = 'false'

            i += 1
