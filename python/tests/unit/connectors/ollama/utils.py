import json


class MockResponse:
    def __init__(self, response, status=200):
        self._response = response
        self.status = status

    async def text(self):
        return self._response

    async def json(self):
        return self._response

    def raise_for_status(self):
        pass

    @property
    async def content(self):
        yield json.dumps(self._response).encode("utf-8")
        yield json.dumps({"done": True}).encode("utf-8")

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self
