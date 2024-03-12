from charset_normalizer.api import from_path
import pytest


@pytest.mark.parametrize(
    "input_data_file, expected_charset, expected_language",
    [
        ('sample-arabic-1.txt', 'cp1256', 'Arabic'),
        ('sample-french-1.txt', 'cp1252', 'French'),
        ('sample-arabic.txt', 'utf_8', 'Arabic'),
        ('sample-russian-3.txt', 'utf_8', 'Russian'),
        ('sample-french.txt', 'utf_8', 'French'),
        ('sample-chinese.txt', 'big5', 'Classical Chinese'),
        ('sample-greek.txt', 'cp1253', 'Greek'),
        ('sample-greek-2.txt', 'cp1253', 'Greek'),
        ('sample-hebrew-2.txt', 'cp1255', 'Hebrew'),
        ('sample-hebrew-3.txt', 'cp1255', 'Hebrew'),
        ('sample-bulgarian.txt', 'utf_8', 'Bulgarian'),
        ('sample-english.bom.txt', 'utf_8', 'English'),
        ('sample-spanish.txt', 'utf_8', 'Spanish'),
        ('sample-korean.txt', 'cp949', 'Korean'),
        ('sample-turkish.txt', 'cp1254', 'Turkish'),
        ('sample-russian-2.txt', 'utf_8', 'Russian'),
        ('sample-russian.txt', 'mac_cyrillic', 'Russian'),
    ]
)
def test_elementary_detection(
    input_data_file: str,
    expected_charset: str,
    expected_language: str,
):
    best_guess = from_path("./data/{}".format(input_data_file)).best()

    assert best_guess is not None, "Elementary detection has failed upon '{}'".format(input_data_file)
    assert best_guess.encoding == expected_charset, "Elementary charset detection has failed upon '{}'".format(input_data_file)
    assert best_guess.language == expected_language, "Elementary language detection has failed upon '{}'".format(input_data_file)
