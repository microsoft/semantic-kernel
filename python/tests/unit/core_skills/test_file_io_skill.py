import os
import tempfile

import pytest

import semantic_kernel as sk
from semantic_kernel.core_skills.file_io_skill import FileIOSkill
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext


def test_can_be_instantiated():
    skill = FileIOSkill()
    assert skill is not None


def test_can_be_imported():
    kernel = sk.create_kernel()
    assert kernel.import_skill(FileIOSkill(), "file")
    assert kernel.skills.has_native_function("file", "readAsync")


@pytest.mark.asyncio
async def test_can_read_async():
    skill = FileIOSkill()

    # Note: On Windows, we must use delete=False, or the skill cannot open the file
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
async def test_can_write():
    skill = FileIOSkill()

    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            context_variables = ContextVariables()

            context_variables.set("path", fp.name)
            context_variables.set("content", "Hello, world!")

            context = SKContext(context_variables, None, None, None)

            await skill.write_async(context)

            content = fp.read()

            assert content == "Hello, world!"
    finally:
        if fp is not None:
            os.remove(fp.name)


@pytest.mark.asyncio
async def test_cannot_write():
    fp = None
    try:
        with tempfile.NamedTemporaryFile(mode="r", delete=False) as fp:
            skill = FileIOSkill()
            os.chmod(fp.name, 0o500)

            context_variables = ContextVariables()

            context_variables.set("path", fp.name)
            context_variables.set("content", "Hello, world!")

            context = SKContext(context_variables, None, None, None)

            with pytest.raises(PermissionError):
                await skill.write_async(context)

            os.chmod(fp.name, 0o777)
    finally:
        if fp is not None:
            os.remove(fp.name)
