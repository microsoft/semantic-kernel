// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors;

import reactor.core.publisher.Mono;

import java.util.List;

public interface WebSearchEngineConnector {

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
