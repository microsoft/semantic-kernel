# Copyright (c) Microsoft. All rights reserved.

from string import ascii_uppercase

import pytest

from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection


def test_add_plugin():
    collection = KernelPluginCollection()
@pytest.fixture(scope="function")
def collection():
    return KernelPluginCollection()


def test_add_plugin(collection: KernelPluginCollection):
    plugin = KernelPlugin(name="TestPlugin")
    collection.add(plugin)
    assert len(collection) == 1
    assert plugin.name in collection


def test_add_plugin_with_description():
    expected_description = "Test Description"
    collection = KernelPluginCollection()
def test_add_plugin_with_description(collection: KernelPluginCollection):
    expected_description = "Test Description"
    plugin = KernelPlugin(name="TestPlugin", description=expected_description)
    collection.add(plugin)
    assert len(collection) == 1
    assert plugin.name in collection
    assert collection[plugin.name].description == expected_description


def test_remove_plugin():
    collection = KernelPluginCollection()
def test_remove_plugin(collection: KernelPluginCollection):
    plugin = KernelPlugin(name="TestPlugin")
    collection.add(plugin)
    collection.remove(plugin)
    assert len(collection) == 0


def test_remove_plugin_by_name():
    collection = KernelPluginCollection()
def test_remove_plugin_by_name(collection: KernelPluginCollection):
    expected_plugin_name = "TestPlugin"
    plugin = KernelPlugin(name=expected_plugin_name)
    collection.add(plugin)
    collection.remove_by_name(expected_plugin_name)
    assert len(collection) == 0


def test_add_list_of_plugins():
    num_plugins = 3
    collection = KernelPluginCollection()
def test_add_list_of_plugins(collection: KernelPluginCollection):
    num_plugins = 3
    plugins = [KernelPlugin(name=f"Plugin_{ascii_uppercase[i]}") for i in range(num_plugins)]
    collection.add_list_of_plugins(plugins)
    assert len(collection) == num_plugins


def test_clear_collection():
    collection = KernelPluginCollection()
def test_clear_collection(collection: KernelPluginCollection):
    plugins = [KernelPlugin(name=f"Plugin_{ascii_uppercase[i]}") for i in range(3)]
    collection.add_list_of_plugins(plugins)
    collection.clear()
    assert len(collection) == 0


def test_iterate_collection():
    collection = KernelPluginCollection()
def test_iterate_collection(collection: KernelPluginCollection):
    plugins = [KernelPlugin(name=f"Plugin_{ascii_uppercase[i]}") for i in range(3)]
    collection.add_list_of_plugins(plugins)

    for i, plugin in enumerate(collection.plugins.values()):
        assert plugin.name == f"Plugin_{ascii_uppercase[i]}"


def test_get_plugin():
    collection = KernelPluginCollection()
def test_get_plugin(collection: KernelPluginCollection):
    plugin = KernelPlugin(name="TestPlugin")
    collection.add(plugin)
    retrieved_plugin = collection["TestPlugin"]
    assert retrieved_plugin == plugin


def test_get_plugin_not_found_raises_keyerror():
    collection = KernelPluginCollection()
def test_get_plugin_not_found_raises_keyerror(collection: KernelPluginCollection):
    with pytest.raises(KeyError):
        _ = collection["NonExistentPlugin"]


def test_get_plugin_succeeds():
    collection = KernelPluginCollection()
def test_get_plugin_succeeds(collection: KernelPluginCollection):
    plugin = KernelPlugin(name="TestPlugin")
    collection.add(plugin)
    found_plugin = collection["TestPlugin"]
    assert found_plugin == plugin
    with pytest.raises(KeyError):
        collection["NonExistentPlugin"] is None


def test_configure_plugins_on_object_creation():
    plugin = KernelPlugin(name="TestPlugin")
    collection = KernelPluginCollection(plugins=[plugin])
    assert len(collection) == 1


def test_overwrite_plugin_with_same_name_succeeds():
    plugin = KernelPlugin(name="TestPluginOne")
    collection = KernelPluginCollection(plugins=[plugin])

    plugin2 = KernelPlugin(name="TestPluginOne")
    collection.add(plugin2)

    assert len(collection) == 1
