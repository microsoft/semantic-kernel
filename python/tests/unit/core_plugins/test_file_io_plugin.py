import os
import tempfile

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.file_io_plugin import FileIOPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_can_be_instantiated():
    plugin = FileIOPlugin()
    assert plugin is not None


def test_can_be_imported():
    kernel = Kernel()
    assert kernel.import_plugin(FileIOPlugin(), "file")
    assert kernel.plugins["file"] is not None
    assert kernel.plugins["file"].name == "file"
    assert kernel.plugins["file"]["readAsync"] is not None


@pytest.mark.asyncio
async def test_can_read():
    plugin = FileIOPlugin()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
            fp.write("Hello, world!")
            fp.flush()

            content = await plugin.read(fp.name)
            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_read():
    plugin = FileIOPlugin()
    filepath = None
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as fp:
        fp.write("Hello, world!")
        filepath = fp.name

    with pytest.raises(AssertionError):
        await plugin.read(filepath)


@pytest.mark.asyncio
async def test_can_write():
    plugin = FileIOPlugin()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            arguments = KernelArguments(path=fp.name, content="Hello, world!")

            await plugin.write(**arguments)

            content = fp.read()

            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_write():
    plugin = FileIOPlugin()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            os.chmod(fp.name, 0o500)

            arguments = KernelArguments(path=fp.name, content="Hello, world!")

            with pytest.raises(PermissionError):
                await plugin.write(**arguments)

            os.chmod(fp.name, 0o777)
    finally:
        if fp is not None:
            os.remove(fp.name)
