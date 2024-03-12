from charset_normalizer import from_bytes


def test_alphabet_property_undefined_range():
    payload = b'\xef\xbb\xbf\xf0\x9f\xa9\xb3'

    best_guess = from_bytes(payload).best()

    assert best_guess is not None, "Payload should have given something, detection failure"
    assert best_guess.encoding == "utf_8", "UTF-8 payload wrongly detected"
    assert best_guess.alphabets == [], "This property in that edge case, should return a empty list"
