import pytest

from urllib3.fields import RequestField, format_header_param_rfc2231, guess_content_type
from urllib3.packages.six import u


class TestRequestField(object):
    @pytest.mark.parametrize(
        "filename, content_types",
        [
            ("image.jpg", ["image/jpeg", "image/pjpeg"]),
            ("notsure", ["application/octet-stream"]),
            (None, ["application/octet-stream"]),
        ],
    )
    def test_guess_content_type(self, filename, content_types):
        assert guess_content_type(filename) in content_types

    def test_create(self):
        simple_field = RequestField("somename", "data")
        assert simple_field.render_headers() == "\r\n"
        filename_field = RequestField("somename", "data", filename="somefile.txt")
        assert filename_field.render_headers() == "\r\n"
        headers_field = RequestField("somename", "data", headers={"Content-Length": 4})
        assert headers_field.render_headers() == "Content-Length: 4\r\n\r\n"

    def test_make_multipart(self):
        field = RequestField("somename", "data")
        field.make_multipart(content_type="image/jpg", content_location="/test")
        assert (
            field.render_headers()
            == 'Content-Disposition: form-data; name="somename"\r\n'
            "Content-Type: image/jpg\r\n"
            "Content-Location: /test\r\n"
            "\r\n"
        )

    def test_make_multipart_empty_filename(self):
        field = RequestField("somename", "data", "")
        field.make_multipart(content_type="application/octet-stream")
        assert (
            field.render_headers()
            == 'Content-Disposition: form-data; name="somename"; filename=""\r\n'
            "Content-Type: application/octet-stream\r\n"
            "\r\n"
        )

    def test_render_parts(self):
        field = RequestField("somename", "data")
        parts = field._render_parts({"name": "value", "filename": "value"})
        assert 'name="value"' in parts
        assert 'filename="value"' in parts
        parts = field._render_parts([("name", "value"), ("filename", "value")])
        assert parts == 'name="value"; filename="value"'

    def test_render_part_rfc2231_unicode(self):
        field = RequestField(
            "somename", "data", header_formatter=format_header_param_rfc2231
        )
        param = field._render_part("filename", u("n\u00e4me"))
        assert param == "filename*=utf-8''n%C3%A4me"

    def test_render_part_rfc2231_ascii(self):
        field = RequestField(
            "somename", "data", header_formatter=format_header_param_rfc2231
        )
        param = field._render_part("filename", b"name")
        assert param == 'filename="name"'

    def test_render_part_html5_unicode(self):
        field = RequestField("somename", "data")
        param = field._render_part("filename", u("n\u00e4me"))
        assert param == u('filename="n\u00e4me"')

    def test_render_part_html5_ascii(self):
        field = RequestField("somename", "data")
        param = field._render_part("filename", b"name")
        assert param == 'filename="name"'

    def test_render_part_html5_unicode_escape(self):
        field = RequestField("somename", "data")
        param = field._render_part("filename", u("hello\\world\u0022"))
        assert param == u('filename="hello\\\\world%22"')

    def test_render_part_html5_unicode_with_control_character(self):
        field = RequestField("somename", "data")
        param = field._render_part("filename", u("hello\x1A\x1B\x1C"))
        assert param == u('filename="hello%1A\x1B%1C"')

    def test_from_tuples_rfc2231(self):
        field = RequestField.from_tuples(
            u("fieldname"),
            (u("filen\u00e4me"), "data"),
            header_formatter=format_header_param_rfc2231,
        )
        cd = field.headers["Content-Disposition"]
        assert cd == u("form-data; name=\"fieldname\"; filename*=utf-8''filen%C3%A4me")

    def test_from_tuples_html5(self):
        field = RequestField.from_tuples(u("fieldname"), (u("filen\u00e4me"), "data"))
        cd = field.headers["Content-Disposition"]
        assert cd == u('form-data; name="fieldname"; filename="filen\u00e4me"')
