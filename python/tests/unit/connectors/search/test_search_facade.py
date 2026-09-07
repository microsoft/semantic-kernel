# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors import brave, google_search, keenable, search


def test_facade_imports_keenable_search():
    """Test that the lazy facade resolves KeenableSearch to the real module."""
    from semantic_kernel.connectors.search import KeenableSearch, KeenableSettings

    assert KeenableSearch is keenable.KeenableSearch
    assert KeenableSettings is keenable.KeenableSettings


def test_facade_imports_brave_and_google_search():
    """Test that the lazy facade resolves the Brave and Google connectors too."""
    from semantic_kernel.connectors.search import BraveSearch, GoogleSearch

    assert BraveSearch is brave.BraveSearch
    assert GoogleSearch is google_search.GoogleSearch


def test_facade_dir_lists_exports():
    """Test that dir() on the facade lists the exported names."""
    names = dir(search)
    assert "KeenableSearch" in names
    assert "BraveSearch" in names
    assert "GoogleSearch" in names


def test_facade_unknown_attribute_raises():
    """Test that an unknown name raises AttributeError, not an import error."""
    with pytest.raises(AttributeError):
        search.NotAConnector  # noqa: B018
