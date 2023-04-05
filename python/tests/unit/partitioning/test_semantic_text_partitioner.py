# Copyright (c) Microsoft. All rights reserved.
import os

NEWLINE = os.linesep

from semantic_kernel.semantic_functions.partitioning import (
    split_plaintext_lines,
    split_markdown_paragraph,
    split_plaintext_paragraph,
)
from semantic_kernel.semantic_functions.partitioning import split_markdown_lines


def test_split_plain_text_lines():
    """Test split_plain_text_lines()"""

    text = "This is a test of the emergency broadcast system. This is only a test."

    max_token_per_line = 10

    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test.",
    ]
    split = split_plaintext_lines(text, max_token_per_line)
    assert expected == split


def test_split_markdown_paragraph():
    """Test split_markdown_paragraph()"""

    text = [
        "This is a test of the emergency broadcast system. This is only a test.",
        "We repeat, this is only a test. A unit test.",
    ]

    max_token_per_line = 11

    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test.",
        "We repeat, this is only a test. A unit test.",
    ]

    split = split_markdown_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_text_paragraph():
    """Test _split_text_paragraph()"""

    text = [
        "This is a test of the emergency broadcast system. This is only a test.",
        "We repeat, this is only a test. A unit test.",
    ]

    max_token_per_line = 13

    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test.",
        "We repeat, this is only a test. A unit test.",
    ]
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_markdown_lines():
    """Test split_markdown_lines()"""

    text = "This is a test of the emergency broadcast system. This is only a test."

    max_token_per_line = 11

    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test.",
    ]
    split = split_markdown_lines(text, max_token_per_line)
    assert expected == split


def test_split_text_paragraph_empty_input():
    """Test split_paragraph() with empty input"""

    text = []
    max_token_per_line = 13

    expected = []
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_markdown_paragraph_empty_input():
    """Test split_paragraph() with empty input"""

    text = []
    max_token_per_line = 10

    expected = []
    split = split_markdown_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_text_paragraph_evenly():
    """Test split_paragraph() with evenly split input"""

    text = [
        "This is a test of the emergency broadcast system. This is only a test.",
        "We repeat, this is only a test. A unit test.",
        "A small note. And another. And once again. Seriously, this is the end. We're finished. All set. Bye.",
        "Done.",
    ]

    max_token_per_line = 11

    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test.",
        "We repeat, this is only a test. A unit test.",
        "A small note. And another. And once again.",
        "Seriously, this is the end. We're finished. All set. Bye. Done.",
    ]
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_text_paragraph_evenly_2():
    """Test split_paragraph() with evenly split input"""

    text = [
        "The gentle breeze rustled the autumn leaves on the tree branches. She smiled and walked away.",
        "The sun set over the horizon peacefully, the beautiful star. Cats love boxes",
        "That is something. Incredible news that is. What a beautiful day to be alive. Seriously, this is the end. We're finished once of for all. All set. Ok.",
        "Done.",
        "Or is it?",
        "Surprise!",
    ]

    max_token_per_line = 15

    expected = [
        "The gentle breeze rustled the autumn leaves on the tree branches.",
        "She smiled and walked away.",
        "The sun set over the horizon peacefully, the beautiful star. Cats love boxes",
        "That is something. Incredible news that is. What a beautiful day to be alive.",
        "Seriously, this is the end. We're finished once of for all. All set. Ok.",
        f"Done.{NEWLINE}Or is it?{NEWLINE}Surprise!",
    ]
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_newline():
    """
    a plaintext example that splits on \r or \n
    """
    text = [
        "This is a test of the emergency broadcast system\r\nThis is only a test",
        "We repeat this is only a test\nA unit test",
        "A small note\nAnd another\r\nAnd once again\rSeriously this is the end\nWe're finished\nAll set\nBye\n",
        "Done",
    ]
    expected = [
        "This is a test of the emergency broadcast system",
        "This is only a test",
        "We repeat this is only a test\nA unit test",
        "A small note\nAnd another\nAnd once again",
        "Seriously this is the end\nWe're finished\nAll set\nBye Done",
    ]
    max_token_per_line = 11
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_punctuation():
    """
    a plaintext example that splits on ? or !
    """
    text = [
        "This is a test of the emergency broadcast system. This is only a test",
        "We repeat, this is only a test? A unit test",
        "A small note! And another? And once again! Seriously, this is the end. We're finished. All set. Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test",
        "We repeat, this is only a test? A unit test",
        "A small note! And another? And once again!",
        "Seriously, this is the end.",
        f"We're finished. All set. Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 12
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_punctuation_2():
    """
    a plaintext example that splits on ? or !
    """
    text = [
        "The gentle breeze rustled the autumn leaves on the tree branches. She smiled and walked away.",
        "The sun set over the horizon peacefully. Cats love boxes",
        "Are you sure? Incredible news! What a beautiful day! Seriously, this is the end. We're finished. All set. Ok.",
        "Done.",
    ]
    expected = [
        "The gentle breeze rustled the autumn leaves on the tree branches.",
        "She smiled and walked away.",
        "The sun set over the horizon peacefully. Cats love boxes",
        "Are you sure? Incredible news!",
        "What a beautiful day! Seriously, this is the end.",
        f"We're finished. All set. Ok.{NEWLINE}Done.",
    ]
    max_token_per_line = 11
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split
