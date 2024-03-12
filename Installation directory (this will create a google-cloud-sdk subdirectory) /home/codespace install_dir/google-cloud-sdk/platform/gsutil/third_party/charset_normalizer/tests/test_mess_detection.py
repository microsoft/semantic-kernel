import pytest
from charset_normalizer.md import mess_ratio


@pytest.mark.parametrize(
    "content, min_expected_ratio, max_expected_ratio",
    [
        ('典肇乎庚辰年十二月廿一，及己丑年二月十九，收各方語言二百五十，合逾七百萬目；二十大卷佔八成，單英文卷亦過二百萬。悉文乃天下有志共筆而成；有意助之，幾網路、隨纂作，大典茁焉。', 0., 0.),
        ('العقلية , التنويم المغناطيسي و / أو الاقتراح', 0., 0.),
        ("RadoZ تـــعــــديــل الـــتــــوقــيــــت مـــن قــبــل", 0., 0.),
        ("Cehennemin Sava■þ²s²'da kim?", 0.1, 0.5),
        ("´Á¥½³ø§i --  ±i®Ìºû, ³¯·Ø©v", 0.5, 1.),
        ("ïstanbul, T■rkiye'nin en kalabal»k, iktisadi ve k■lt■rel aÓ»dan en —nemli", 0.1, 0.5),
        ("<i>Parce que Óa, c'est la vÕritable histoire de la rencontre avec votre Tante Robin.</i>", 0.01, 0.5),
        ("""ØĢØŠØģØ§ØĶŲ ŲŲ ØĢŲ Ø§ŲŲØ§Øģ ŲŲŲ ŲØ§ ØģŲŲŲØŠØģØ§ØĶŲŲŲØ ØŊØđŲØ§ ŲØģŲØđ ØđŲ (ŲØąŲØŊŲ) ŲØ§ŲØŪØ§ØŠŲ""", 0.8, 2.0),
        ("""ÇáÚŞáíÉ , ÇáÊäæíã ÇáãÛäÇØíÓí æ / Ãæ ÇáÇŞÊÑÇÍ""", 0.8, 2.5),
        ("""hishamkoc@yahoo.com ุชุฑุฌูููุฉ ููุดูููุงู ุงููููููููุงูRadoZ ุชูููุนููููุฏูููู ุงููููุชูููููููููููููุช ููููู ูููุจููู""", 0.5, 2.0)

    ]
)
def test_mess_detection(content, min_expected_ratio, max_expected_ratio):
    calculated_mess_ratio = mess_ratio(
        content,
        maximum_threshold=1.
    )

    assert min_expected_ratio <= calculated_mess_ratio <= max_expected_ratio, "The mess detection ratio calculated for given content is not well adjusted!"
