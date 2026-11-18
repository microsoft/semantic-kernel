# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.streaming_text_content import StreamingTextContent


def test_stc_add_combines_metadata():
    chunk1 = StreamingTextContent(choice_index=0, text="Hello, ", metadata={"id": "cmpl-1"})
    chunk2 = StreamingTextContent(choice_index=0, text="world!", metadata={"usage": {"prompt_tokens": 5}})

    combined = chunk1 + chunk2

    assert combined.text == "Hello, world!"
    assert combined.metadata == {"id": "cmpl-1", "usage": {"prompt_tokens": 5}}

    # Make sure the original metadata is preserved
    assert chunk1.metadata == {"id": "cmpl-1"}
    assert chunk2.metadata == {"usage": {"prompt_tokens": 5}}


def test_stc_add_metadata_conflicting_keys_other_wins():
    chunk1 = StreamingTextContent(choice_index=0, text="Hello, ", metadata={"id": "cmpl-1", "logprobs": None})
    chunk2 = StreamingTextContent(choice_index=0, text="world!", metadata={"logprobs": {"tokens": ["world!"]}})

    combined = chunk1 + chunk2

    assert combined.metadata == {"id": "cmpl-1", "logprobs": {"tokens": ["world!"]}}
