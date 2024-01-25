# Copyright (c) Microsoft. All rights reserved.

from string import ascii_uppercase

import pytest

from semantic_kernel.plugin_definition.default_kernel_plugin import DefaultKernelPlugin
from semantic_kernel.plugin_definition.kernel_plugin_collection import KernelPluginCollection


def test_add_plugin():
    collection = KernelPluginCollection()
    plugin = DefaultKernelPlugin(name="TestPlugin")
    collection.add(plugin)
    assert len(collection) == 1
    assert collection.contains(plugin.name)


def test_remove_plugin():
    collection = KernelPluginCollection()
    plugin = DefaultKernelPlugin(name="TestPlugin")
    collection.add(plugin)
    collection.remove(plugin)
    assert len(collection) == 0


def test_remove_plugin_by_name():
    collection = KernelPluginCollection()
    expected_plugin_name = "TestPlugin"
    plugin = DefaultKernelPlugin(name=expected_plugin_name)
    collection.add(plugin)
    collection.remove_by_name(expected_plugin_name)
    assert len(collection) == 0


def test_add_range():
    num_plugins = 3
    collection = KernelPluginCollection()
    plugins = [DefaultKernelPlugin(name=f"Plugin_{ascii_uppercase[i]}") for i in range(num_plugins)]
    collection.add_range(plugins)
    assert len(collection) == num_plugins


def test_clear_collection():
    collection = KernelPluginCollection()
    plugins = [DefaultKernelPlugin(name=f"Plugin_{ascii_uppercase[i]}") for i in range(3)]
    collection.add_range(plugins)
    collection.clear()
    assert len(collection) == 0


def test_iterate_collection():
    collection = KernelPluginCollection()
    plugins = [DefaultKernelPlugin(name=f"Plugin_{ascii_uppercase[i]}") for i in range(3)]
    collection.add_range(plugins)

    for i, plugin in enumerate(collection.plugins.values()):
        assert plugin.name == f"Plugin_{ascii_uppercase[i]}"


def test_get_plugin():
    collection = KernelPluginCollection()
    plugin = DefaultKernelPlugin(name="TestPlugin")
    collection.add(plugin)
    retrieved_plugin = collection["TestPlugin"]
    assert retrieved_plugin == plugin


def test_get_plugin_not_found_raises_keyerror():
    collection = KernelPluginCollection()
    with pytest.raises(KeyError):
        _ = collection["NonExistentPlugin"]


def test_get_plugin_succeeds():
    collection = KernelPluginCollection()
    plugin = DefaultKernelPlugin(name="TestPlugin")
    collection.add(plugin)
    found_plugin = collection.get_plugin("TestPlugin")
    assert found_plugin == plugin
    assert collection.get_plugin("NonExistentPlugin") is None


def test_configure_plugins_on_object_creation():
    plugin = DefaultKernelPlugin(name="TestPlugin")
    collection = KernelPluginCollection(plugins=[plugin])
    assert len(collection) == 1
