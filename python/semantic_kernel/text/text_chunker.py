# Copyright (c) Microsoft. All rights reserved.
"""
Split text in chunks, attempting to leave meaning intact.
For plain text, split looking at new lines first, then periods, and so on.
For markdown, split looking at punctuation first, and so on.
"""
import os
from typing import List

NEWLINE = os.linesep

TEXT_SPLIT_OPTIONS = [
    ["\n", "\r"],
    ["."],
    ["?", "!"],
    [";"],
    [":"],
    [","],
    [")", "]", "}"],
    [" "],
    ["-"],
    None,
]

MD_SPLIT_OPTIONS = [
    ["."],
    ["?", "!"],
    [";"],
    [":"],
    [","],
    [")", "]", "}"],
    [" "],
    ["-"],
    ["\n", "\r"],
    None,
]


def split_plaintext_lines(text: str, max_token_per_line: int) -> List[str]:
    """
    Split plain text into lines.
    it will split on new lines first, and then on punctuation.
    """
    return _split_text_lines(text, max_token_per_line, True)


def split_markdown_lines(text: str, max_token_per_line: int) -> List[str]:
    """
    Split markdown into lines.
    It will split on punctuation first, and then on space and new lines.
    """
    return _split_markdown_lines(text, max_token_per_line, True)


def split_plaintext_paragraph(text: List[str], max_tokens: int) -> List[str]:
    """
    Split plain text into paragraphs.
    """

    split_lines = []
    for line in text:
        split_lines.extend(_split_text_lines(line, max_tokens, True))

    return _split_text_paragraph(split_lines, max_tokens)


def split_markdown_paragraph(text: List[str], max_tokens: int) -> List[str]:
    """
    Split markdown into paragraphs.
    """
    split_lines = []
    for line in text:
        split_lines.extend(_split_markdown_lines(line, max_tokens, False))

    return _split_text_paragraph(split_lines, max_tokens)


def _split_text_paragraph(text: List[str], max_tokens: int) -> List[str]:
    """
    Split text into paragraphs.
    """
    if not text:
        return []

    paragraphs = []
    current_paragraph = []

    for line in text:
        num_tokens_line = _token_count(line)
        num_tokens_paragraph = _token_count("".join(current_paragraph))

        if (
            num_tokens_paragraph + num_tokens_line + 1 >= max_tokens
            and len(current_paragraph) > 0
        ):
            paragraphs.append("".join(current_paragraph).strip())
            current_paragraph = []

        current_paragraph.append(f"{line}{NEWLINE}")

    if len(current_paragraph) > 0:
        paragraphs.append("".join(current_paragraph).strip())
        current_paragraph = []

    # Distribute text more evenly in the last paragraphs
    # when the last paragraph is too short.

    if len(paragraphs) > 1:
        last_para = paragraphs[-1]
        sec_last_para = paragraphs[-2]

        if _token_count(last_para) < max_tokens / 4:
            last_para_tokens = last_para.split(" ")
            sec_last_para_tokens = sec_last_para.split(" ")
            last_para_token_count = len(last_para_tokens)
            sec_last_para_token_count = len(sec_last_para_tokens)

            if last_para_token_count + sec_last_para_token_count <= max_tokens:
                sec_last_para = " ".join(sec_last_para_tokens) + NEWLINE
                last_para = " ".join(last_para_tokens)
                new_sec_last_para = sec_last_para + last_para
                paragraphs[-2] = new_sec_last_para.strip()
                paragraphs.pop()

    return paragraphs


def _split_markdown_lines(text: str, max_token_per_line: int, trim: bool) -> List[str]:
    """
    Split markdown into lines.
    """

    lines = _split_str_lines(text, max_token_per_line, MD_SPLIT_OPTIONS, trim)
    return lines


def _split_text_lines(text: str, max_token_per_line: int, trim: bool) -> List[str]:
    """
    Split text into lines.
    """

    lines = _split_str_lines(text, max_token_per_line, TEXT_SPLIT_OPTIONS, trim)

    return lines


def _split_str_lines(
    text: str, max_tokens: int, separators: List[List[str]], trim: bool
) -> List[str]:
    if not text:
        return []

    text = text.replace("\r\n", "\n")
    lines = []
    was_split = False
    for split_option in separators:
        if not lines:
            lines, was_split = _split_str(text, max_tokens, split_option, trim)
        else:
            lines, was_split = _split_list(lines, max_tokens, split_option, trim)
        if not was_split:
            break

    return lines


def _split_str(
    text: str, max_tokens: int, separators: List[str], trim: bool
) -> List[str]:
    """
    Split text into lines.
    """
    if not text:
        return []

    input_was_split = False
    text = text.strip() if trim else text

    text_as_is = [text]

    if _token_count(text) <= max_tokens:
        return text_as_is, input_was_split

    input_was_split = True

    half = int(len(text) / 2)

    cutpoint = -1

    if not separators:
        cutpoint = half

    elif set(separators) & set(text) and len(text) > 2:
        for index, text_char in enumerate(text):
            if text_char not in separators:
                continue

            if abs(half - index) < abs(half - cutpoint):
                cutpoint = index + 1

    else:
        return text_as_is, input_was_split

    if 0 < cutpoint < len(text):
        lines = []
        first_split, has_split1 = _split_str(
            text[:cutpoint], max_tokens, separators, trim
        )
        second_split, has_split2 = _split_str(
            text[cutpoint:], max_tokens, separators, trim
        )

        lines.extend(first_split)
        lines.extend(second_split)

        input_was_split = has_split1 or has_split2
    else:
        return text_as_is, input_was_split

    return lines, input_was_split


def _split_list(
    text: List[str], max_tokens: int, separators: List[str], trim: bool
) -> List[str]:
    """
    Split list of string into lines.
    """
    if not text:
        return []

    lines = []
    input_was_split = False
    for line in text:
        split_str, was_split = _split_str(line, max_tokens, separators, trim)
        lines.extend(split_str)
        input_was_split = input_was_split or was_split

    return lines, input_was_split


def _token_count(text: str) -> int:
    """
    Count the number of tokens in a string.

    TODO: chunking methods should be configurable to allow for different
          tokenization strategies depending on the model to be called.
          For now, we use an extremely rough estimate.
    """
    return int(len(text) / 4)
