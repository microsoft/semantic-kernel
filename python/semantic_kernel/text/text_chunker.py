# Copyright (c) Microsoft. All rights reserved.
"""
Split text in chunks, attempting to leave meaning intact.
For plain text, split looking at new lines first, then periods, and so on.
For markdown, split looking at punctuation first, and so on.
"""
import os
import re
from typing import Callable, List, Tuple

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


def _token_counter(text: str) -> int:
    """
    Count the number of tokens in a string.

    TODO: chunking methods should be configurable to allow for different
          tokenization strategies depending on the model to be called.
          For now, we use an extremely rough estimate.
    """
    return len(text) // 4


def split_plaintext_lines(
    text: str, max_token_per_line: int, token_counter: Callable = _token_counter
) -> List[str]:
    """
    Split plain text into lines.
    it will split on new lines first, and then on punctuation.
    """
    return _split_text_lines(
        text=text,
        max_token_per_line=max_token_per_line,
        trim=True,
        token_counter=token_counter,
    )


def split_markdown_lines(
    text: str, max_token_per_line: int, token_counter: Callable = _token_counter
) -> List[str]:
    """
    Split markdown into lines.
    It will split on punctuation first, and then on space and new lines.
    """
    return _split_markdown_lines(
        text=text,
        max_token_per_line=max_token_per_line,
        trim=True,
        token_counter=token_counter,
    )


def split_plaintext_paragraph(
    text: List[str], max_tokens: int, token_counter: Callable = _token_counter
) -> List[str]:
    """
    Split plain text into paragraphs.
    """

    split_lines = []
    for line in text:
        split_lines.extend(
            _split_text_lines(
                text=line,
                max_token_per_line=max_tokens,
                trim=True,
                token_counter=token_counter,
            )
        )

    return _split_text_paragraph(
        text=split_lines, max_tokens=max_tokens, token_counter=token_counter
    )


def split_markdown_paragraph(
    text: List[str], max_tokens: int, token_counter: Callable = _token_counter
) -> List[str]:
    """
    Split markdown into paragraphs.
    """
    split_lines = []
    for line in text:
        split_lines.extend(
            _split_markdown_lines(
                text=line,
                max_token_per_line=max_tokens,
                trim=False,
                token_counter=token_counter,
            )
        )

    return _split_text_paragraph(
        text=split_lines, max_tokens=max_tokens, token_counter=token_counter
    )


def _split_text_paragraph(
    text: List[str], max_tokens: int, token_counter: Callable = _token_counter
) -> List[str]:
    """
    Split text into paragraphs.
    """
    if not text:
        return []

    paragraphs = []
    current_paragraph = []

    for line in text:
        num_tokens_line = token_counter(line)
        num_tokens_paragraph = token_counter("".join(current_paragraph))

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

        if token_counter(last_para) < max_tokens / 4:
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


def _split_markdown_lines(
    text: str,
    max_token_per_line: int,
    trim: bool,
    token_counter: Callable = _token_counter,
) -> List[str]:
    """
    Split markdown into lines.
    """

    return _split_str_lines(
        text=text,
        max_tokens=max_token_per_line,
        separators=MD_SPLIT_OPTIONS,
        trim=trim,
        token_counter=token_counter,
    )


def _split_text_lines(
    text: str,
    max_token_per_line: int,
    trim: bool,
    token_counter: Callable = _token_counter,
) -> List[str]:
    """
    Split text into lines.
    """

    return _split_str_lines(
        text=text,
        max_tokens=max_token_per_line,
        separators=TEXT_SPLIT_OPTIONS,
        trim=trim,
        token_counter=token_counter,
    )


def _split_str_lines(
    text: str,
    max_tokens: int,
    separators: List[List[str]],
    trim: bool,
    token_counter: Callable = _token_counter,
) -> List[str]:
    if not text:
        return []

    text = text.replace("\r\n", "\n")
    lines = []
    was_split = False
    for split_option in separators:
        if not lines:
            lines, was_split = _split_str(
                text=text,
                max_tokens=max_tokens,
                separators=split_option,
                trim=trim,
                token_counter=token_counter,
            )
        else:
            lines, was_split = _split_list(
                text=lines,
                max_tokens=max_tokens,
                separators=split_option,
                trim=trim,
                token_counter=token_counter,
            )
        if was_split:
            break

    return lines


def _split_str(
    text: str,
    max_tokens: int,
    separators: List[str],
    trim: bool,
    token_counter: Callable = _token_counter,
) -> Tuple[List[str], bool]:
    """
    Split text into lines.
    """
    input_was_split = False
    if not text:
        return [], input_was_split

    if trim:
        text = text.strip()

    text_as_is = [text]

    if token_counter(text) <= max_tokens:
        return text_as_is, input_was_split

    half = len(text) // 2

    cutpoint = -1

    if not separators:
        cutpoint = half
    elif set(separators) & set(text) and len(text) > 2:
        regex_separators = re.compile("|".join(re.escape(s) for s in separators))
        min_dist = half
        for match in re.finditer(regex_separators, text):
            end = match.end()
            dist = abs(half - end)
            if dist < min_dist:
                min_dist = dist
                cutpoint = end
            elif end > half:
                # distance is increasing, so we can stop searching
                break
    else:
        return text_as_is, input_was_split

    if 0 < cutpoint < len(text):
        lines = []
        for text_part in [text[:cutpoint], text[cutpoint:]]:
            split, has_split = _split_str(
                text=text_part,
                max_tokens=max_tokens,
                separators=separators,
                trim=trim,
                token_counter=token_counter,
            )
            lines.extend(split)
            input_was_split = input_was_split or has_split
    else:
        return text_as_is, input_was_split

    return lines, input_was_split


def _split_list(
    text: List[str],
    max_tokens: int,
    separators: List[str],
    trim: bool,
    token_counter: Callable = _token_counter,
) -> Tuple[List[str], bool]:
    """
    Split list of string into lines.
    """
    if not text:
        return [], False

    lines = []
    input_was_split = False
    for line in text:
        split_str, was_split = _split_str(
            text=line,
            max_tokens=max_tokens,
            separators=separators,
            trim=trim,
            token_counter=token_counter,
        )
        lines.extend(split_str)
        input_was_split = input_was_split or was_split

    return lines, input_was_split
