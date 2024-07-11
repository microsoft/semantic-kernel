import os
import tempfile

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_skills.file_io_skill import FileIOSkill
from semantic_kernel.orchestration.context_variables import ContextVariables


def test_can_be_instantiated():
    skill = FileIOSkill()
    assert skill is not None


def test_can_be_imported():
    kernel = Kernel()
    assert kernel.import_skill(FileIOSkill(), "file")
    assert kernel.skills.has_native_function("file", "readAsync")


@pytest.mark.asyncio
async def test_can_read_async():
    skill = FileIOSkill()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as fp:
            fp.write("Hello, world!")
            fp.flush()

            content = await skill.read_async(fp.name)
            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_read_async():
    skill = FileIOSkill()
    filepath = None
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as fp:
        fp.write("Hello, world!")
        filepath = fp.name

    with pytest.raises(AssertionError):
        await skill.read_async(filepath)


@pytest.mark.asyncio
async def test_can_write(context_factory):
    skill = FileIOSkill()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            context_variables = ContextVariables()

            context_variables.set("path", fp.name)
            context_variables.set("content", "Hello, world!")

            context = context_factory(context_variables)

            await skill.write_async(context)

            content = fp.read()

            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_write(context_factory):
    skill = FileIOSkill()
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            os.chmod(fp.name, 0o500)

            context_variables = ContextVariables()

            context_variables.set("path", fp.name)
            context_variables.set("content", "Hello, world!")

            context = context_factory(context_variables)

            with pytest.raises(PermissionError):
                await skill.write_async(context)

            os.chmod(fp.name, 0o777)
    finally:
        if fp is not None:
            os.remove(fp.name)
