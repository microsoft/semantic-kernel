"""Tests for `semantic_kernel.settings`."""
import os
import typing as t
from pathlib import Path

import pytest
from dotenv import dotenv_values
from pydantic.env_settings import SettingsSourceCallable

from semantic_kernel.settings import KernelSettings, load_settings


def test_load_settings() -> None:
    """I should be able to load the settings in the test environment.

    If this test fails, a majority of the other tests will fail as well.
    """
    settings = load_settings()
    assert isinstance(settings, KernelSettings)
    assert settings.openai.api_key, "OpenAI API key not set."


@pytest.fixture()
def temp_dotenv_file(dotenv_overrides: t.Dict[str, str]) -> t.Iterator[None]:
    """Override dotenv file in current directory with a temporary one."""
    dotenv_path = Path.cwd() / ".env"
    original_contents = dotenv_path.read_text()
    new_contents = "\n".join(
        f"{key}={value}" for key, value in dotenv_overrides.items()
    )
    dotenv_path.write_text(new_contents)
    try:
        yield
    finally:  # I don't think we need a try/finally here, but I'm not sure.
        dotenv_path.write_text(original_contents)


@pytest.fixture()
def temp_os_environ(dotenv_overrides: t.Dict[str, str]) -> t.Iterator[None]:
    """Override os.environ with the dotenv overrides for the duration of this fixture."""
    original_environ = os.environ.copy()
    os.environ.update(dotenv_overrides)
    try:
        yield
    finally:
        os.environ = original_environ


@pytest.fixture()
def temp_empty_dotenv_file() -> t.Iterator[None]:
    """Override dotenv file in current directory with an empty one."""
    dotenv_path = Path.cwd() / ".env"
    original_contents = dotenv_path.read_text()
    dotenv_path.write_text("")
    try:
        yield
    finally:
        dotenv_path.write_text(original_contents)


@pytest.mark.parametrize(
    "dotenv_overrides",
    [
        {"OPENAI__API_KEY": "test", "OPENAI__ORG_ID": "test"},
    ],
)
@pytest.mark.usefixtures("temp_dotenv_file", "temp_os_environ")
def test_load_settings_using_dotenv_lib(dotenv_overrides: t.Dict[str, str]) -> None:
    """Check that the overrides are actually being respected."""
    assert dotenv_values() == dotenv_overrides


class TestKernelSettings(KernelSettings):
    """KernelSettings with different order of sources to give precedence to dotenv."""

    class Config:
        """Pydantic config to set the order of sources."""

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            """Customise the config sources.

            Reorder the config sources so that we only use the dotenv file. This way, if
            the dotenv file is not being used, we know that the settings are not being
            loaded correctly.
            """
            return (env_settings,)


@pytest.mark.parametrize(
    "dotenv_overrides",
    [
        {"OPENAI__API_KEY": "test", "OPENAI__ORG_ID": "test"},
    ],
)
@pytest.mark.usefixtures("temp_dotenv_file", "temp_os_environ")
def test_load_settings_from_dotenv_files(dotenv_overrides: t.Dict[str, str]) -> None:
    """I should be able to load the settings from a .env file."""
    settings = TestKernelSettings()  # type: ignore
    assert settings.openai.api_key == dotenv_overrides["OPENAI__API_KEY"]
    assert settings.openai.org_id == dotenv_overrides["OPENAI__ORG_ID"]


@pytest.mark.parametrize(
    "dotenv_overrides",
    [
        {"OPENAI__API_KEY": "test", "OPENAI__ORG_ID": "test"},
    ],
)
# NOTE: We're using the `temp_empty_dotenv_file` instead of `temp_dotenv_file` here
# This is because we want to test that the settings are being loaded from os.environ
# and not from the dotenv file. Therefore we need to make sure that the dotenv file
# is empty.
@pytest.mark.usefixtures("temp_empty_dotenv_file", "temp_os_environ")
def test_load_settings_from_os_environ(dotenv_overrides: t.Dict[str, str]) -> None:
    """I should be able to load the settings from env vars."""
    settings = TestKernelSettings()  # type: ignore
    assert (
        not dotenv_values()
    ), "dotenv file should be empty otherwise this test has no point."
    assert settings.openai.api_key == dotenv_overrides["OPENAI__API_KEY"]
    assert settings.openai.org_id == dotenv_overrides["OPENAI__ORG_ID"]
