// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors;

import java.util.List;

import reactor.core.publisher.Mono;

/**
 * Web search engine connector interface.
 */
public interface WebSearchEngineConnector {
    /**
     * Represents a web page.
     */
    interface WebPage {
        String getName();
        String getUrl();
        String getSnippet();
    }

    /**
     * Execute a web search engine search.
     * @param query Query to search.
     * @param count Number of results. Defaults to 1. Must be between 1 and 50.
     * @param offset Number of results to skip. Defaults to 0.
     * @return First snippet returned from search.
     */
    Mono<List<WebPage>> searchAsync(String query, int count, int offset);

}
