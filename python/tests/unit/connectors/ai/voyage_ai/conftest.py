# Copyright (c) Microsoft. All rights reserved.


import pytest


@pytest.fixture(scope="session")
def voyage_ai_unit_test_env(monkeypatch_session):
    """Fixture to set VoyageAI environment variables for testing."""
    monkeypatch_session.setenv("VOYAGE_AI_API_KEY", "test-api-key")
    monkeypatch_session.setenv("VOYAGE_AI_EMBEDDING_MODEL_ID", "voyage-3-large")
    monkeypatch_session.setenv("VOYAGE_AI_CONTEXTUALIZED_EMBEDDING_MODEL_ID", "voyage-context-3")
    monkeypatch_session.setenv("VOYAGE_AI_RERANKER_MODEL_ID", "rerank-2.5")
    monkeypatch_session.setenv("VOYAGE_AI_MULTIMODAL_EMBEDDING_MODEL_ID", "voyage-multimodal-3")

    return {
        "VOYAGE_AI_API_KEY": "test-api-key",
        "VOYAGE_AI_EMBEDDING_MODEL_ID": "voyage-3-large",
        "VOYAGE_AI_CONTEXTUALIZED_EMBEDDING_MODEL_ID": "voyage-context-3",
        "VOYAGE_AI_RERANKER_MODEL_ID": "rerank-2.5",
        "VOYAGE_AI_MULTIMODAL_EMBEDDING_MODEL_ID": "voyage-multimodal-3",
    }


@pytest.fixture
def voyage_ai_service():
    """Fixture for mock VoyageAI service."""
    pytest.importorskip("voyageai", reason="voyageai package not installed")


@pytest.fixture(scope="session")
def monkeypatch_session():
    """Session-scoped monkeypatch fixture."""
    from _pytest.monkeypatch import MonkeyPatch

    m = MonkeyPatch()
    yield m
    m.undo()
