# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.data.text_search import SearchFilter
from semantic_kernel.data.vector_search import VectorSearchFilter


def test_filter():
    empty_filter = SearchFilter()
    assert empty_filter.filters == []
    assert empty_filter.group_type == "AND"
    assert str(empty_filter) == ""


def test_filter_class_method():
    filter = SearchFilter.equal_to("field_name", "value")
    assert len(filter.filters) == 1
    assert str(filter) == "(filter_clause_type='equal_to' field_name='field_name' value='value')"


def test_filter_regular():
    filter = SearchFilter()
    filter.equal_to("field_name", "value")
    assert len(filter.filters) == 1
    assert str(filter) == "(filter_clause_type='equal_to' field_name='field_name' value='value')"


def test_multiple_filters():
    filter = SearchFilter.equal_to("field_name", "value").equal_to("field_name2", "value2")
    assert len(filter.filters) == 2
    assert (
        str(filter)
        == "(filter_clause_type='equal_to' field_name='field_name' value='value') AND (filter_clause_type='equal_to' field_name='field_name2' value='value2')"  # noqa: E501
    )


def test_text_search_filter():
    filter = SearchFilter.equal_to("field_name", "value")
    assert len(filter.filters) == 1
    assert str(filter) == "(filter_clause_type='equal_to' field_name='field_name' value='value')"


def test_vector_search_filter():
    filter = VectorSearchFilter.any_tag_equal_to("field_name", "value")
    assert len(filter.filters) == 1
    assert str(filter) == "(filter_clause_type='any_tags_equal_to' field_name='field_name' value='value')"

    filter2 = VectorSearchFilter()
    filter2.any_tag_equal_to("field_name", "value")
    assert len(filter2.filters) == 1
    assert str(filter2) == "(filter_clause_type='any_tags_equal_to' field_name='field_name' value='value')"
