from tests.compat import mock, unittest

from boto.ec2.snapshot import Snapshot
from boto.ec2.tag import Tag, TagSet
from boto.ec2.volume import Volume, AttachmentSet, VolumeAttribute


class VolumeTests(unittest.TestCase):
    def setUp(self):
        self.attach_data = AttachmentSet()
        self.attach_data.id = 1
        self.attach_data.instance_id = 2
        self.attach_data.status = "some status"
        self.attach_data.attach_time = 5
        self.attach_data.device = "/dev/null"

        self.volume_one = Volume()
        self.volume_one.id = 1
        self.volume_one.create_time = 5
        self.volume_one.status = "one_status"
        self.volume_one.size = "one_size"
        self.volume_one.snapshot_id = 1
        self.volume_one.attach_data = self.attach_data
        self.volume_one.zone = "one_zone"

        self.volume_two = Volume()
        self.volume_two.connection = mock.Mock()
        self.volume_two.id = 1
        self.volume_two.create_time = 6
        self.volume_two.status = "two_status"
        self.volume_two.size = "two_size"
        self.volume_two.snapshot_id = 2
        self.volume_two.attach_data = None
        self.volume_two.zone = "two_zone"

    @mock.patch("boto.ec2.volume.TaggedEC2Object.startElement")
    def test_startElement_calls_TaggedEC2Object_startElement_with_correct_args(self, startElement):
        volume = Volume()
        volume.startElement("some name", "some attrs", None)
        startElement.assert_called_with(
            "some name",
            "some attrs",
            None
        )

    @mock.patch("boto.ec2.volume.TaggedEC2Object.startElement")
    def test_startElement_retval_not_None_returns_correct_thing(self, startElement):
        tag_set = mock.Mock(TagSet)
        startElement.return_value = tag_set
        volume = Volume()
        retval = volume.startElement(None, None, None)
        self.assertEqual(retval, tag_set)

    @mock.patch("boto.ec2.volume.TaggedEC2Object.startElement")
    @mock.patch("boto.resultset.ResultSet")
    def test_startElement_with_name_tagSet_calls_ResultSet(self, ResultSet, startElement):
        startElement.return_value = None
        result_set = mock.Mock(ResultSet([("item", Tag)]))
        volume = Volume()
        volume.tags = result_set
        retval = volume.startElement("tagSet", None, None)
        self.assertEqual(retval, volume.tags)

    @mock.patch("boto.ec2.volume.TaggedEC2Object.startElement")
    def test_startElement_with_name_attachmentSet_returns_AttachmentSet(self, startElement):
        startElement.return_value = None
        attach_data = AttachmentSet()
        volume = Volume()
        volume.attach_data = attach_data
        retval = volume.startElement("attachmentSet", None, None)
        self.assertEqual(retval, volume.attach_data)

    @mock.patch("boto.ec2.volume.TaggedEC2Object.startElement")
    def test_startElement_else_returns_None(self, startElement):
        startElement.return_value = None
        volume = Volume()
        retval = volume.startElement("not tagSet or attachmentSet", None, None)
        self.assertEqual(retval, None)

    def check_that_attribute_has_been_set(self, name, value, attribute, obj_value=None):
        volume = Volume()
        volume.endElement(name, value, None)
        expected_value = obj_value if obj_value is not None else value
        self.assertEqual(getattr(volume, attribute), expected_value)

    def test_endElement_sets_correct_attributes_with_values(self):
        for arguments in [("volumeId", "some value", "id"),
                          ("createTime", "some time", "create_time"),
                          ("status", "some status", "status"),
                          ("size", 5, "size"),
                          ("snapshotId", 1, "snapshot_id"),
                          ("availabilityZone", "some zone", "zone"),
                          ("someName", "some value", "someName"),
                          ("encrypted", "true", "encrypted", True)]:
            self.check_that_attribute_has_been_set(*arguments)

    def test_endElement_with_name_status_and_empty_string_value_doesnt_set_status(self):
        volume = Volume()
        volume.endElement("status", "", None)
        self.assertNotEqual(volume.status, "")

    def test_update_with_result_set_greater_than_0_updates_dict(self):
        self.volume_two.connection.get_all_volumes.return_value = [self.volume_one]
        self.volume_two.update()

        assert all([self.volume_two.create_time == 5,
                    self.volume_two.status == "one_status",
                    self.volume_two.size == "one_size",
                    self.volume_two.snapshot_id == 1,
                    self.volume_two.attach_data == self.attach_data,
                    self.volume_two.zone == "one_zone"])

    def test_update_with_validate_true_raises_value_error(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.connection.get_all_volumes.return_value = []
        with self.assertRaisesRegexp(ValueError, "^1 is not a valid Volume ID$"):
            self.volume_one.update(True)

    def test_update_returns_status(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.connection.get_all_volumes.return_value = [self.volume_two]
        retval = self.volume_one.update()
        self.assertEqual(retval, "two_status")

    def test_delete_calls_delete_volume(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.delete()
        self.volume_one.connection.delete_volume.assert_called_with(
            1,
            dry_run=False
        )

    def test_attach_calls_attach_volume(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.attach("instance_id", "/dev/null")
        self.volume_one.connection.attach_volume.assert_called_with(
            1,
            "instance_id",
            "/dev/null",
            dry_run=False
        )

    def test_detach_calls_detach_volume(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.detach()
        self.volume_one.connection.detach_volume.assert_called_with(
            1, 2, "/dev/null", False, dry_run=False)

    def test_detach_with_no_attach_data(self):
        self.volume_two.connection = mock.Mock()
        self.volume_two.detach()
        self.volume_two.connection.detach_volume.assert_called_with(
            1, None, None, False, dry_run=False)

    def test_detach_with_force_calls_detach_volume_with_force(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.detach(True)
        self.volume_one.connection.detach_volume.assert_called_with(
            1, 2, "/dev/null", True, dry_run=False)

    def test_create_snapshot_calls_connection_create_snapshot(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.create_snapshot()
        self.volume_one.connection.create_snapshot.assert_called_with(
            1,
            None,
            dry_run=False
        )

    def test_create_snapshot_with_description(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.create_snapshot("some description")
        self.volume_one.connection.create_snapshot.assert_called_with(
            1,
            "some description",
            dry_run=False
        )

    def test_volume_state_returns_status(self):
        retval = self.volume_one.volume_state()
        self.assertEqual(retval, "one_status")

    def test_attachment_state_returns_state(self):
        retval = self.volume_one.attachment_state()
        self.assertEqual(retval, "some status")

    def test_attachment_state_no_attach_data_returns_None(self):
        retval = self.volume_two.attachment_state()
        self.assertEqual(retval, None)

    def test_snapshots_returns_snapshots(self):
        snapshot_one = Snapshot()
        snapshot_one.volume_id = 1
        snapshot_two = Snapshot()
        snapshot_two.volume_id = 2

        self.volume_one.connection = mock.Mock()
        self.volume_one.connection.get_all_snapshots.return_value = [snapshot_one, snapshot_two]
        retval = self.volume_one.snapshots()
        self.assertEqual(retval, [snapshot_one])

    def test_snapshots__with_owner_and_restorable_by(self):
        self.volume_one.connection = mock.Mock()
        self.volume_one.connection.get_all_snapshots.return_value = []
        self.volume_one.snapshots("owner", "restorable_by")
        self.volume_one.connection.get_all_snapshots.assert_called_with(
            owner="owner", restorable_by="restorable_by", dry_run=False)


class AttachmentSetTests(unittest.TestCase):
    def check_that_attribute_has_been_set(self, name, value, attribute):
        attachment_set = AttachmentSet()
        attachment_set.endElement(name, value, None)
        self.assertEqual(getattr(attachment_set, attribute), value)

    def test_endElement_with_name_volumeId_sets_id(self):
        return self.check_that_attribute_has_been_set("volumeId", "some value", "id")

    def test_endElement_with_name_instanceId_sets_instance_id(self):
        return self.check_that_attribute_has_been_set("instanceId", 1, "instance_id")

    def test_endElement_with_name_status_sets_status(self):
        return self.check_that_attribute_has_been_set("status", "some value", "status")

    def test_endElement_with_name_attachTime_sets_attach_time(self):
        return self.check_that_attribute_has_been_set("attachTime", 5, "attach_time")

    def test_endElement_with_name_device_sets_device(self):
        return self.check_that_attribute_has_been_set("device", "/dev/null", "device")

    def test_endElement_with_other_name_sets_other_name_attribute(self):
        return self.check_that_attribute_has_been_set("someName", "some value", "someName")


class VolumeAttributeTests(unittest.TestCase):
    def setUp(self):
        self.volume_attribute = VolumeAttribute()
        self.volume_attribute._key_name = "key_name"
        self.volume_attribute.attrs = {"key_name": False}

    def test_startElement_with_name_autoEnableIO_sets_key_name(self):
        self.volume_attribute.startElement("autoEnableIO", None, None)
        self.assertEqual(self.volume_attribute._key_name, "autoEnableIO")

    def test_startElement_without_name_autoEnableIO_returns_None(self):
        retval = self.volume_attribute.startElement("some name", None, None)
        self.assertEqual(retval, None)

    def test_endElement_with_name_value_and_value_true_sets_attrs_key_name_True(self):
        self.volume_attribute.endElement("value", "true", None)
        self.assertEqual(self.volume_attribute.attrs['key_name'], True)

    def test_endElement_with_name_value_and_value_false_sets_attrs_key_name_False(self):
        self.volume_attribute._key_name = "other_key_name"
        self.volume_attribute.endElement("value", "false", None)
        self.assertEqual(self.volume_attribute.attrs['other_key_name'], False)

    def test_endElement_with_name_volumeId_sets_id(self):
        self.volume_attribute.endElement("volumeId", "some_value", None)
        self.assertEqual(self.volume_attribute.id, "some_value")

    def test_endElement_with_other_name_sets_other_name_attribute(self):
        self.volume_attribute.endElement("someName", "some value", None)
        self.assertEqual(self.volume_attribute.someName, "some value")


if __name__ == "__main__":
    unittest.main()
