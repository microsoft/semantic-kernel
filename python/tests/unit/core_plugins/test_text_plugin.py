import semantic_kernel as sk
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.plugin_definition.plugin_collection import PluginCollection


def test_can_be_instantiated():
    assert TextPlugin()


def test_can_be_imported():
    kernel = sk.Kernel()
    assert kernel.import_plugin(TextPlugin())
    assert kernel.plugins.has_native_function(PluginCollection.GLOBAL_PLUGIN, "trim")


def test_can_be_imported_with_name():
    kernel = sk.Kernel()
    assert kernel.import_plugin(TextPlugin(), "text")
    assert kernel.plugins.has_native_function("text", "trim")


def test_can_trim():
    text_plugin = TextPlugin()
    result = text_plugin.trim("  hello world  ")
    assert result == "hello world"


def test_can_trim_start():
    text_plugin = TextPlugin()
    result = text_plugin.trim_start("  hello world  ")
    assert result == "hello world  "


def test_can_trim_end():
    text_plugin = TextPlugin()
    result = text_plugin.trim_end("  hello world  ")
    assert result == "  hello world"


def test_can_lower():
    text_plugin = TextPlugin()
    result = text_plugin.lowercase("  HELLO WORLD  ")
    assert result == "  hello world  "


def test_can_upper():
    text_plugin = TextPlugin()
    result = text_plugin.uppercase("  hello world  ")
    assert result == "  HELLO WORLD  "
