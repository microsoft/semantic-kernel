import pytest

from charset_normalizer import from_bytes
from charset_normalizer.constant import TOO_BIG_SEQUENCE


def test_large_payload_u8_sig_basic_entry():
    payload = ('0' * TOO_BIG_SEQUENCE).encode("utf_8_sig")
    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Large U8 payload case detection completely failed"
    assert best_guess.encoding == "utf_8", "Large U8 payload case detection wrongly detected!"
    assert best_guess.bom is True, "SIG/BOM property should be True"
    assert len(best_guess.raw) == len(payload), "Large payload should remain untouched when accessed through .raw"


def test_large_payload_ascii_basic_entry():
    payload = ('0' * TOO_BIG_SEQUENCE).encode("utf_8")
    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Large ASCII payload case detection completely failed"
    assert best_guess.encoding == "ascii", "Large ASCII payload case detection wrongly detected!"
    assert best_guess.bom is False, "SIG/BOM property should be False"
    assert len(best_guess.raw) == len(payload), "Large payload should remain untouched when accessed through .raw"


def test_misleading_large_sequence():
    content = (("hello simple ascii " * TOO_BIG_SEQUENCE) + ('我没有埋怨，磋砣的只是一些时间。 磋砣的只是一些时间。')) .encode('utf_8')

    guesses = from_bytes(content)

    assert len(guesses) > 0
    match = guesses.best()
    assert match is not None
    assert match.encoding == 'utf_8'
    assert str(match) is not None
