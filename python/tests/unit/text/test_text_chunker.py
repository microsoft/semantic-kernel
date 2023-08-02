# Copyright (c) Microsoft. All rights reserved.
import os

from semantic_kernel.text import (
    split_markdown_lines,
    split_markdown_paragraph,
    split_plaintext_lines,
    split_plaintext_paragraph,
)

NEWLINE = os.linesep


def test_split_plain_text_lines_with_token_count():
    """Test split_plain_text_lines() with external token counter"""

    text = "This is a test of the emergency broadcast system. This is only a test."

    max_token_per_line = 8

    expected = [
        "This is a test of the",
        "emergency",
        "broadcast system.",
        "This is only a test.",
    ]
    split = split_plaintext_lines(
        text=text,
        max_token_per_line=max_token_per_line,
        token_counter=lambda x: len(x) // 3,
    )
    assert expected == split


def test_split_plain_text_lines_half():
    """Test split_plain_text_lines() with external token counter"""

    text_1 = "This is a test of. cutting. at the half point."
    text_2 = "This is a test of . cutting. at the half point."

    max_token_per_line = 10

    expected_1 = ["This is a test of. cutting.", "at the half point."]
    split_1 = split_plaintext_lines(text=text_1, max_token_per_line=max_token_per_line)
    assert expected_1 == split_1

    expected_2 = ["This is a test of .", "cutting. at the half point."]
    split_2 = split_plaintext_lines(text=text_2, max_token_per_line=max_token_per_line)
    assert expected_2 == split_2


