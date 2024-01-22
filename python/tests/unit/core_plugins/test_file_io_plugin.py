import os
import tempfile

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.file_io_plugin import FileIOPlugin
from semantic_kernel.orchestration.context_variables import ContextVariables


def test_can_be_instantiated():
    plugin = FileIOPlugin()
    assert plugin is not None


def test_can_be_imported():
    kernel = Kernel()
    assert kernel.import_plugin(FileIOPlugin(), "file")
    assert kernel.plugins.has_native_function("file", "readAsync")


@pytest.mark.asyncio
async def test_can_read_async():
    plugin = FileIOPlugin()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
            fp.write("Hello, world!")
            fp.flush()

            content = await plugin.read_async(fp.name)
            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_read_async():
    plugin = FileIOPlugin()
    filepath = None
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as fp:
        fp.write("Hello, world!")
        filepath = fp.name

    with pytest.raises(AssertionError):
        await plugin.read_async(filepath)


@pytest.mark.asyncio
async def test_can_write(context_factory):
    plugin = FileIOPlugin()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            context_variables = ContextVariables()

            context_variables.set("path", fp.name)
            context_variables.set("content", "Hello, world!")

            context = context_factory(context_variables)

            await plugin.write_async(context)

            content = fp.read()

            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_write(context_factory):
    plugin = FileIOPlugin()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            os.chmod(fp.name, 0o500)

            context_variables = ContextVariables()

            context_variables.set("path", fp.name)
            context_variables.set("content", "Hello, world!")

            context = context_factory(context_variables)

            with pytest.raises(PermissionError):
                await plugin.write_async(context)

            os.chmod(fp.name, 0o777)
    finally:
        if fp is not None:
            os.remove(fp.name)
