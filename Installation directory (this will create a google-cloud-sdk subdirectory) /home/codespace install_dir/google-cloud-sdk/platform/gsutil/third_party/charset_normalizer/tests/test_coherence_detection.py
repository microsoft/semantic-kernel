import pytest
from charset_normalizer.cd import encoding_languages, mb_encoding_languages, is_multi_byte_encoding, get_target_features


@pytest.mark.parametrize(
    "iana_encoding, expected_languages",
    [
        ("cp864", ["Arabic", "Farsi"]),
        ("cp862", ["Hebrew"]),
        ("cp737", ["Greek"]),
        ("cp424", ["Hebrew"]),
        ("cp273", ["Latin Based"]),
        ("johab", ["Korean"]),
        ("shift_jis", ["Japanese"]),
        ("mac_greek", ["Greek"]),
        ("iso2022_jp", ["Japanese"])
    ]
)
def test_infer_language_from_cp(iana_encoding, expected_languages):
    languages = mb_encoding_languages(iana_encoding) if is_multi_byte_encoding(iana_encoding) else encoding_languages(iana_encoding)

    for expected_language in expected_languages:
        assert expected_language in languages, "Wrongly detected language for given code page"


@pytest.mark.parametrize(
    "language, expected_have_accents, expected_pure_latin",
    [
        ("English", False, True),
        ("French", True, True),
        ("Hebrew", False, False),
        ("Arabic", False, False),
        ("Vietnamese", True, True),
        ("Turkish", True, True)
    ]
)
def test_target_features(language, expected_have_accents, expected_pure_latin):
    target_have_accents, target_pure_latin = get_target_features(language)

    assert target_have_accents is expected_have_accents
    assert target_pure_latin is expected_pure_latin
