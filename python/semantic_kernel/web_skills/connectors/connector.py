class ConnectorBase:
    """
    Base class for search engine connectors
    """

    def search_async(self, query: str, num_results: int, offset: int) -> str:
        pass
