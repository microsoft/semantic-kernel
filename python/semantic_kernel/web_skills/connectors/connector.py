class Connector:
    """
    Base class for search engine connectors
    """

    def search_async(self, query: str, count: int, offset: int) -> str:
        pass
