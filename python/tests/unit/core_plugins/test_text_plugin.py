# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.text_plugin import TextPlugin


def test_can_be_instantiated():
    assert TextPlugin()


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< main
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< main
>>>>>>> main
>>>>>>> Stashed changes
def test_can_be_imported(kernel: Kernel):
    kernel.add_plugin(TextPlugin(), "text_plugin")
    assert not kernel.get_function(
        plugin_name="text_plugin", function_name="trim"
    ).is_prompt


def test_can_be_imported_with_name(kernel: Kernel):
    kernel.add_plugin(TextPlugin(), "text")
    assert not kernel.get_function(plugin_name="text", function_name="trim").is_prompt
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
def test_can_be_imported():
    kernel = sk.Kernel()
    assert kernel.import_plugin(TextPlugin(), "text_plugin")
    assert not kernel.plugins["text_plugin"]["trim"].is_prompt


def test_can_be_imported_with_name():
    kernel = sk.Kernel()
    assert kernel.import_plugin(TextPlugin(), "text")
    assert not kernel.plugins["text"]["trim"].is_prompt
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes


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
