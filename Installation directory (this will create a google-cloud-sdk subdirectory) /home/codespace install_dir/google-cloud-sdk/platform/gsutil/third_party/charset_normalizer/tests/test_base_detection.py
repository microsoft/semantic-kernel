from charset_normalizer.api import from_bytes
from charset_normalizer.models import CharsetMatches

import pytest


def test_empty():
    best_guess = from_bytes(b'').best()

    assert best_guess is not None, "Empty bytes payload SHOULD NOT return None"
    assert best_guess.encoding == "utf_8", "Empty bytes payload SHOULD be guessed as UTF-8 (arbitrary)"
    assert len(best_guess.alphabets) == 0, ""


def test_bool_matches():
    guesses_not_empty = from_bytes(b'')
    guesses_empty = CharsetMatches([])

    assert bool(guesses_not_empty) is True, "Bool behaviour of CharsetMatches altered, should be True"
    assert bool(guesses_empty) is False, "Bool behaviour of CharsetMatches altered, should be False"


@pytest.mark.parametrize(
    "payload, expected_encoding",
    [
        (b'\xfe\xff', 'utf_16'),
        ('\uFEFF'.encode('gb18030'), 'gb18030'),
        (b'\xef\xbb\xbf', 'utf_8'),
        ("".encode('utf_32'), "utf_32")
    ]
)
def test_empty_but_with_bom_or_sig(payload, expected_encoding):
    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Empty detection but with SIG/BOM has failed!"
    assert best_guess.encoding == expected_encoding, "Empty detection but with SIG/BOM is wrongly detected!"
    assert best_guess.raw == payload, "The RAW property should contain the original payload given for detection."
    assert best_guess.byte_order_mark is True, "The BOM/SIG property should return True"
    assert str(best_guess) == "", "The cast to str SHOULD be empty"


@pytest.mark.parametrize(
    "payload, expected_encoding",
    [
        ((u'\uFEFF' + '我没有埋怨，磋砣的只是一些时间。').encode('gb18030'), "gb18030",),
        ('我没有埋怨，磋砣的只是一些时间。'.encode('utf_32'), "utf_32",),
        ('我没有埋怨，磋砣的只是一些时间。'.encode('utf_8_sig'), "utf_8",),
    ]
)
def test_content_with_bom_or_sig(payload, expected_encoding):
    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Detection but with SIG/BOM has failed!"
    assert best_guess.encoding == expected_encoding, "Detection but with SIG/BOM is wrongly detected!"
    assert best_guess.byte_order_mark is True, "The BOM/SIG property should return True"


@pytest.mark.parametrize(
    "payload",
    [
        b"AbAdZ pOoooOlDl mmlDoDkA lldDkeEkddA mpAlkDF",
        b"g4UsPJdfzNkGW2jwmKDGDilKGKYtpF2X.mx3MaTWL1tL7CNn5U7DeCcodKX7S3lwwJPKNjBT8etY",
        b'{"token": "g4UsPJdfzNkGW2jwmKDGDilKGKYtpF2X.mx3MaTWL1tL7CNn5U7DeCcodKX7S3lwwJPKNjBT8etY"}',
        b"81f4ab054b39cb0e12701e734077d84264308f5fc79494fc5f159fa2ebc07b73c8cc0e98e009664a20986706f90146e8eefcb929ce1f74a8eab21369fdc70198",
        b"{}",
    ]
)
def test_obviously_ascii_content(payload):
    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Dead-simple ASCII detection has failed!"
    assert best_guess.encoding == "ascii", "Dead-simple ASCII detection is wrongly detected!"


@pytest.mark.parametrize(
    "payload",
    [
        '\u020d\x1b'.encode('utf-8'),
        'h\xe9llo world!\n'.encode('utf_8'),
        '我没有埋怨，磋砣的只是一些时间。'.encode('utf_8'),
        'Bсеки човек има право на образование. Oбразованието трябва да бъде безплатно, поне що се отнася до началното и основното образование.'.encode('utf_8'),
        'Bсеки човек има право на образование.'.encode('utf_8'),
        "(° ͜ʖ °), creepy face, smiley 😀".encode("utf_8"),
        """["Financiën", "La France"]""".encode("utf_8"),
        "Qu'est ce que une étoile?".encode("utf_8"),
        """<?xml ?><c>Financiën</c>""".encode("utf_8"),
        "😀".encode("utf_8")
    ]
)
def test_obviously_utf8_content(payload):
    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Dead-simple UTF-8 detection has failed!"
    assert best_guess.encoding == "utf_8", "Dead-simple UTF-8 detection is wrongly detected!"


def test_mb_cutting_chk():
    # This payload should be wrongfully split and the autofix should ran automatically
    # on chunks extraction.
    payload = b"\xbf\xaa\xbb\xe7\xc0\xfb    \xbf\xb9\xbc\xf6 " \
              b"   \xbf\xac\xb1\xb8\xc0\xda\xb5\xe9\xc0\xba  \xba\xb9\xc0\xbd\xbc\xad\xb3\xaa " * 128

    guesses = from_bytes(payload, cp_isolation=["cp949"])
    best_guess = guesses.best()

    assert len(guesses) == 1, "cp isolation is set and given seq should be clear CP949!"
    assert best_guess.encoding == "cp949"


def test_alphabets_property():
    best_guess = from_bytes(
        "😀 Hello World! How affairs are going? 😀".encode("utf_8")
    ).best()

    assert "Basic Latin" in best_guess.alphabets
    assert "Emoticons range(Emoji)" in best_guess.alphabets
    assert best_guess.alphabets.count("Basic Latin") == 1
