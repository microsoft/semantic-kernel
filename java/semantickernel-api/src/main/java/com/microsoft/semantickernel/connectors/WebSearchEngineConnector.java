// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors;

import java.util.List;
import reactor.core.publisher.Mono;

/**
 * Web search engine connector interface.
 */
public interface WebSearchEngineConnector {

    /**
     * Execute a web search engine search.
     *
     * @param query  Query to search.
     * @param count  Number of results. Defaults to 1. Must be between 1 and 50.
     * @param offset Number of results to skip. Defaults to 0.
     * @return First snippet returned from search.
     */
    Mono<List<WebPage>> searchAsync(String query, int count, int offset);

    /**
     * Represents a web page.
     */
    interface WebPage {

        /**
         * Gets the name of the web page.
         *
         * @return The name of the web page.
         */
        String getName();

        /**
         * Gets the URL of the web page.
         *
         * @return The URL of the web page.
         */
        String getUrl();

        /**
         * Gets the snippet of the web page.
         *
         * @return The snippet of the web page.
         */
        String getSnippet();
    }

}
