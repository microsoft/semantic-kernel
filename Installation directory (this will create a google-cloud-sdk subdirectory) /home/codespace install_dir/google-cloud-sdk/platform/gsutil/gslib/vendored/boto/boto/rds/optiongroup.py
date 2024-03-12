# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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
Represents an OptionGroup
"""

from boto.rds.dbsecuritygroup import DBSecurityGroup
from boto.resultset import ResultSet


class OptionGroup(object):
    """
    Represents an RDS option group

    Properties reference available from the AWS documentation at
    http://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_OptionGroup.html

    :ivar connection: :py:class:`boto.rds.RDSConnection` associated with the
                      current object
    :ivar name: Name of the option group
    :ivar description: The description of the option group
    :ivar engine_name: The name of the database engine to use
    :ivar major_engine_version: The major version number of the engine to use
    :ivar allow_both_vpc_and_nonvpc: Indicates whether this option group can be
                                     applied to both VPC and non-VPC instances.
                                     The value ``True`` indicates the option
                                     group can be applied to both VPC and
                                     non-VPC instances.
    :ivar vpc_id: If AllowsVpcAndNonVpcInstanceMemberships is 'false', this
                  field is blank. If AllowsVpcAndNonVpcInstanceMemberships is
                  ``True`` and this field is blank, then this option group can
                  be applied to both VPC and non-VPC instances. If this field
                  contains a value, then this option group can only be applied
                  to instances that are in the VPC indicated by this field.
    :ivar options: The list of :py:class:`boto.rds.optiongroup.Option` objects
                   associated with the group
    """
    def __init__(self, connection=None, name=None, engine_name=None,
                 major_engine_version=None, description=None,
                 allow_both_vpc_and_nonvpc=False, vpc_id=None):
        self.name = name
        self.engine_name = engine_name
        self.major_engine_version = major_engine_version
        self.description = description
        self.allow_both_vpc_and_nonvpc = allow_both_vpc_and_nonvpc
        self.vpc_id = vpc_id
        self.options = []

    def __repr__(self):
        return 'OptionGroup:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'Options':
            self.options = ResultSet([
                ('Options', Option)
            ])
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'OptionGroupName':
            self.name = value
        elif name == 'EngineName':
            self.engine_name = value
        elif name == 'MajorEngineVersion':
            self.major_engine_version = value
        elif name == 'OptionGroupDescription':
            self.description = value
        elif name == 'AllowsVpcAndNonVpcInstanceMemberships':
            if value.lower() == 'true':
                self.allow_both_vpc_and_nonvpc = True
            else:
                self.allow_both_vpc_and_nonvpc = False
        elif name == 'VpcId':
            self.vpc_id = value
        else:
            setattr(self, name, value)

    def delete(self):
        return self.connection.delete_option_group(self.name)


class Option(object):
    """
    Describes a Option for use in an OptionGroup

    :ivar name: The name of the option
    :ivar description: The description of the option.
    :ivar permanent: Indicate if this option is permanent.
    :ivar persistent: Indicate if this option is persistent.
    :ivar port: If required, the port configured for this option to use.
    :ivar settings: The option settings for this option.
    :ivar db_security_groups: If the option requires access to a port, then
                              this DB Security Group allows access to the port.
    :ivar vpc_security_groups: If the option requires access to a port, then
                               this VPC Security Group allows access to the
                               port.
    """
    def __init__(self, name=None, description=None, permanent=False,
                 persistent=False, port=None, settings=None,
                 db_security_groups=None, vpc_security_groups=None):
        self.name = name
        self.description = description
        self.permanent = permanent
        self.persistent = persistent
        self.port = port
        self.settings = settings
        self.db_security_groups = db_security_groups
        self.vpc_security_groups = vpc_security_groups

        if self.settings is None:
            self.settings = []

        if self.db_security_groups is None:
            self.db_security_groups = []

        if self.vpc_security_groups is None:
            self.vpc_security_groups = []

    def __repr__(self):
        return 'Option:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'OptionSettings':
            self.settings = ResultSet([
                ('OptionSettings', OptionSetting)
            ])
        elif name == 'DBSecurityGroupMemberships':
            self.db_security_groups = ResultSet([
                ('DBSecurityGroupMemberships', DBSecurityGroup)
            ])
        elif name == 'VpcSecurityGroupMemberships':
            self.vpc_security_groups = ResultSet([
                ('VpcSecurityGroupMemberships', VpcSecurityGroup)
            ])
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'OptionName':
            self.name = value
        elif name == 'OptionDescription':
            self.description = value
        elif name == 'Permanent':
            if value.lower() == 'true':
                self.permenant = True
            else:
                self.permenant = False
        elif name == 'Persistent':
            if value.lower() == 'true':
                self.persistent = True
            else:
                self.persistent = False
        elif name == 'Port':
            self.port = int(value)
        else:
            setattr(self, name, value)


class OptionSetting(object):
    """
    Describes a OptionSetting for use in an Option

    :ivar name: The name of the option that has settings that you can set.
    :ivar description: The description of the option setting.
    :ivar value: The current value of the option setting.
    :ivar default_value: The default value of the option setting.
    :ivar allowed_values: The allowed values of the option setting.
    :ivar data_type: The data type of the option setting.
    :ivar apply_type: The DB engine specific parameter type.
    :ivar is_modifiable: A Boolean value that, when true, indicates the option
                         setting can be modified from the default.
    :ivar is_collection: Indicates if the option setting is part of a
                         collection.
    """

    def __init__(self, name=None, description=None, value=None,
                 default_value=False, allowed_values=None, data_type=None,
                 apply_type=None, is_modifiable=False, is_collection=False):
        self.name = name
        self.description = description
        self.value = value
        self.default_value = default_value
        self.allowed_values = allowed_values
        self.data_type = data_type
        self.apply_type = apply_type
        self.is_modifiable = is_modifiable
        self.is_collection = is_collection

    def __repr__(self):
        return 'OptionSetting:%s' % self.name

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Name':
            self.name = value
        elif name == 'Description':
            self.description = value
        elif name == 'Value':
            self.value = value
        elif name == 'DefaultValue':
            self.default_value = value
        elif name == 'AllowedValues':
            self.allowed_values = value
        elif name == 'DataType':
            self.data_type = value
        elif name == 'ApplyType':
            self.apply_type = value
        elif name == 'IsModifiable':
            if value.lower() == 'true':
                self.is_modifiable = True
            else:
                self.is_modifiable = False
        elif name == 'IsCollection':
            if value.lower() == 'true':
                self.is_collection = True
            else:
                self.is_collection = False
        else:
            setattr(self, name, value)


class VpcSecurityGroup(object):
    """
    Describes a VPC security group for use in a OptionGroup
    """
    def __init__(self, vpc_id=None, status=None):
        self.vpc_id = vpc_id
        self.status = status

    def __repr__(self):
        return 'VpcSecurityGroup:%s' % self.vpc_id

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'VpcSecurityGroupId':
            self.vpc_id = value
        elif name == 'Status':
            self.status = value
        else:
            setattr(self, name, value)


class OptionGroupOption(object):
    """
    Describes a OptionGroupOption for use in an OptionGroup

    :ivar name: The name of the option
    :ivar description: The description of the option.
    :ivar engine_name: Engine name that this option can be applied to.
    :ivar major_engine_version: Indicates the major engine version that the
                                option is available for.
    :ivar min_minor_engine_version: The minimum required engine version for the
                                    option to be applied.
    :ivar permanent: Indicate if this option is permanent.
    :ivar persistent: Indicate if this option is persistent.
    :ivar port_required: Specifies whether the option requires a port.
    :ivar default_port: If the option requires a port, specifies the default
                        port for the option.
    :ivar settings: The option settings for this option.
    :ivar depends_on: List of all options that are prerequisites for this
                      option.
    """
    def __init__(self, name=None, description=None, engine_name=None,
                 major_engine_version=None, min_minor_engine_version=None,
                 permanent=False, persistent=False, port_required=False,
                 default_port=None, settings=None, depends_on=None):
        self.name = name
        self.description = description
        self.engine_name = engine_name
        self.major_engine_version = major_engine_version
        self.min_minor_engine_version = min_minor_engine_version
        self.permanent = permanent
        self.persistent = persistent
        self.port_required = port_required
        self.default_port = default_port
        self.settings = settings
        self.depends_on = depends_on

        if self.settings is None:
            self.settings = []

        if self.depends_on is None:
            self.depends_on = []

    def __repr__(self):
        return 'OptionGroupOption:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'OptionGroupOptionSettings':
            self.settings = ResultSet([
                ('OptionGroupOptionSettings', OptionGroupOptionSetting)
            ])
        elif name == 'OptionsDependedOn':
            self.depends_on = []
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Name':
            self.name = value
        elif name == 'Description':
            self.description = value
        elif name == 'EngineName':
            self.engine_name = value
        elif name == 'MajorEngineVersion':
            self.major_engine_version = value
        elif name == 'MinimumRequiredMinorEngineVersion':
            self.min_minor_engine_version = value
        elif name == 'Permanent':
            if value.lower() == 'true':
                self.permenant = True
            else:
                self.permenant = False
        elif name == 'Persistent':
            if value.lower() == 'true':
                self.persistent = True
            else:
                self.persistent = False
        elif name == 'PortRequired':
            if value.lower() == 'true':
                self.port_required = True
            else:
                self.port_required = False
        elif name == 'DefaultPort':
            self.default_port = int(value)
        else:
            setattr(self, name, value)


class OptionGroupOptionSetting(object):
    """
    Describes a OptionGroupOptionSetting for use in an OptionGroupOption.

    :ivar name: The name of the option that has settings that you can set.
    :ivar description: The description of the option setting.
    :ivar value: The current value of the option setting.
    :ivar default_value: The default value of the option setting.
    :ivar allowed_values: The allowed values of the option setting.
    :ivar data_type: The data type of the option setting.
    :ivar apply_type: The DB engine specific parameter type.
    :ivar is_modifiable: A Boolean value that, when true, indicates the option
                         setting can be modified from the default.
    :ivar is_collection: Indicates if the option setting is part of a
                         collection.
    """

    def __init__(self, name=None, description=None, default_value=False,
                 allowed_values=None, apply_type=None, is_modifiable=False):
        self.name = name
        self.description = description
        self.default_value = default_value
        self.allowed_values = allowed_values
        self.apply_type = apply_type
        self.is_modifiable = is_modifiable

    def __repr__(self):
        return 'OptionGroupOptionSetting:%s' % self.name

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'SettingName':
            self.name = value
        elif name == 'SettingDescription':
            self.description = value
        elif name == 'DefaultValue':
            self.default_value = value
        elif name == 'AllowedValues':
            self.allowed_values = value
        elif name == 'ApplyType':
            self.apply_type = value
        elif name == 'IsModifiable':
            if value.lower() == 'true':
                self.is_modifiable = True
            else:
                self.is_modifiable = False
        else:
            setattr(self, name, value)
