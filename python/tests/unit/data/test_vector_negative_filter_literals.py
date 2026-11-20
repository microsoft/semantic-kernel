# Copyright (c) Microsoft. All rights reserved.

"""Regression: negative numeric literals in vector-store filter lambdas (#14571)."""

from ast import Constant, UnaryOp, dump, parse
from unittest.mock import MagicMock

import pytest
from chromadb.api import ClientAPI
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Range

from semantic_kernel.connectors.chroma import ChromaCollection
from semantic_kernel.connectors.qdrant import QdrantCollection
from semantic_kernel.data.vector import (
    VectorStoreCollectionDefinition,
    VectorStoreField,
    _FoldUnaryNumericConstants,
)


@pytest.fixture
def numeric_definition() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="str"),
            VectorStoreField("data", name="price", type="float"),
            VectorStoreField("vector", name="vector", dimensions=2, type="float"),
        ]
    )


@pytest.mark.parametrize("literal,expected", [("-5", -5), ("-5.5", -5.5)])
def test_fold_unary_numeric_constants_negates_literal(literal, expected):
    tree = parse(f"lambda x: x.price > {literal}")
    folded = _FoldUnaryNumericConstants().visit(tree)
    # Body of the lambda should now compare against Constant(-5), not UnaryOp(USub, ...).
    compare = folded.body[0].value.body
    right = compare.comparators[0]
    assert isinstance(right, Constant)
    assert right.value == expected
    assert not isinstance(right, UnaryOp)


@pytest.mark.parametrize("expression", ["-True", "-False", "+True", "+False", "+5", "+5.5", "~5", "-x.price"])
def test_fold_unary_numeric_constants_preserves_other_unary_expressions(expression):
    tree = parse(f"lambda x: x.price > {expression}")
    original = dump(tree)
    folded = _FoldUnaryNumericConstants().visit(tree)
    assert dump(folded) == original


@pytest.mark.parametrize("literal,expected", [("-5", -5), ("-5.5", -5.5)])
def test_chroma_build_filter_accepts_negative_literal(numeric_definition, literal, expected):
    collection = ChromaCollection(
        collection_name="temps",
        record_type=dict,
        definition=numeric_definition,
        client=MagicMock(spec=ClientAPI),
    )
    parsed = collection._build_filter(f"lambda x: x.price > {literal}")
    assert parsed == {"price": {"$gt": expected}}


@pytest.mark.parametrize("expression", ["-True", "-False", "+True", "+False", "+5", "+5.5", "~5", "-x.price"])
def test_chroma_build_filter_rejects_other_unary_expressions(numeric_definition, expression):
    collection = ChromaCollection(
        collection_name="temps",
        record_type=dict,
        definition=numeric_definition,
        client=MagicMock(spec=ClientAPI),
    )
    with pytest.raises(NotImplementedError, match="Unary"):
        collection._build_filter(f"lambda x: x.price > {expression}")


@pytest.mark.parametrize("literal,expected", [("-5", -5), ("-5.5", -5.5)])
def test_qdrant_build_filter_accepts_negative_literal(numeric_definition, literal, expected):
    collection = QdrantCollection(
        record_type=dict,
        collection_name="temps",
        definition=numeric_definition,
        client=MagicMock(spec=AsyncQdrantClient),
    )
    parsed = collection._build_filter(f"lambda x: x.price > {literal}")
    assert parsed == FieldCondition(key="price", range=Range(gt=expected))