def test_split_plain_text_lines():
    """Test split_plain_text_lines()"""

    text = "This is a test of the emergency broadcast system. This is only a test."

    max_token_per_line = 13

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

    max_token_per_line = 15

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

    max_token_per_line = 15

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
        "A small note. And another. And once again. Seriously, this is the end. "
        + "We're finished. All set. Bye.",
        "Done.",
    ]

    max_token_per_line = 15

    expected = [
        "This is a test of the emergency broadcast system.",
        "This is only a test.",
        "We repeat, this is only a test. A unit test.",
        "A small note. And another. And once again.",
        f"Seriously, this is the end. We're finished. All set. Bye.{NEWLINE}Done.",
    ]
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_text_paragraph_evenly_2():
    """Test split_paragraph() with evenly split input"""

    text = [
        "The gentle breeze rustled the autumn leaves on the tree branches. "
        + "She smiled and walked away.",
        "The sun set over the horizon peacefully, the beautiful star. Cats love boxes.",
        "That is something. Incredible news that is. "
        + "What a beautiful day to be alive. Seriously, this is the end. "
        + "We're finished once of for all. All set. Ok. ",
        "Done.",
        "Or is it?",
        "Surprise!",
    ]

    max_token_per_line = 17

    expected = [
        "The gentle breeze rustled the autumn leaves on the tree branches.",
        "She smiled and walked away.",
        "The sun set over the horizon peacefully, the beautiful star.",
        f"Cats love boxes.{NEWLINE}That is something. Incredible news that is.",
        f"What a beautiful day to be alive.{NEWLINE}Seriously, this is the end.",
        f"We're finished once of for all. All set. Ok.{NEWLINE}Done.{NEWLINE}"
        + f"Or is it?{NEWLINE}Surprise!",
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
        "A small note\nAnd another\r\nAnd once again\rSeriously this is the end\n"
        + "We're finished\nAll set\nBye\n",
        "Done",
    ]
    expected = [
        "This is a test of the emergency broadcast system",
        "This is only a test",
        "We repeat this is only a test\nA unit test",
        "A small note\nAnd another\nAnd once again",
        f"Seriously this is the end\nWe're finished\nAll set\nBye{NEWLINE}Done",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_punctuation():
    """
    a plaintext example that splits on ? or !
    """
    text = [
        "This is a test of the emergency broadcast system. This is only a test",
        "We repeat, this is only a test? A unit test",
        "A small note! And another? And once again! Seriously, this is the end. "
        + "We're finished. All set. Bye.",
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
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_semicolon():
    """
    a plaintext example that splits on ;
    """
    text = [
        "This is a test of the emergency broadcast system; This is only a test",
        "We repeat; this is only a test; A unit test",
        "A small note; And another; And once again; Seriously, this is the end;"
        + " We're finished; All set; Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system;",
        "This is only a test",
        "We repeat; this is only a test; A unit test",
        "A small note; And another; And once again;",
        f"Seriously, this is the end; We're finished; All set; Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_colon():
    """
    a plaintext example that splits on :
    """
    text = [
        "This is a test of the emergency broadcast system: This is only a test",
        "We repeat: this is only a test: A unit test",
        "A small note: And another: And once again: Seriously, this is the end: "
        + "We're finished: All set: Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system:",
        "This is only a test",
        "We repeat: this is only a test: A unit test",
        "A small note: And another: And once again:",
        f"Seriously, this is the end: We're finished: All set: Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_commas():
    """
    a plaintext example that splits on ,
    """
    text = [
        "This is a test of the emergency broadcast system, This is only a test",
        "We repeat, this is only a test, A unit test",
        "A small note, And another, And once again, Seriously this is the end, "
        + "We're finished, All set, Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system,",
        "This is only a test",
        "We repeat, this is only a test, A unit test",
        "A small note, And another, And once again,",
        f"Seriously this is the end, We're finished, All set, Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_closing_brackets():
    """
    a plaintext example that splits on closing brackets
    """
    text = [
        "This is a test of the emergency broadcast system) This is only a test",
        "We repeat) this is only a test) A unit test",
        "A small note] And another) And once again] Seriously this is the end} "
        + "We're finished} All set} Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system)",
        "This is only a test",
        "We repeat) this is only a test) A unit test",
        "A small note] And another) And once again]",
        "Seriously this is the end\u007d We're finished\u007d All set\u007d "
        + f"Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_spaces():
    """
    a plaintext example that splits on spaces
    """
    text = [
        "This is a test of the emergency broadcast system This is only a test",
        "We repeat this is only a test A unit test",
        "A small note And another And once again Seriously this is the end We're "
        + "finished All set Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency",
        "broadcast system This is only a test",
        "We repeat this is only a test A unit test",
        "A small note And another And once again Seriously",
        f"this is the end We're finished All set Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_hyphens():
    """
    a plaintext example that splits on hyphens
    """
    text = [
        "This is a test of the emergency broadcast system-This is only a test",
        "We repeat-this is only a test-A unit test",
        "A small note-And another-And once again-Seriously, this is the end-We're"
        + " finished-All set-Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency",
        "broadcast system-This is only a test",
        "We repeat-this is only a test-A unit test",
        "A small note-And another-And once again-Seriously,",
        f"this is the end-We're finished-All set-Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_paragraph_nodelimiters():
    """
    a plaintext example that splits on spaces
    """
    text = [
        "Thisisatestoftheemergencybroadcastsystem",
        "Thisisonlyatest",
        "WerepeatthisisonlyatestAunittest",
        "AsmallnoteAndanotherAndonceagain",
        "SeriouslythisistheendWe'refinishedAllsetByeDoneThisOneWillBeSplitToMeet"
        + "TheLimit",
    ]
    expected = [
        f"Thisisatestoftheemergencybroadcastsystem{NEWLINE}Thisisonlyatest",
        "WerepeatthisisonlyatestAunittest",
        "AsmallnoteAndanotherAndonceagain",
        "SeriouslythisistheendWe'refinishedAllse",
        "tByeDoneThisOneWillBeSplitToMeetTheLimit",
    ]
    max_token_per_line = 15
    split = split_plaintext_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_md_on_dot():
    """
    a markdown example that splits on .
    """
    text = [
        "This is a test of the emergency broadcast\n system.This\n is only a test",
        "We repeat. this is only a test. A unit test",
        "A small note. And another. And once again. Seriously, this is the end. "
        + "We're finished. All set. Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast\n system.",
        "This\n is only a test",
        "We repeat. this is only a test. A unit test",
        "A small note. And another. And once again.",
        f"Seriously, this is the end. We're finished. All set. Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_md_on_colon():
    """
    a markdown example that splits on :
    """
    text = [
        "This is a test of the emergency broadcast system: This is only a test",
        "We repeat: this is only a test: A unit test",
        "A small note: And another: And once again: Seriously, this is the end: "
        + "We're finished: All set: Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system:",
        "This is only a test",
        "We repeat: this is only a test: A unit test",
        "A small note: And another: And once again:",
        f"Seriously, this is the end: We're finished: All set: Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_md_on_punctuation():
    """
    a markdown example that splits on punctuation
    """
    text = [
        "This is a test of the emergency broadcast\n system?This\n is only a test",
        "We repeat? this is only a test! A unit test",
        "A small note? And another! And once again? Seriously, this is the end! "
        + "We're finished! All set! Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast\n system?",
        "This\n is only a test",
        "We repeat? this is only a test! A unit test",
        "A small note? And another! And once again?",
        f"Seriously, this is the end! We're finished! All set! Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_md_on_semicolon():
    """
    a markdown example that splits on semicolons
    """
    text = [
        "This is a test of the emergency broadcast system; This is only a test",
        "We repeat; this is only a test; A unit test",
        "A small note; And another; And once again; Seriously, this is the end; "
        + "We're finished; All set; Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system;",
        "This is only a test",
        "We repeat; this is only a test; A unit test",
        "A small note; And another; And once again;",
        f"Seriously, this is the end; We're finished; All set; Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(text, max_token_per_line)
    assert expected == split


def test_split_md_on_commas():
    """
    a markdown example that splits on commas
    """
    test = [
        "This is a test of the emergency broadcast system, This is only a test",
        "We repeat, this is only a test, A unit test",
        "A small note, And another, And once again, Seriously, this is the end, "
        + "We're finished, All set, Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system,",
        "This is only a test",
        "We repeat, this is only a test, A unit test",
        "A small note, And another, And once again, Seriously,",
        f"this is the end, We're finished, All set, Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(test, max_token_per_line)
    assert expected == split


def test_split_md_on_brackets():
    """
    a markdown example that splits on brackets
    """
    test = [
        "This is a test of the emergency broadcast system) This is only a test.",
        "We repeat [this is only a test] A unit test",
        "A small note (And another) And once (again) Seriously, this is the end "
        + "We're finished (All set) Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency broadcast system)",
        "This is only a test.",
        "We repeat [this is only a test] A unit test",
        "A small note (And another) And once (again) Seriously,",
        f"this is the end We're finished (All set) Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(test, max_token_per_line)
    assert expected == split


def test_split_md_on_spaces():
    """
    a markdown example that splits on spaces
    """
    test = [
        "This is a test of the emergency broadcast system This is only a test",
        "We repeat this is only a test A unit test",
        "A small note And another And once again Seriously this is the end We're "
        + "finished All set Bye.",
        "Done.",
    ]
    expected = [
        "This is a test of the emergency",
        "broadcast system This is only a test",
        "We repeat this is only a test A unit test",
        "A small note And another And once again Seriously",
        f"this is the end We're finished All set Bye.{NEWLINE}Done.",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(test, max_token_per_line)
    assert expected == split


def test_split_md_on_newlines():
    test = [
        "This_is_a_test_of_the_emergency_broadcast_system\r\nThis_is_only_a_test",
        "We_repeat_this_is_only_a_test\nA_unit_test",
        "A_small_note\nAnd_another\r\nAnd_once_again\rSeriously_this_is_the_end\n"
        + "We're_finished\nAll_set\nBye\n",
        "Done",
    ]
    expected = [
        "This_is_a_test_of_the_emergency_broadcast_system",
        "This_is_only_a_test",
        "We_repeat_this_is_only_a_test\nA_unit_test",
        "A_small_note\nAnd_another\nAnd_once_again",
        f"Seriously_this_is_the_end\nWe're_finished\nAll_set\nBye{NEWLINE}Done",
    ]
    max_token_per_line = 15
    split = split_markdown_paragraph(test, max_token_per_line)
    assert expected == split
